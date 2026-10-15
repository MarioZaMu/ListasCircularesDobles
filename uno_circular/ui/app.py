"""Main window: switches between setup and game, with the structure panel on the right."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from game.uno_game import UnoGame
from models.player import Player
from models.uno_table import UnoTable
from ui.setup_view import SetupView
from ui.structure_panel import StructurePanel
from ui.table_view import MUTED, RingCanvas, TableView

DEFAULT_PLAYERS: tuple[tuple[str, bool], ...] = (
    ("Tú", True), ("Ana", False), ("Luis", False), ("Sofía", False),
)


class UnoApp(ctk.CTk):
    """CustomTkinter application window."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("UNO · Lista Circular Doble — Estructuras de Datos")
        # Fit the window to the screen (leave room for the taskbar).
        width = min(1440, self.winfo_screenwidth() - 40)
        height = min(900, self.winfo_screenheight() - 90)
        self.geometry(f"{width}x{height}+10+10")
        self.minsize(min(1100, width), min(680, height))

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=430)
        self.grid_rowconfigure(0, weight=1)

        self.table = UnoTable()
        self.content: SetupView | TableView | None = None
        self.panel = StructurePanel(self, get_ring=self._current_ring)
        self.panel.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        self.show_setup()

    # ---------------------------------------------------------------- views
    def _current_ring(self) -> RingCanvas | None:
        return getattr(self.content, "ring", None)

    def _swap(self, view: SetupView | TableView) -> None:
        self.panel.stop_walk()
        if self.content is not None:
            if isinstance(self.content, TableView):
                self.content.stop()
            self.content.destroy()
        self.content = view
        view.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

    def show_setup(self) -> None:
        """Create an empty table and show the setup screen with default players."""
        self.table = UnoTable()
        self.panel.set_table(self.table)
        self.panel.log("Nueva mesa: head = None, size = 0")
        view = SetupView(self, self.table, on_change=self.panel.refresh, on_start=self.start_game)
        self._swap(view)
        for name, is_human in DEFAULT_PLAYERS:
            self.table.add_player_last(Player(name, is_human=is_human))
        view.refresh()

    def start_game(self) -> None:
        """Build an ``UnoGame`` on the configured table and show the game screen."""
        self.panel.log("— Comienza la partida —")
        game = UnoGame(self.table)
        view = TableView(self, game, on_change=self.panel.refresh,
                         on_game_over=self._show_results, on_quit=self._confirm_quit)
        game.on_event = view.add_event
        self._swap(view)
        game.start()
        view.begin()

    # -------------------------------------------------------------- dialogs
    def _confirm_quit(self) -> None:
        if messagebox.askyesno("Abandonar partida", "¿Volver a la configuración? "
                               "Se perderá la partida actual.", parent=self):
            self.show_setup()
        elif isinstance(self.content, TableView):
            self.content.begin()

    def _show_results(self, game: UnoGame) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Resultados")
        dialog.geometry("360x380")
        dialog.resizable(False, False)
        dialog.transient(self)

        ctk.CTkLabel(dialog, text="¡Partida terminada!",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(dialog, text="Orden en que salieron de la mesa (remove_player)",
                     text_color=MUTED).pack(pady=(0, 12))
        for place, name in enumerate(game.rankings, start=1):
            ctk.CTkLabel(dialog, text=f"{place}.º  {name}",
                         font=ctk.CTkFont(size=16, weight="bold" if place == 1 else "normal")).pack(pady=2)

        def new_game() -> None:
            dialog.destroy()
            self.show_setup()

        ctk.CTkButton(dialog, text="Nueva partida", command=new_game).pack(pady=(18, 6))
        ctk.CTkButton(dialog, text="Cerrar", fg_color="#3a3f4b", command=dialog.destroy).pack()
        dialog.after(120, dialog.grab_set)
