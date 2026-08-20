"""
ui/tabs/template_tab.py - Custom Naming Template Builder with Clickable Tags & Live Simulator.
"""

import tkinter as tk
from tkinter import ttk
from core.template_engine import TemplateEngine
from core.parser import SmartMediaParser
from config import DEFAULT_TEMPLATES


class TemplateTab(ttk.Frame):
    """Interactive Template Builder with clickable tokens and real-time simulator."""

    def __init__(self, parent, main_app, **kwargs):
        super().__init__(parent, padding="15", **kwargs)
        self.main_app = main_app

        self.columnconfigure(0, weight=1)

        self._build_template_picker()
        self._build_token_palette()
        self._build_live_simulator()

    def _build_template_picker(self):
        picker_frame = ttk.LabelFrame(
            self, text="📝 Naming Template Configuration", padding="12"
        )
        picker_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        picker_frame.columnconfigure(1, weight=1)

        # Presets dropdown
        ttk.Label(
            picker_frame, text="Preset Templates: ", font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, sticky=tk.W, pady=4)
        self.preset_combo = ttk.Combobox(
            picker_frame, values=list(DEFAULT_TEMPLATES.keys()), state="readonly"
        )
        self.preset_combo.set("Standard")
        self.preset_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=4)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        # Template Entry
        ttk.Label(
            picker_frame, text="Custom Pattern: ", font=("Segoe UI", 9, "bold")
        ).grid(row=1, column=0, sticky=tk.W, pady=8)
        self.template_var = tk.StringVar(
            value="{Title} ({Year}) [{Languages}] [{Resolution}] - S{Season}E{Episode}"
        )
        self.template_var.trace_add("write", lambda *_: self._update_simulation())

        self.template_entry = ttk.Entry(
            picker_frame, textvariable=self.template_var, font=("Consolas", 11)
        )
        self.template_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=8)

        # Validation status
        self.val_status_var = tk.StringVar(value="✅ Template syntax is valid.")
        self.val_lbl = ttk.Label(
            picker_frame,
            textvariable=self.val_status_var,
            font=("Segoe UI", 8),
            foreground="#34d399",
        )
        self.val_lbl.grid(row=2, column=1, sticky=tk.W)

    def _build_token_palette(self):
        palette_frame = ttk.LabelFrame(
            self, text="🏷️ Clickable Token Palette (Click to Insert)", padding="12"
        )
        palette_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)

        tokens = [
            ("{Title}", "Anime Title"),
            ("{Year}", "Release Year (e.g. 2024)"),
            ("{Season}", "Season Number (01)"),
            ("{Episode}", "Episode Number (05)"),
            ("{EpisodeRange}", "Multi-Episode (E01-E04)"),
            ("{Resolution}", "Resolution (1080p, 4K)"),
            ("{Codec}", "Video Codec (x265, AV1)"),
            ("{AudioCodec}", "Audio Codec (AAC, FLAC)"),
            ("{AudioChannels}", "Audio Channels (5.1, Stereo)"),
            ("{AudioLang}", "Audio Language (Japanese, Hindi)"),
            ("{Languages}", "Detected Languages (Hindi, English, Japanese)"),
            ("{Group}", "Release Group (SubsPlease)"),
            ("{Bitrate}", "Bitrate (12Mbps)"),
            ("{FPS}", "Frame Rate (24fps)"),
            ("{Type}", "Type (Movie, OVA, Special)"),
        ]

        # Arrange in a grid of 4 columns
        for idx, (token_code, token_desc) in enumerate(tokens):
            r = idx // 4
            c = idx % 4
            btn = ttk.Button(
                palette_frame,
                text=token_code,
                command=lambda t=token_code: self._insert_token(t),
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky=(tk.W, tk.E))
            palette_frame.columnconfigure(c, weight=1)

    def _build_live_simulator(self):
        sim_frame = ttk.LabelFrame(
            self, text="⚡ Live Simulation & Test Preview", padding="12"
        )
        sim_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        sim_frame.columnconfigure(1, weight=1)

        ttk.Label(
            sim_frame, text="Sample Raw Filename: ", font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, sticky=tk.W, pady=4)
        self.sample_input_var = tk.StringVar(
            value="[SubsPlease] Bleach - Thousand-Year Blood War - 01 (1080p) [x265] [7A8B9C0D].mkv"
        )
        self.sample_input_var.trace_add("write", lambda *_: self._update_simulation())
        ttk.Entry(
            sim_frame, textvariable=self.sample_input_var, font=("Consolas", 9)
        ).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=4)

        ttk.Label(
            sim_frame, text="Rendered Result: ", font=("Segoe UI", 9, "bold")
        ).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.sample_output_var = tk.StringVar()
        self.output_lbl = tk.Label(
            sim_frame,
            textvariable=self.sample_output_var,
            font=("Consolas", 10, "bold"),
            fg="#38bdf8",
            bg="#0f172a",
            padx=8,
            pady=8,
            anchor="w",
        )
        self.output_lbl.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=4)

        self._update_simulation()

    def _insert_token(self, token: str):
        pos = self.template_entry.index(tk.INSERT)
        current = self.template_var.get()
        new_text = current[:pos] + token + current[pos:]
        self.template_var.set(new_text)
        self.template_entry.icursor(pos + len(token))
        self.template_entry.focus()

    def _on_preset_selected(self, event=None):
        name = self.preset_combo.get()
        if name in DEFAULT_TEMPLATES:
            self.template_var.set(DEFAULT_TEMPLATES[name])

    def _update_simulation(self):
        template = self.template_var.get()
        is_valid, msg = TemplateEngine.validate_template(template)
        if not is_valid:
            self.val_status_var.set(f"❌ {msg}")
            self.val_lbl.config(foreground="#f87171")
            self.sample_output_var.set("[Invalid Template]")
            return

        self.val_status_var.set("✅ Template syntax is valid.")
        self.val_lbl.config(foreground="#34d399")

        raw_sample = self.sample_input_var.get()
        parsed = SmartMediaParser.parse_filename(raw_sample)
        if not parsed.get("Year"):
            parsed["Year"] = "2023"
        if not parsed.get("Resolution"):
            parsed["Resolution"] = "1080p"
        if not parsed.get("VideoCodec"):
            parsed["VideoCodec"] = "x265"

        rendered = TemplateEngine.render(template, parsed, extension=".mkv")
        self.sample_output_var.set(rendered)
