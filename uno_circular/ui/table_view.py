"""Game screen: ring canvas with next/prev arrows, status bar and player hand."""

from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from game.uno_game import GameError, UnoGame
from models.card import BLUE, COLOR_NAMES_ES, COLORS, GREEN, RED, YELLOW, Card
from models.player import Player
from models.uno_table import CLOCKWISE, UnoTable

# ----------------------------------------------------------------- palette
CANVAS_BG = "#171a21"
NODE_FILL = "#2a2f3b"
NODE_HUMAN_FILL = "#33415c"
NODE_OUTLINE = "#4b5263"
TEXT = "#e6e8ee"
MUTED = "#8b93a7"
NEXT_COLOR = "#4ade80"
PREV_COLOR = "#fb923c"
TURN_COLOR = "#facc15"
FLASH_COLOR = "#38bdf8"
CARD_COLORS: dict[str | None, str] = {
    RED: "#e5383b",
    YELLOW: "#f4c430",
    GREEN: "#2bb24c",
    BLUE: "#2f6fdf",
    None: "#26262b",
}
CARD_HOVER: dict[str | None, str] = {
    RED: "#ff5a5d",
    YELLOW: "#ffd84d",
    GREEN: "#3fd463",
    BLUE: "#4b8bff",
    None: "#3a3a42",
}
CARD_DIM: dict[str | None, str] = {
    RED: "#5b2a2d",
    YELLOW: "#5e5228",
    GREEN: "#24492e",
    BLUE: "#273d63",
    None: "#202024",
}
COLOR_BY_NAME_ES = {name: code for code, name in COLOR_NAMES_ES.items()}

CPU_DELAY_MS = 950
CPU_DELAY_FAST_MS = 550
ANIMATION_FRAMES = 12
ANIMATION_STEP_MS = 22


def text_color_for(color: str | None) -> str:
    """Dark text on yellow cards, white everywhere else."""
    return "#1b1b1b" if color == YELLOW else "#ffffff"


