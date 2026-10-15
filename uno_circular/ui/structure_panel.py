"""'Estructura de datos' panel: live pointer log, traversals and invariant check."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Iterator

import customtkinter as ctk

from models.player import Player
from models.uno_table import UnoTable
from ui.table_view import MUTED, NEXT_COLOR, PREV_COLOR, RingCanvas

TRAVERSAL_STEP_MS = 480

# Log line color by keyword (first match wins).
LOG_TAGS: tuple[tuple[str, str, str], ...] = (
    ("Insertar", "insert", "#4ade80"),
    ("Eliminado", "remove", "#f87171"),
    ("Eliminar", "remove", "#f87171"),
    ("Reversa", "reverse", "#c084fc"),
    ("El turno pasa", "turn", "#facc15"),
    ("Turno", "turn", "#93c5fd"),
    ("current_turn", "turn", "#93c5fd"),
    ("Recorrido", "walk", "#38bdf8"),
    ("validate_links", "check", "#fde68a"),
)


class StructurePanel(ctk.CTkFrame):
    """Shows the circular doubly linked list working, for the teacher.

    * state of ``head``, ``head.prev``, ``current_turn``, ``direction`` and ``size``;
    * ``display_table()`` output;
    * a live log of every pointer operation (fed by ``UnoTable.logger``);
    * buttons that walk the ring with the traversal generators.
    """

    def __init__(self, master: tk.Misc, get_ring: Callable[[], RingCanvas | None]) -> None:
        super().__init__(master, corner_radius=14, width=440)
        self.grid_propagate(False)  # keep a fixed width while texts change
        self.table: UnoTable | None = None
        self.get_ring = get_ring
        self._counter = 0
        self._walk_job: str | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self, text="Estructura de datos", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(self, text="Lista circular doble: UnoTable  ·  nodo: Player",
                     text_color=MUTED).grid(row=1, column=0, sticky="w", padx=14)

        self.state_box = ctk.CTkFrame(self, fg_color="#1f232c", corner_radius=10)
        self.state_box.grid(row=2, column=0, sticky="ew", padx=12, pady=8)
        self.state_box.grid_columnconfigure(1, weight=1)
        self._state_labels: dict[str, ctk.CTkLabel] = {}
        for row, key in enumerate(("head", "head.prev (último)", "current_turn", "direction",
                                   "size", "validate_links()")):
            ctk.CTkLabel(self.state_box, text=key, font=ctk.CTkFont(family="Consolas", size=13),
                         text_color=MUTED).grid(row=row, column=0, sticky="w", padx=(12, 8), pady=1)
            value = ctk.CTkLabel(self.state_box, text="—", anchor="w",
                                 font=ctk.CTkFont(family="Consolas", size=13, weight="bold"))
            value.grid(row=row, column=1, sticky="w", pady=1)
            self._state_labels[key] = value

        self.display_label = ctk.CTkLabel(self, text="", wraplength=380, justify="left", anchor="w",
                                          font=ctk.CTkFont(family="Consolas", size=12))
        self.display_label.grid(row=3, column=0, sticky="ew", padx=14)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=4, column=0, sticky="ew", padx=10, pady=8)
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(buttons, text="Recorrer ↻ (next)", fg_color="#166534", hover_color="#15803d",
                      command=lambda: self.walk(clockwise=True)).grid(row=0, column=0, sticky="ew", padx=3)
        ctk.CTkButton(buttons, text="Recorrer ↺ (prev)", fg_color="#9a3412", hover_color="#c2410c",
                      command=lambda: self.walk(clockwise=False)).grid(row=0, column=1, sticky="ew", padx=3)
        ctk.CTkButton(buttons, text="Validar enlaces", fg_color="#3a3f4b",
                      command=self.check_links).grid(row=1, column=0, sticky="ew", padx=3, pady=(6, 0))
        ctk.CTkButton(buttons, text="Limpiar bitácora", fg_color="#3a3f4b",
                      command=self.clear_log).grid(row=1, column=1, sticky="ew", padx=3, pady=(6, 0))

        self.log_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12), wrap="word")
        self.log_box.grid(row=5, column=0, sticky="nsew", padx=12, pady=(0, 12))
        for _keyword, tag, color in LOG_TAGS:
            self.log_box.tag_config(tag, foreground=color)
        self.log_box.tag_config("num", foreground="#6b7280")
        self.log_box.configure(state="disabled")

    # ---------------------------------------------------------------- public
    def set_table(self, table: UnoTable) -> None:
        """Attach a table and start receiving its pointer-operation log."""
        self.stop_walk()
        self.table = table
        table.logger = self.log
        self.refresh()

    def log(self, message: str) -> None:
        """Append one line to the bitácora (used as ``UnoTable.logger``)."""
        self._counter += 1
        tag = next((t for keyword, t, _c in LOG_TAGS if keyword in message), None)
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{self._counter:03d} ", "num")
        self.log_box.insert("end", message + "\n", tag or ())
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def refresh(self) -> None:
        """Update the pointer summary from the table."""
        table = self.table
        if table is None:
            return
        labels = self._state_labels
        labels["head"].configure(text=table.head.name if table.head else "None")
        labels["head.prev (último)"].configure(text=table.last.name if table.last else "None")
        labels["current_turn"].configure(text=table.current_turn.name if table.current_turn else "None")
        if table.direction == 1:
            labels["direction"].configure(text="1  ↻ horario (usa next)", text_color=NEXT_COLOR)
        else:
            labels["direction"].configure(text="-1 ↺ antihorario (usa prev)", text_color=PREV_COLOR)
        labels["size"].configure(text=str(len(table)))
        valid = table.validate_links()
        labels["validate_links()"].configure(text="True ✓" if valid else "False ✗",
                                             text_color="#4ade80" if valid else "#f87171")
        self.display_label.configure(text="display_table(): " + table.display_table(to_console=False))

    def check_links(self) -> None:
        if self.table is None:
            return
        valid = self.table.validate_links()
        self.log(f"validate_links() = {valid}: head.prev.next is head, "
                 f"node.next.prev is node en {len(self.table)} nodos")
        self.refresh()

    # ------------------------------------------------------------- traversal
    def walk(self, clockwise: bool) -> None:
        """Animate a full lap using ``traverse_clockwise`` / ``traverse_counterclockwise``."""
        if self.table is None:
            return
        self.stop_walk()
        if self.table.is_empty():
            self.log("Recorrido: la lista está vacía (head = None)")
            return
        if clockwise:
            traverse = self.table.traverse_clockwise
            title = "Recorrido ↻ con next desde head"
        else:
            traverse = self.table.traverse_counterclockwise
            title = "Recorrido ↺ con prev desde head.prev"
        order = " → ".join(p.name for p in traverse())
        self.log(f"{title}: {order} → (vuelta completa, se detiene al volver al inicio)")
        # A second, lazy generator drives the highlight one node at a time.
        self._step(traverse())

    def _step(self, generator: Iterator[Player]) -> None:
        ring = self.get_ring()
        try:
            player = next(generator)
        except StopIteration:
            self._walk_job = None
            if ring is not None:
                ring.flash_name = None
                ring.redraw()
            return
        if ring is not None:
            ring.flash_name = player.name
            ring.redraw()
        self._walk_job = self.after(TRAVERSAL_STEP_MS, self._step, generator)

    def stop_walk(self) -> None:
        if self._walk_job is not None:
            self.after_cancel(self._walk_job)
            self._walk_job = None
        ring = self.get_ring()
        if ring is not None:
            ring.flash_name = None

