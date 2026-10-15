"""Setup screen: add players at the beginning/end, remove them and start."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from game.uno_game import MAX_PLAYERS
from models.player import Player
from models.uno_table import UnoTable
from ui.table_view import MUTED, RingCanvas

MAX_NAME_LENGTH = 12
MAX_CPUS = MAX_PLAYERS - 1
ERROR_COLOR = "#f87171"
OK_COLOR = "#4ade80"


class SetupView(ctk.CTkFrame):
    """Configure the table before the game using the linked list operations."""

    def __init__(self, master: tk.Misc, table: UnoTable, on_change: Callable[[], None],
                 on_start: Callable[[], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self.table = table
        self.on_change = on_change
        self.on_start = on_start

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Configuración de la mesa",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=(4, 0))
        ctk.CTkLabel(self, text="Cada jugador es un nodo de una lista circular doble. "
                                "Necesitas 1 jugador humano y de 1 a 5 jugadores CPU.",
                     text_color=MUTED).grid(row=1, column=0, sticky="nw", padx=8)

        self.ring = RingCanvas(self, table)
        self.ring.show_turn = False
        self.ring.grid(row=2, column=0, sticky="nsew", padx=4, pady=8)

        self._build_form()

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self, corner_radius=12)
        form.grid(row=3, column=0, sticky="ew", padx=4, pady=(0, 4))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Nombre:").grid(row=0, column=0, padx=(14, 6), pady=(12, 6), sticky="w")
        self.name_entry = ctk.CTkEntry(form, placeholder_text="Ej. Ana")
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=(12, 6))
        self.name_entry.bind("<Return>", lambda _e: self._add(last=True))
        self.kind_selector = ctk.CTkSegmentedButton(form, values=["CPU", "Humano"])
        self.kind_selector.set("CPU")
        self.kind_selector.grid(row=0, column=2, padx=8, pady=(12, 6))
        ctk.CTkButton(form, text="Agregar al inicio", width=140,
                      command=lambda: self._add(last=False)).grid(row=0, column=3, padx=4, pady=(12, 6))
        ctk.CTkButton(form, text="Agregar al final", width=140,
                      command=lambda: self._add(last=True)).grid(row=0, column=4, padx=(4, 14), pady=(12, 6))

        ctk.CTkLabel(form, text="Eliminar:").grid(row=1, column=0, padx=(14, 6), pady=6, sticky="w")
        self.remove_menu = ctk.CTkOptionMenu(form, values=["—"])
        self.remove_menu.grid(row=1, column=1, sticky="ew", pady=6)
        ctk.CTkButton(form, text="Eliminar jugador", width=140, fg_color="#7f1d1d",
                      hover_color="#991b1b", command=self._remove).grid(row=1, column=3, padx=4, pady=6)

        self.status_label = ctk.CTkLabel(form, text="", anchor="w")
        self.status_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=14, pady=(4, 12))
        self.start_button = ctk.CTkButton(form, text="▶  Empezar partida", height=40,
                                          font=ctk.CTkFont(size=15, weight="bold"),
                                          fg_color="#15803d", hover_color="#16a34a",
                                          command=self._start)
        self.start_button.grid(row=2, column=3, columnspan=2, sticky="ew", padx=(4, 14), pady=(4, 12))

    # --------------------------------------------------------------- actions
    def refresh(self) -> None:
        """Redraw the preview ring and update the remove menu."""
        names = [p.name for p in self.table.traverse_clockwise()]
        self.remove_menu.configure(values=names or ["—"])
        if self.remove_menu.get() not in names:
            self.remove_menu.set(names[0] if names else "—")
        self.ring.redraw()
        self.on_change()

    def _status(self, text: str, ok: bool = True) -> None:
        self.status_label.configure(text=text, text_color=OK_COLOR if ok else ERROR_COLOR)

    def _counts(self) -> tuple[int, int]:
        humans = sum(1 for p in self.table.traverse_clockwise() if p.is_human)
        return humans, len(self.table) - humans

    def _add(self, last: bool) -> None:
        name = self.name_entry.get().strip()
        is_human = self.kind_selector.get() == "Humano"
        humans, cpus = self._counts()
        if not name:
            self._status("Escribe un nombre.", ok=False)
            return
        if len(name) > MAX_NAME_LENGTH:
            self._status(f"Máximo {MAX_NAME_LENGTH} caracteres.", ok=False)
            return
        if is_human and humans >= 1:
            self._status("Solo puede haber 1 jugador humano.", ok=False)
            return
        if not is_human and cpus >= MAX_CPUS:
            self._status(f"Máximo {MAX_CPUS} jugadores CPU.", ok=False)
            return
        player = Player(name, is_human=is_human)
        try:
            if last:
                self.table.add_player_last(player)
            else:
                self.table.add_player_first(player)
        except ValueError as error:
            self._status(str(error), ok=False)
            return
        self.name_entry.delete(0, "end")
        where = "al final" if last else "al inicio"
        self._status(f"{name} agregado {where}.")
        self.refresh()

    def _remove(self) -> None:
        name = self.remove_menu.get()
        removed = self.table.remove_player(name)
        if removed is None:
            self._status("No hay jugador para eliminar.", ok=False)
            return
        self._status(f"{name} eliminado de la mesa.")
        self.refresh()

    def _start(self) -> None:
        humans, cpus = self._counts()
        if humans != 1:
            self._status("Agrega exactamente 1 jugador humano.", ok=False)
            return
        if not 1 <= cpus <= MAX_CPUS:
            self._status(f"Agrega entre 1 y {MAX_CPUS} jugadores CPU.", ok=False)
            return
        self.on_start()