class RingCanvas(tk.Canvas):
    """Draws the circular doubly linked list as a round table.

    Every node is placed clockwise around a circle; green arrows show the
    ``next`` pointers (inside the ring) and orange arrows the ``prev`` pointers
    (outside). The current turn is shown with a yellow halo that slides along
    the ring when the turn changes.
    """

    def __init__(self, master: tk.Misc, table: UnoTable | None = None, **kwargs) -> None:
        super().__init__(master, bg=CANVAS_BG, highlightthickness=0, **kwargs)
        self.table = table
        self.top_card: Card | None = None
        self.active_color: str | None = None
        self.show_turn = True
        self.flash_name: str | None = None
        self._halo_angle: float | None = None
        self._anim_job: str | None = None
        self.bind("<Configure>", lambda _e: self.redraw())

    # -------------------------------------------------------------- geometry
    def _geometry(self) -> tuple[float, float, float]:
        width = max(self.winfo_width(), 240)
        height = max(self.winfo_height(), 240)
        radius = max(min(width, height) / 2 - 78, 70)
        return width / 2, height / 2, radius

    def _node_radius(self) -> float:
        size = len(self.table) if self.table else 0
        return 40 if size <= 4 else 34

    def _angle_of(self, index: int, size: int) -> float:
        # Screen y grows downwards, so increasing angles go clockwise.
        return -math.pi / 2 + 2 * math.pi * index / size

    def _layout(self) -> dict[str, tuple[float, float, float]]:
        """Map player name → (x, y, angle) by walking the ring once with ``next``."""
        layout: dict[str, tuple[float, float, float]] = {}
        if self.table is None or self.table.is_empty():
            return layout
        cx, cy, radius = self._geometry()
        size = len(self.table)
        for index, player in enumerate(self.table.traverse_clockwise()):
            angle = self._angle_of(index, size)
            layout[player.name] = (cx + radius * math.cos(angle),
                                   cy + radius * math.sin(angle), angle)
        return layout

    # --------------------------------------------------------------- drawing
    def redraw(self) -> None:
        """Repaint the whole table."""
        self.delete("all")
        cx, cy, radius = self._geometry()
        self._draw_legend()
        if self.table is None or self.table.is_empty():
            self.create_text(cx, cy, text="Mesa vacía\nhead = None", fill=MUTED,
                             font=("Segoe UI", 15), justify="center")
            return

        layout = self._layout()
        node_r = self._node_radius()
        self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                         outline="#232733", width=1, dash=(3, 5))

        if len(self.table) == 1:
            self._draw_self_loop(layout[self.table.head.name], node_r)
        else:
            prev_offset = 18 if len(self.table) == 2 else 8
            for player in self.table.traverse_clockwise():
                a = layout[player.name][:2]
                self._arrow(a, layout[player.next.name][:2], 8, NEXT_COLOR, node_r)
                self._arrow(a, layout[player.prev.name][:2], prev_offset, PREV_COLOR, node_r)

        if self.show_turn and self._halo_angle is not None:
            hx = cx + radius * math.cos(self._halo_angle)
            hy = cy + radius * math.sin(self._halo_angle)
            for width, pad in ((10, 12), (4, 8)):
                self.create_oval(hx - node_r - pad, hy - node_r - pad,
                                 hx + node_r + pad, hy + node_r + pad,
                                 outline=TURN_COLOR if width == 4 else "#5c4d12", width=width)

        for player in self.table.traverse_clockwise():
            self._draw_node(player, layout[player.name], node_r, cx, cy)

        self._draw_center(cx, cy)

    def _draw_legend(self) -> None:
        self.create_line(14, 18, 44, 18, fill=NEXT_COLOR, width=2, arrow=tk.LAST)
        self.create_text(50, 18, text="next", anchor="w", fill=NEXT_COLOR, font=("Consolas", 11))
        self.create_line(14, 38, 44, 38, fill=PREV_COLOR, width=2, arrow=tk.LAST)
        self.create_text(50, 38, text="prev", anchor="w", fill=PREV_COLOR, font=("Consolas", 11))

    def _arrow(self, a: tuple[float, float], b: tuple[float, float], offset: float,
               color: str, node_r: float) -> None:
        dx, dy = b[0] - a[0], b[1] - a[1]
        dist = math.hypot(dx, dy) or 1
        ux, uy = dx / dist, dy / dist
        nx, ny = -uy, ux  # perpendicular, so next/prev lines do not overlap
        sx, sy = a[0] + ux * node_r + nx * offset, a[1] + uy * node_r + ny * offset
        ex, ey = b[0] - ux * (node_r + 2) + nx * offset, b[1] - uy * (node_r + 2) + ny * offset
        self.create_line(sx, sy, ex, ey, fill=color, width=2, arrow=tk.LAST,
                         arrowshape=(11, 13, 5))

    def _draw_self_loop(self, pos: tuple[float, float, float], node_r: float) -> None:
        x, y, _ = pos
        # Loop on the right side of the node: next and prev point to itself.
        left = x + node_r - 14
        self.create_arc(left, y - 26, left + 62, y + 26, start=140, extent=-280,
                        style="arc", outline=NEXT_COLOR, width=2)
        self.create_line(left + 6, y + 15, left + 2, y + 12, fill=NEXT_COLOR, width=2,
                         arrow=tk.LAST, arrowshape=(9, 11, 4))
        self.create_text(left + 70, y, text="next = prev = sí mismo", anchor="w",
                         fill=MUTED, font=("Consolas", 10))

    def _draw_node(self, player: Player, pos: tuple[float, float, float], node_r: float,
                   cx: float, cy: float) -> None:
        x, y, angle = pos
        is_turn = self.show_turn and player is self.table.current_turn
        outline = FLASH_COLOR if player.name == self.flash_name else (
            TURN_COLOR if is_turn else NODE_OUTLINE)
        fill = NODE_HUMAN_FILL if player.is_human else NODE_FILL
        self.create_oval(x - node_r, y - node_r, x + node_r, y + node_r,
                         fill=fill, outline=outline, width=4 if outline != NODE_OUTLINE else 2)
        self.create_text(x, y - 9, text=player.name, fill=TEXT, font=("Segoe UI", 11, "bold"))
        detail = f"{player.card_count} cartas" if player.hand else ("Humano" if player.is_human else "CPU")
        self.create_text(x, y + 11, text=detail, fill=MUTED, font=("Segoe UI", 9))

        tags = []
        if player is self.table.head:
            tags.append("head")
        if player is self.table.last and len(self.table) > 1:
            tags.append("head.prev (último)")
        if tags:
            # Place the label outside the ring, anchored away from the node.
            cos, sin = math.cos(angle), math.sin(angle)
            tx = x + cos * (node_r + 14)
            ty = y + sin * (node_r + 14)
            if cos > 0.35:
                anchor = "w"
            elif cos < -0.35:
                anchor = "e"
            else:
                anchor = "s" if sin < 0 else "n"
            self.create_text(tx, ty, text="\n".join(tags), fill="#c4b5fd", anchor=anchor,
                             font=("Consolas", 10, "bold"), justify="center")

    def _draw_center(self, cx: float, cy: float) -> None:
        if self.table.direction == CLOCKWISE:
            symbol, label = "↻", "Horario · next"
        else:
            symbol, label = "↺", "Antihorario · prev"
        if self.top_card is None:
            self.create_text(cx, cy - 8, text=symbol, fill=TEXT, font=("Segoe UI Symbol", 40))
            self.create_text(cx, cy + 32, text=label, fill=MUTED, font=("Segoe UI", 11))
            return
        self.create_text(cx, cy - 92, text=symbol, fill=TEXT, font=("Segoe UI Symbol", 30))
        self.create_text(cx, cy - 64, text=label, fill=MUTED, font=("Segoe UI", 10))
        card = self.top_card
        w, h = 38, 54
        self.create_rectangle(cx - w, cy - h + 14, cx + w, cy + h + 14,
                              fill=CARD_COLORS[card.color],
                              outline=CARD_COLORS[self.active_color] if card.is_wild else "#ffffff",
                              width=5 if card.is_wild else 2)
        self.create_text(cx, cy + 14, text=card.symbol, fill=text_color_for(card.color),
                         font=("Segoe UI Symbol", 26, "bold"))
        if self.active_color:
            self.create_text(cx, cy + h + 32, text=f"Color: {COLOR_NAMES_ES[self.active_color]}",
                             fill=CARD_COLORS[self.active_color], font=("Segoe UI", 11, "bold"))

    # -------------------------------------------------------------- animation
    def update_turn(self, animate: bool = True) -> None:
        """Move the yellow halo to ``current_turn``, sliding along the ring."""
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        current = self.table.current_turn if self.table else None
        layout = self._layout()
        if current is None or current.name not in layout:
            self._halo_angle = None
            self.redraw()
            return
        target = layout[current.name][2]
        start = self._halo_angle
        if not animate or start is None:
            self._halo_angle = target
            self.redraw()
            return
        # Travel in the direction of play so the slide matches next/prev.
        delta = (target - start) % (2 * math.pi)
        if self.table.direction != CLOCKWISE:
            delta -= 2 * math.pi
        if abs(delta) < 1e-6:
            self._halo_angle = target
            self.redraw()
            return
        self._animate(start, delta, 1)

    def _animate(self, start: float, delta: float, frame: int) -> None:
        t = frame / ANIMATION_FRAMES
        eased = 1 - (1 - t) ** 3
        self._halo_angle = start + delta * eased
        self.redraw()
        if frame < ANIMATION_FRAMES:
            self._anim_job = self.after(ANIMATION_STEP_MS, self._animate, start, delta, frame + 1)
        else:
            self._anim_job = None


