"""
ui/tabs/watch_tab.py - Automated Watch Folder & Webhook Notifications Controls.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui.widgets import PathSelector
from core.watch_folder import WatchFolderService
from core.notifier import Notifier
from pathlib import Path


class WatchTab(ttk.Frame):
    """Automated watch folder scheduler and Discord / Telegram webhook settings."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app
        self.watcher_service = None

        self.columnconfigure(0, weight=1)

        self._build_watch_folder_section()
        self._build_webhook_section()

    def _build_watch_folder_section(self):
        watch_frame = ttk.LabelFrame(self, text="👀 Automated Background Folder Watcher", padding="12")
        watch_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        watch_frame.columnconfigure(0, weight=1)

        self.watch_path_selector = PathSelector(
            watch_frame,
            label_text="Watch Directory: ",
            default_path=r"R:\Anime_Downloads"
        )
        self.watch_path_selector.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # Options
        opts_frame = ttk.Frame(watch_frame)
        opts_frame.grid(row=1, column=0, sticky=tk.W, pady=5)

        ttk.Label(opts_frame, text="Poll Interval (sec):").pack(side=tk.LEFT, padx=(0, 5))
        self.poll_var = tk.IntVar(value=30)
        ttk.Spinbox(opts_frame, from_=5, to=3600, textvariable=self.poll_var, width=6).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(opts_frame, text="Write Stability Delay (sec):").pack(side=tk.LEFT, padx=(0, 5))
        self.stability_var = tk.IntVar(value=10)
        ttk.Spinbox(opts_frame, from_=2, to=300, textvariable=self.stability_var, width=6).pack(side=tk.LEFT)

        # Action Buttons
        btn_frame = ttk.Frame(watch_frame)
        btn_frame.grid(row=2, column=0, sticky=tk.W, pady=8)

        self.start_watch_btn = ttk.Button(
            btn_frame,
            text="▶️ Start Folder Watcher",
            style="Accent.TButton",
            command=self._start_watcher
        )
        self.start_watch_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_watch_btn = ttk.Button(
            btn_frame,
            text="⏹️ Stop Watcher",
            style="Danger.TButton",
            state=tk.DISABLED,
            command=self._stop_watcher
        )
        self.stop_watch_btn.pack(side=tk.LEFT)

        self.watch_status_lbl = ttk.Label(btn_frame, text="Status: Inactive", foreground="#94a3b8")
        self.watch_status_lbl.pack(side=tk.LEFT, padx=15)

    def _build_webhook_section(self):
        webhook_frame = ttk.LabelFrame(self, text="🔔 Webhook Notifications (Discord / Telegram)", padding="12")
        webhook_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        webhook_frame.columnconfigure(1, weight=1)

        # Discord
        ttk.Label(webhook_frame, text="Discord Webhook URL: ", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.discord_url_var = tk.StringVar()
        ttk.Entry(webhook_frame, textvariable=self.discord_url_var, font=("Consolas", 9)).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Button(
            webhook_frame,
            text="🔔 Test Discord",
            command=self._test_discord
        ).grid(row=0, column=2, padx=5)

        # Telegram
        ttk.Label(webhook_frame, text="Telegram Bot Token: ", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.tg_token_var = tk.StringVar()
        ttk.Entry(webhook_frame, textvariable=self.tg_token_var, font=("Consolas", 9)).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Label(webhook_frame, text="Telegram Chat ID: ", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.tg_chat_var = tk.StringVar()
        ttk.Entry(webhook_frame, textvariable=self.tg_chat_var, font=("Consolas", 9)).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Button(
            webhook_frame,
            text="✈️ Test Telegram",
            command=self._test_telegram
        ).grid(row=2, column=2, padx=5)

    def _start_watcher(self):
        watch_path = self.watch_path_selector.get()
        if not watch_path or not Path(watch_path).exists():
            messagebox.showerror("Error", "Please specify a valid watch directory.")
            return

        organizer = self.main_app.get_organizer_instance()
        out_dir = Path(self.main_app.get_output_path())

        def on_file_ready(file_p: Path):
            organizer.process_file(file_p, out_dir, dry_run=False)

        self.watcher_service = WatchFolderService(
            watch_path,
            process_callback=on_file_ready,
            video_extensions=organizer.video_extensions,
            poll_interval=self.poll_var.get(),
            stability_wait=self.stability_var.get()
        )
        self.watcher_service.start()
        self.start_watch_btn.config(state=tk.DISABLED)
        self.stop_watch_btn.config(state=tk.NORMAL)
        self.watch_status_lbl.config(text="Status: 🟢 Active Watching", foreground="#34d399")

    def _stop_watcher(self):
        if self.watcher_service:
            self.watcher_service.stop()
            self.watcher_service = None
        self.start_watch_btn.config(state=tk.NORMAL)
        self.stop_watch_btn.config(state=tk.DISABLED)
        self.watch_status_lbl.config(text="Status: Inactive", foreground="#94a3b8")

    def _test_discord(self):
        url = self.discord_url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a Discord Webhook URL first.")
            return
        dummy_summary = {"processed": 10, "skipped": 2, "duplicates": 1, "errors": 0, "duration_seconds": 3.5, "files_per_sec": 3.4}
        success = Notifier.send_discord_webhook(url, dummy_summary)
        if success:
            messagebox.showinfo("Success", "Discord test notification sent successfully!")
        else:
            messagebox.showerror("Error", "Failed to send Discord webhook notification. Please check URL.")

    def _test_telegram(self):
        token = self.tg_token_var.get().strip()
        chat_id = self.tg_chat_var.get().strip()
        if not token or not chat_id:
            messagebox.showwarning("Warning", "Please enter Telegram Bot Token and Chat ID.")
            return
        success = Notifier.send_telegram_message(token, chat_id, "🎬 *Anime Organizer Pro* test notification!")
        if success:
            messagebox.showinfo("Success", "Telegram notification sent successfully!")
        else:
            messagebox.showerror("Error", "Failed to send Telegram message.")
