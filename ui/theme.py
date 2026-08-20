"""
ui/theme.py - Modern Design Theme & Styling Tokens for Tkinter / TTK.
"""

import tkinter as tk
from tkinter import ttk


class ModernTheme:
    """Manages color schemes and modern widget styles."""

    # Dark Theme Colors
    BG_DARK = "#0f172a"          # Slate 900
    BG_CARD_DARK = "#1e293b"     # Slate 800
    BG_INPUT_DARK = "#334155"    # Slate 700
    TEXT_PRIMARY_DARK = "#f8fafc" # Slate 50
    TEXT_MUTED_DARK = "#94a3b8"   # Slate 400
    ACCENT_PRIMARY = "#3b82f6"   # Blue 500
    ACCENT_SUCCESS = "#10b981"   # Emerald 500
    ACCENT_WARNING = "#f59e0b"   # Amber 500
    ACCENT_DANGER = "#ef4444"    # Red 500
    BORDER_COLOR = "#334155"

    @classmethod
    def apply_theme(cls, root: tk.Tk):
        """Configures modern ttk styles on the root window."""
        style = ttk.Style(root)
        style.theme_use("clam")

        # Configure Fonts
        font_family = "Segoe UI"
        style.configure(".", font=(font_family, 9))

        # Notebook (Tabs)
        style.configure(
            "TNotebook",
            background="#1e293b",
            tabmargins=[2, 5, 2, 0]
        )
        style.configure(
            "TNotebook.Tab",
            padding=[14, 8],
            font=(font_family, 10, "bold"),
            background="#0f172a",
            foreground="#94a3b8"
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#3b82f6"), ("active", "#1e293b")],
            foreground=[("selected", "#ffffff"), ("active", "#f8fafc")]
        )

        # Buttons
        style.configure(
            "Accent.TButton",
            font=(font_family, 10, "bold"),
            background="#3b82f6",
            foreground="#ffffff",
            borderwidth=0,
            padding=[12, 6]
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#2563eb"), ("disabled", "#64748b")]
        )

        style.configure(
            "Success.TButton",
            font=(font_family, 10, "bold"),
            background="#10b981",
            foreground="#ffffff",
            borderwidth=0,
            padding=[12, 6]
        )
        style.map(
            "Success.TButton",
            background=[("active", "#059669"), ("disabled", "#64748b")]
        )

        style.configure(
            "Danger.TButton",
            font=(font_family, 10, "bold"),
            background="#ef4444",
            foreground="#ffffff",
            borderwidth=0,
            padding=[12, 6]
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#dc2626"), ("disabled", "#64748b")]
        )

        # LabelFrames
        style.configure(
            "TLabelframe",
            background="#1e293b",
            foreground="#f8fafc",
            relief="solid",
            borderwidth=1
        )
        style.configure(
            "TLabelframe.Label",
            background="#1e293b",
            foreground="#38bdf8",
            font=(font_family, 10, "bold")
        )

        # Treeview (Tables)
        style.configure(
            "Treeview",
            background="#1e293b",
            foreground="#f8fafc",
            fieldbackground="#1e293b",
            rowheight=26,
            font=(font_family, 9)
        )
        style.configure(
            "Treeview.Heading",
            background="#0f172a",
            foreground="#94a3b8",
            font=(font_family, 9, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")]
        )

        # Progressbar
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#0f172a",
            background="#3b82f6",
            thickness=12
        )