class TableView(ctk.CTkFrame):
    """Game screen: table ring, event log and the human player's hand."""

    def __init__(self, master: tk.Misc, game: UnoGame, on_change: Callable[[], None],
                 on_game_over: Callable[[UnoGame], None], on_quit: Callable[[], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self.game = game
        self.on_change = on_change
        self.on_game_over = on_game_over
        self.on_quit = on_quit
        self._job: str | None = None
        self._finished_reported = False
        self.human: Player | None = next(
            (p for p in game.table.traverse_clockwise() if p.is_human), None)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self.ring = RingCanvas(self, game.table)
        self.ring.grid(row=1, column=0, sticky="nsew", padx=4, pady=(4, 6))
        self._build_log()
        self._build_hand()

    # -------------------------------------------------------------- building
    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, corner_radius=12)
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 4))
        header.grid_columnconfigure(0, weight=1)
        self.turn_label = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=18, weight="bold"),
                                       anchor="w")
        self.turn_label.grid(row=0, column=0, sticky="w", padx=14, pady=10)
        self.direction_label = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=16))
        self.direction_label.grid(row=0, column=1, padx=10)
        self.deck_label = ctk.CTkLabel(header, text="", text_color=MUTED)
        self.deck_label.grid(row=0, column=2, padx=10)
        ctk.CTkButton(header, text="Abandonar partida", width=140, fg_color="#3a3f4b",
                      hover_color="#7f1d1d", command=self._quit).grid(row=0, column=3, padx=10)

    def _build_log(self) -> None:
        self.log_box = ctk.CTkTextbox(self, height=92, font=ctk.CTkFont(size=12), wrap="word")
        self.log_box.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 6))
        self.log_box.configure(state="disabled")

    def _build_hand(self) -> None:
        box = ctk.CTkFrame(self, corner_radius=12)
        box.grid(row=3, column=0, sticky="ew", padx=4)
        box.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(box, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        top.grid_columnconfigure(0, weight=1)
        self.hand_label = ctk.CTkLabel(top, text="Tu mano", font=ctk.CTkFont(size=14, weight="bold"),
                                       anchor="w")
        self.hand_label.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top, text="Color para comodín:").grid(row=0, column=1, padx=(10, 6))
        self.color_selector = ctk.CTkSegmentedButton(
            top, values=[COLOR_NAMES_ES[c] for c in COLORS],
            selected_color="#4b5563", selected_hover_color="#6b7280")
        self.color_selector.set(COLOR_NAMES_ES[RED])
        self.color_selector.grid(row=0, column=2, padx=4)
        self.draw_button = ctk.CTkButton(top, text="Robar carta", width=120, command=self._human_draw)
        self.draw_button.grid(row=0, column=3, padx=(12, 4))
        self.pass_button = ctk.CTkButton(top, text="Pasar", width=80, fg_color="#3a3f4b",
                                         command=self._human_pass)
        self.pass_button.grid(row=0, column=4, padx=4)

        self.cards_frame = ctk.CTkScrollableFrame(box, orientation="horizontal", height=104,
                                                  fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=(4, 8))

    # ------------------------------------------------------------- lifecycle
    def begin(self) -> None:
        """Draw the initial state and hand the turn to whoever starts."""
        self.refresh(animate=False)
        self._schedule()

    def stop(self) -> None:
        """Cancel pending CPU moves (called before the view is destroyed)."""
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    def add_event(self, message: str) -> None:
        """Append a game event (Spanish) to the log box."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # --------------------------------------------------------------- refresh
    def refresh(self, animate: bool = True) -> None:
        """Update every widget from the game state."""
        game, table = self.game, self.game.table
        self.ring.top_card = game.top_card
        self.ring.active_color = game.active_color
        self.ring.show_turn = not game.is_over
        self.ring.update_turn(animate=animate)

        current = game.current_player
        if game.is_over:
            self.turn_label.configure(text="Partida terminada", text_color=TEXT)
        elif current is not None:
            whose = "Tu turno" if current.is_human else f"Turno de {current.name}"
            self.turn_label.configure(text=f"{whose}", text_color=TURN_COLOR if current.is_human else TEXT)
        if table.direction == CLOCKWISE:
            self.direction_label.configure(text="↻ Horario (next)", text_color=NEXT_COLOR)
        else:
            self.direction_label.configure(text="↺ Antihorario (prev)", text_color=PREV_COLOR)
        self.deck_label.configure(text=f"Mazo: {len(game.deck)} cartas")
        self._render_hand()
        self.on_change()

    def _is_human_turn(self) -> bool:
        current = self.game.current_player
        return not self.game.is_over and current is not None and current.is_human

    def _render_hand(self) -> None:
        for child in self.cards_frame.winfo_children():
            child.destroy()
        human = self.human
        seated = human is not None and human.name in self.game.table
        if human is None or not seated:
            place = (self.game.rankings.index(human.name) + 1
                     if human is not None and human.name in self.game.rankings else None)
            text = (f"¡Terminaste en el puesto #{place}! Ya saliste de la mesa; los CPU siguen jugando."
                    if place else "No hay jugador humano en la mesa.")
            self.hand_label.configure(text="Tu mano")
            ctk.CTkLabel(self.cards_frame, text=text, text_color=MUTED).pack(padx=10, pady=30)
            self.draw_button.configure(state="disabled")
            self.pass_button.configure(state="disabled")
            return

        my_turn = self._is_human_turn()
        playable = set(self.game.playable_indices(human)) if my_turn else set()
        self.hand_label.configure(text=f"Tu mano ({len(human.hand)} cartas)"
                                  + (" — elige una carta resaltada" if playable else ""))
        for index, card in enumerate(human.hand):
            can_play = index in playable
            button = ctk.CTkButton(
                self.cards_frame, text=card.symbol, width=60, height=88, corner_radius=10,
                font=ctk.CTkFont(size=22, weight="bold"),
                fg_color=CARD_COLORS[card.color] if can_play or not my_turn else CARD_DIM[card.color],
                hover_color=CARD_HOVER[card.color],
                text_color=text_color_for(card.color),
                text_color_disabled=text_color_for(card.color) if not my_turn else "#6b7280",
                border_width=3 if can_play else 1,
                border_color="#ffffff" if can_play else "#3a3f4b",
                state="normal" if can_play else "disabled",
                command=lambda i=index: self._human_play(i))
            button.pack(side="left", padx=4, pady=(10 if can_play else 16, 4))

        self.draw_button.configure(state="normal" if my_turn and self.game.drawn_card is None
                                   else "disabled")
        self.pass_button.configure(state="normal" if my_turn and self.game.drawn_card is not None
                                   else "disabled")

    # --------------------------------------------------------- human actions
    def _human_play(self, index: int) -> None:
        if not self._is_human_turn():
            return
        color = COLOR_BY_NAME_ES.get(self.color_selector.get(), RED)
        try:
            self.game.play_card(index, chosen_color=color, player=self.human)
        except GameError as error:
            self.add_event(f"⚠ {error}")
            return
        self.refresh()
        self._schedule()

    def _human_draw(self) -> None:
        if not self._is_human_turn():
            return
        try:
            self.game.draw_card(player=self.human)
        except GameError as error:
            self.add_event(f"⚠ {error}")
            return
        self.refresh()
        self._schedule()

    def _human_pass(self) -> None:
        if not self._is_human_turn():
            return
        try:
            self.game.pass_turn(player=self.human)
        except GameError as error:
            self.add_event(f"⚠ {error}")
            return
        self.refresh()
        self._schedule()

    # ------------------------------------------------------------- CPU turns
    def _schedule(self) -> None:
        """Queue the next CPU move, or report the end of the game."""
        self.stop()
        if self.game.is_over:
            if not self._finished_reported:
                self._finished_reported = True
                self._job = self.after(700, lambda: self.on_game_over(self.game))
            return
        current = self.game.current_player
        if current is not None and not current.is_human:
            human_out = self.human is None or self.human.name not in self.game.table
            delay = CPU_DELAY_FAST_MS if human_out else CPU_DELAY_MS
            self._job = self.after(delay, self._cpu_step)

    def _cpu_step(self) -> None:
        self._job = None
        if self.game.is_over:
            return
        self.game.cpu_turn()
        self.refresh()
        self._schedule()

    def _quit(self) -> None:
        self.stop()
        self.on_quit()
