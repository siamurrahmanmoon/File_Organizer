"""
ui/tabs/filter_tab.py - Granular Filtering Controls & Regex Pattern Builder.
"""

import tkinter as tk
from tkinter import ttk
import re


class FilterTab(ttk.Frame):
    """Granular filter controls: file size, resolution, codec, language, and regex tester."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app

        self.columnconfigure((0, 1), weight=1)

        self._build_size_and_year_filters()
        self._build_resolution_and_codec_filters()
        self._build_regex_pattern_tester()

    def _build_size_and_year_filters(self):
        size_frame = ttk.LabelFrame(self, text="📏 Size & Year Restrictions", padding="12")
        size_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        size_frame.columnconfigure(1, weight=1)

        # Min / Max Size
        ttk.Label(size_frame, text="Min Size (MB):").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.min_size_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(size_frame, from_=0, to=50000, increment=50, textvariable=self.min_size_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=4)

        ttk.Label(size_frame, text="Max Size (MB):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.max_size_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(size_frame, from_=0, to=100000, increment=500, textvariable=self.max_size_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=4)

        # Year range
        ttk.Label(size_frame, text="Min Year:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.min_year_var = tk.IntVar(value=1950)
        ttk.Spinbox(size_frame, from_=1900, to=2099, textvariable=self.min_year_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=4)

        ttk.Label(size_frame, text="Max Year:").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.max_year_var = tk.IntVar(value=2099)
        ttk.Spinbox(size_frame, from_=1900, to=2099, textvariable=self.max_year_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=4)

    def _build_resolution_and_codec_filters(self):
        media_frame = ttk.LabelFrame(self, text="🎬 Allowed Resolution & Codecs", padding="12")
        media_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        ttk.Label(media_frame, text="Filter Resolutions (Leave blank for all):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))
        self.res_vars = {}
        for r in ["4K", "1080p", "720p", "480p"]:
            var = tk.BooleanVar(value=False)
            self.res_vars[r] = var
            ttk.Checkbutton(media_frame, text=r, variable=var).pack(anchor=tk.W)

        ttk.Separator(media_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(media_frame, text="Filter Video Codecs:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))
        self.codec_vars = {}
        for c in ["x265", "HEVC", "x264", "AV1"]:
            var = tk.BooleanVar(value=False)
            self.codec_vars[c] = var
            ttk.Checkbutton(media_frame, text=c, variable=var).pack(anchor=tk.W)

    def _build_regex_pattern_tester(self):
        regex_frame = ttk.LabelFrame(self, text="🎨 Advanced Custom Regex Tester & Filter", padding="12")
        regex_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=10)
        regex_frame.columnconfigure(1, weight=1)

        self.enable_custom_regex_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            regex_frame,
            text="Enable Custom Regex Filter (Only process files matching the pattern below)",
            variable=self.enable_custom_regex_var
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))

        ttk.Label(regex_frame, text="Regex Pattern: ", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.regex_pattern_var = tk.StringVar(value=r"")
        self.regex_pattern_var.trace_add("write", lambda *_: self._test_regex())
        ttk.Entry(regex_frame, textvariable=self.regex_pattern_var, font=("Consolas", 10)).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=4)

        ttk.Label(regex_frame, text="Test Filename: ", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.regex_test_str_var = tk.StringVar(value="Attack on Titan S04E12 (1080p).mkv")
        self.regex_test_str_var.trace_add("write", lambda *_: self._test_regex())
        ttk.Entry(regex_frame, textvariable=self.regex_test_str_var, font=("Consolas", 10)).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=4)

        ttk.Label(regex_frame, text="Match Result: ", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky=tk.W, pady=4)
        self.regex_result_var = tk.StringVar(value="ℹ️ Enter a pattern to test")
        self.regex_result_lbl = tk.Label(
            regex_frame,
            textvariable=self.regex_result_var,
            font=("Segoe UI", 9, "bold"),
            fg="#94a3b8",
            bg="#1e293b",
            padx=5,
            pady=3
        )
        self.regex_result_lbl.grid(row=3, column=1, sticky=tk.W, pady=4)

        self._test_regex()

    def _test_regex(self):
        pattern = self.regex_pattern_var.get()
        test_str = self.regex_test_str_var.get()
        if not pattern:
            self.regex_result_var.set("ℹ️ Empty pattern (all files match)")
            self.regex_result_lbl.config(fg="#94a3b8")
            return

        try:
            m = re.search(pattern, test_str, re.IGNORECASE)
            if m:
                self.regex_result_var.set(f"✅ MATCH FOUND: '{m.group(0)}'")
                self.regex_result_lbl.config(fg="#34d399")
            else:
                self.regex_result_var.set("❌ NO MATCH")
                self.regex_result_lbl.config(fg="#f87171")
        except re.error as e:
            self.regex_result_var.set(f"⚠️ Regex Error: {e}")
            self.regex_result_lbl.config(fg="#facc15")
