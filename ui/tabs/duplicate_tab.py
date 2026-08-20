"""
ui/tabs/duplicate_tab.py - Duplicate Detection Manager & Quarantine Vault.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from pathlib import Path
from core.duplicate_detector import DuplicateDetector
from config import QUARANTINE_DIR


class DuplicateTab(ttk.Frame):
    """Duplicate file detection scanner, quality comparisons, and quarantine management."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_settings_section()
        self._build_quarantine_section()

    def _build_settings_section(self):
        settings_frame = ttk.LabelFrame(self, text="🔍 Duplicate Detection Rules", padding="12")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure((0, 1), weight=1)

        self.enable_dups_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Enable Duplicate Detection Engine", variable=self.enable_dups_var).grid(row=0, column=0, sticky=tk.W, pady=4)

        # Strategy
        ttk.Label(settings_frame, text="Hashing Strategy:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.hash_algo_combo = ttk.Combobox(settings_frame, values=["fast (Head+Mid+Tail)", "sha256", "md5"], state="readonly", width=25)
        self.hash_algo_combo.set("fast (Head+Mid+Tail)")
        self.hash_algo_combo.grid(row=1, column=1, sticky=tk.W, pady=4)

        # Action
        ttk.Label(settings_frame, text="Action on Duplicate:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.dup_action_combo = ttk.Combobox(settings_frame, values=["quarantine (Safe Vault)", "skip", "overwrite_if_better"], state="readonly", width=25)
        self.dup_action_combo.set("quarantine (Safe Vault)")
        self.dup_action_combo.grid(row=2, column=1, sticky=tk.W, pady=4)

    def _build_quarantine_section(self):
        vault_frame = ttk.LabelFrame(self, text="📦 Quarantine Vault Manager", padding="12")
        vault_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        vault_frame.columnconfigure(0, weight=1)
        vault_frame.rowconfigure(1, weight=1)

        # Top buttons
        btn_frame = ttk.Frame(vault_frame)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))

        ttk.Button(btn_frame, text="🔄 Refresh Quarantine", command=self.refresh_quarantine).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 Open Quarantine Folder", command=self._open_quarantine_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Empty Quarantine", style="Danger.TButton", command=self._empty_quarantine).pack(side=tk.RIGHT, padx=5)

        # Treeview
        columns = ("filename", "size_mb", "quarantined_date")
        self.tree = ttk.Treeview(vault_frame, columns=columns, show="headings")
        self.tree.heading("filename", text="Quarantined File")
        self.tree.heading("size_mb", text="Size (MB)")
        self.tree.heading("quarantined_date", text="Date Added")

        self.tree.column("filename", width=400)
        self.tree.column("size_mb", width=100, anchor=tk.CENTER)
        self.tree.column("quarantined_date", width=150, anchor=tk.CENTER)

        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def refresh_quarantine(self):
        self.tree.delete(*self.tree.get_children())
        if not QUARANTINE_DIR.exists():
            return

        for p in QUARANTINE_DIR.iterdir():
            if p.is_file():
                stat = p.stat()
                size_mb = f"{stat.st_size / (1024*1024):.2f}"
                import datetime
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                self.tree.insert("", tk.END, values=(p.name, size_mb, mtime))

    def _open_quarantine_folder(self):
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(QUARANTINE_DIR))

    def _empty_quarantine(self):
        if not messagebox.askyesno("Confirm", "Permanently delete all files in the quarantine vault?"):
            return
        for p in QUARANTINE_DIR.iterdir():
            try:
                if p.is_file():
                    p.unlink()
            except Exception:
                pass
        self.refresh_quarantine()
        messagebox.showinfo("Success", "Quarantine vault emptied.")
