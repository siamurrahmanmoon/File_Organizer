"""
ui/tabs/rollback_tab.py - SQLite Operation Journal History & 1-Click Rollback / Undo.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.rollback_manager import RollbackManager


class RollbackTab(ttk.Frame):
    """Session history viewer and 1-Click Rollback/Undo manager."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app
        self.rollback_mgr = RollbackManager()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()
        self._build_table()
        self._build_action_buttons()

    def _build_header(self):
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(
            header_frame,
            text="🔄 Operation Journal & Undo History",
            font=("Segoe UI", 12, "bold")
        ).pack(side=tk.LEFT)

        ttk.Button(
            header_frame,
            text="🔄 Refresh History",
            command=self.refresh_history
        ).pack(side=tk.RIGHT)

    def _build_table(self):
        table_frame = ttk.Frame(self)
        table_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("session_id", "start_time", "source_dir", "files", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("session_id", text="Session ID")
        self.tree.heading("start_time", text="Timestamp")
        self.tree.heading("source_dir", text="Source Folder")
        self.tree.heading("files", text="Files Processed")
        self.tree.heading("status", text="Status")

        self.tree.column("session_id", width=180)
        self.tree.column("start_time", width=160)
        self.tree.column("source_dir", width=300)
        self.tree.column("files", width=100, anchor=tk.CENTER)
        self.tree.column("status", width=100, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))

    def _build_action_buttons(self):
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.rollback_btn = ttk.Button(
            btn_frame,
            text="⏪ Rollback / Undo Selected Session",
            style="Danger.TButton",
            command=self._execute_rollback
        )
        self.rollback_btn.pack(side=tk.RIGHT, padx=5)

    def refresh_history(self):
        self.tree.delete(*self.tree.get_children())
        sessions = self.rollback_mgr.list_sessions(limit=30)
        for s in sessions:
            self.tree.insert(
                "",
                tk.END,
                iid=s["session_id"],
                values=(
                    s["session_id"],
                    s["start_time"].replace("T", " ")[:19],
                    s["source_dir"],
                    s["processed_files"],
                    s["status"].upper()
                )
            )

    def _execute_rollback(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a session from the list to rollback.")
            return

        session_id = selected[0]
        if not messagebox.askyesno(
            "Confirm Rollback",
            f"Are you sure you want to reverse all file moves from session:\n{session_id}?\n\nFiles will be moved back to their original locations."
        ):
            return

        success_count, error_count, errors = self.rollback_mgr.rollback_session(session_id)
        self.refresh_history()

        if error_count == 0:
            messagebox.showinfo("Success", f"Rollback complete! Successfully restored {success_count} files.")
        else:
            messagebox.showwarning(
                "Partial Rollback",
                f"Restored {success_count} files.\nEncountered {error_count} error(s):\n" + "\n".join(errors[:5])
            )
