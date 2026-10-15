"""Entry point: UNO turns modelled with a circular doubly linked list."""

from __future__ import annotations

import sys

if sys.version_info < (3, 10):
    sys.exit("Se requiere Python 3.10 o superior.")


def main() -> None:
    """Launch the CustomTkinter application."""
    from ui.app import UnoApp

    app = UnoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
