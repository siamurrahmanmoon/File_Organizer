"""
ui/tabs/preview_tab.py - Side-by-Side Diff Preview & Selective Rename Table.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Dict, Any


class PreviewTab(ttk.Frame):
    """Side-by-side Before/After diff viewer with selective file execution."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app
        self.planned_items: List[Dict[str, Any]] = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_top_controls()
        self._build_table()
        self._build_bottom_controls()

    def _build_top_controls(self):
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        ctrl_frame.columnconfigure(2, weight=1)

        self.refresh_btn = ttk.Button(
            ctrl_frame,
            text="🔄 Scan & Generate Preview",
            style="Accent.TButton",
            command=self.refresh_preview
        )
        self.refresh_btn.grid(row=0, column=0, padx=(0, 10))

        # Search filter
        ttk.Label(ctrl_frame, text="🔍 Filter:", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, padx=(10, 5))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._filter_table())
        self.filter_entry = ttk.Entry(ctrl_frame, textvariable=self.filter_var)
        self.filter_entry.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(0, 10))

        self.count_lbl = ttk.Label(ctrl_frame, text="0 items found", font=("Segoe UI", 9))
        self.count_lbl.grid(row=0, column=3)

    def _build_table(self):
        table_frame = ttk.Frame(self)
        table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("status", "original", "renamed", "year", "resolution", "codec")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended"
        )

        self.tree.heading("status", text="Status")
        self.tree.heading("original", text="Original Filename")
        self.tree.heading("renamed", text="New Formatted Name")
        self.tree.heading("year", text="Year")
        self.tree.heading("resolution", text="Resolution")
        self.tree.heading("codec", text="Codec")

        self.tree.column("status", width=80, anchor=tk.CENTER)
        self.tree.column("original", width=340)
        self.tree.column("renamed", width=380)
        self.tree.column("year", width=70, anchor=tk.CENTER)
        self.tree.column("resolution", width=80, anchor=tk.CENTER)
        self.tree.column("codec", width=80, anchor=tk.CENTER)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def _build_bottom_controls(self):
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.apply_selected_btn = ttk.Button(
            bottom_frame,
            text="⚡ Apply & Rename Selected",
            style="Success.TButton",
            command=self._apply_selected
        )
        self.apply_selected_btn.pack(side=tk.RIGHT, padx=5)

        self.select_all_btn = ttk.Button(
            bottom_frame,
            text="Select All",
            command=self._select_all
        )
        self.select_all_btn.pack(side=tk.LEFT, padx=5)

        self.deselect_all_btn = ttk.Button(
            bottom_frame,
            text="Deselect All",
            command=self._deselect_all
        )
        self.deselect_all_btn.pack(side=tk.LEFT, padx=5)

    def refresh_preview(self):
        """Scans source folder and populates the Before/After diff table."""
        source_dir = self.main_app.get_source_path()
        if not source_dir or not Path(source_dir).exists():
            messagebox.showwarning("Warning", "Please select a valid Source directory in the Organize tab first.")
            return

        self.tree.delete(*self.tree.get_children())
        self.planned_items.clear()

        organizer = self.main_app.get_organizer_instance()
        src_path = Path(source_dir)

        count = 0
        glob_pattern = "**/*" if organizer.config.process_subfolders else "*"
        for p in src_path.glob(glob_pattern):
            if p.is_file() and p.suffix.lower() in organizer.video_extensions:
                plan = organizer.plan_file_rename(p)
                info = plan["parsed_info"]
                item_data = {
                    "source_path": p,
                    "target_name": plan["target_name"],
                    "status": "Ready",
                    "original": p.name,
                    "renamed": plan["target_name"],
                    "year": info.get("Year", "-"),
                    "resolution": info.get("Resolution", "-"),
                    "codec": info.get("VideoCodec", "-"),
                }
                self.planned_items.append(item_data)
                count += 1

        self._populate_table(self.planned_items)
        self.count_lbl.config(text=f"{count} files loaded")

    def _populate_table(self, items: List[Dict[str, Any]]):
        self.tree.delete(*self.tree.get_children())
        for idx, it in enumerate(items):
            self.tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(
                    it["status"],
                    it["original"],
                    it["renamed"],
                    it["year"],
                    it["resolution"],
                    it["codec"]
                )
            )

    def _filter_table(self):
        query = self.filter_var.get().lower().strip()
        if not query:
            self._populate_table(self.planned_items)
            return

        filtered = [
            it for it in self.planned_items
            if query in it["original"].lower() or query in it["renamed"].lower()
        ]
        self._populate_table(filtered)

    def _select_all(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)

    def _deselect_all(self):
        self.tree.selection_remove(self.tree.selection())

    def _apply_selected(self):
        selected_ids = self.tree.selection()
        if not selected_ids:
            messagebox.showinfo("Info", "Please select one or more files in the table to rename.")
            return

        if not messagebox.askyesno("Confirm", f"Rename {len(selected_ids)} selected file(s)?"):
            return

        organizer = self.main_app.get_organizer_instance()
        out_dir = Path(self.main_app.get_output_path())
        success_count = 0

        for iid in selected_ids:
            idx = int(iid)
            if idx < len(self.planned_items):
                item = self.planned_items[idx]
                src = item["source_path"]
                rel = src.parent.relative_to(organizer.source_path) if organizer.config.process_subfolders else Path("")
                target_folder = out_dir / rel
                res = organizer.process_file(src, target_folder, dry_run=False)
                if res == "success":
                    self.tree.set(iid, "status", "✅ Renamed")
                    success_count += 1
                else:
                    self.tree.set(iid, "status", "❌ Failed")

        messagebox.showinfo("Done", f"Successfully organized {success_count} file(s)!")
