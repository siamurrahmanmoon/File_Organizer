"""
ui/widgets.py - Reusable Custom GUI Components and Widgets.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable, Optional, Any


class PathSelector(ttk.Frame):
    """A clean directory/file path selector with entry and browse button."""

    def __init__(
        self,
        parent,
        label_text: str,
        default_path: str = "",
        is_directory: bool = True,
        on_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.is_directory = is_directory
        self.on_change = on_change

        self.columnconfigure(1, weight=1)

        ttk.Label(self, text=label_text, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(0, 10), sticky=tk.W)

        self.path_var = tk.StringVar(value=default_path)
        if self.on_change:
            self.path_var.trace_add("write", lambda *_: self.on_change(self.path_var.get()))

        self.entry = ttk.Entry(self, textvariable=self.path_var, font=("Segoe UI", 9))
        self.entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        self.browse_btn = ttk.Button(self, text="📂 Browse", command=self._browse)
        self.browse_btn.grid(row=0, column=2)

    def _browse(self):
        if self.is_directory:
            chosen = filedialog.askdirectory(initialdir=self.path_var.get() or ".")
        else:
            chosen = filedialog.askopenfilename(initialdir=self.path_var.get() or ".")
        if chosen:
            self.path_var.set(chosen)

    def get(self) -> str:
        return self.path_var.get().strip()

    def set(self, val: str):
        self.path_var.set(val)


class StatCard(ttk.Frame):
    """Displays a numeric stat with a label inside a card frame."""

    def __init__(self, parent, title: str, initial_val: str = "0", value_color: str = "#38bdf8", **kwargs):
        super().__init__(parent, padding="10", **kwargs)
        self.columnconfigure(0, weight=1)

        self.val_var = tk.StringVar(value=initial_val)
        self.val_label = tk.Label(
            self,
            textvariable=self.val_var,
            font=("Segoe UI", 16, "bold"),
            fg=value_color,
            bg="#1e293b"
        )
        self.val_label.grid(row=0, column=0)

        self.title_label = tk.Label(
            self,
            text=title.upper(),
            font=("Segoe UI", 8, "bold"),
            fg="#94a3b8",
            bg="#1e293b"
        )
        self.title_label.grid(row=1, column=0, pady=(2, 0))

    def update_value(self, new_val: Any):
        self.val_var.set(str(new_val))
