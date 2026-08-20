"""
ui/tabs/analytics_tab.py - Processing History Analytics & Multi-Format Report Exporter.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from pathlib import Path
from ui.widgets import StatCard
from config import REPORTS_DIR


class AnalyticsTab(ttk.Frame):
    """Analytics dashboard and multi-format report exporter."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app

        self.columnconfigure(0, weight=1)

        self._build_metric_cards()
        self._build_export_section()

    def _build_metric_cards(self):
        cards_frame = ttk.LabelFrame(self, text="📊 Live Session Metrics", padding="12")
        cards_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.processed_card = StatCard(cards_frame, title="Processed Files", initial_val="0", value_color="#34d399")
        self.processed_card.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.skipped_card = StatCard(cards_frame, title="Skipped Files", initial_val="0", value_color="#facc15")
        self.skipped_card.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.duplicates_card = StatCard(cards_frame, title="Duplicates", initial_val="0", value_color="#c084fc")
        self.duplicates_card.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.errors_card = StatCard(cards_frame, title="Errors", initial_val="0", value_color="#f87171")
        self.errors_card.grid(row=0, column=3, padx=5, pady=5, sticky=(tk.W, tk.E))

    def _build_export_section(self):
        export_frame = ttk.LabelFrame(self, text="📑 Export Analytics Reports", padding="12")
        export_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        export_frame.columnconfigure((0, 1, 2, 3), weight=1)

        ttk.Button(
            export_frame,
            text="📊 Export CSV Report",
            command=self._export_csv
        ).grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Button(
            export_frame,
            text="📑 Export JSON Report",
            command=self._export_json
        ).grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Button(
            export_frame,
            text="🌐 Export HTML Dashboard",
            style="Accent.TButton",
            command=self._export_html
        ).grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Button(
            export_frame,
            text="📂 Open Reports Folder",
            command=self._open_reports_folder
        ).grid(row=0, column=3, padx=5, pady=5, sticky=(tk.W, tk.E))

    def update_metrics(self, summary: dict):
        self.processed_card.update_value(summary.get("processed", 0))
        self.skipped_card.update_value(summary.get("skipped", 0))
        self.duplicates_card.update_value(summary.get("duplicates", 0))
        self.errors_card.update_value(summary.get("errors", 0))

    def _export_csv(self):
        organizer = self.main_app.get_organizer_instance()
        if organizer and organizer.analytics:
            path = organizer.analytics.export_csv()
            messagebox.showinfo("Exported", f"CSV Report saved to:\n{path}")

    def _export_json(self):
        organizer = self.main_app.get_organizer_instance()
        if organizer and organizer.analytics:
            path = organizer.analytics.export_json()
            messagebox.showinfo("Exported", f"JSON Report saved to:\n{path}")

    def _export_html(self):
        organizer = self.main_app.get_organizer_instance()
        if organizer and organizer.analytics:
            path = organizer.analytics.export_html()
            messagebox.showinfo("Exported", f"HTML Dashboard Report saved to:\n{path}")
            os.startfile(str(path))

    def _open_reports_folder(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(REPORTS_DIR))
