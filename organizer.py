import sys
import os

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Automatically enforce running inside project's virtual environment (venv)
from utils.venv_utils import ensure_venv
ensure_venv()

import tkinter as tk
from ui.main_window import AnimeOrganizerGUI
from core.engine import AnimeFileOrganizer
from config import get_default_config


def main():
    # If arguments are passed on command line, dispatch to CLI
    if len(sys.argv) > 1:
        from cli import main as cli_main
        cli_main()
        return

    # Otherwise launch modern GUI
    root = tk.Tk()
    app = AnimeOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
