"""
Desktop GUI Application for Spatial IR Parser & Validator.
Provides an interactive desktop interface to input spatial descriptions, view JSON IR,
check real-time validation errors, and visualize room adjacency graphs.
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from parser import SpatialNLParser
from validator import SpatialValidator
from visualizer import visualize

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

SAMPLE_DESCRIPTIONS = {
    "4-Room Apartment (Valid)": (
        "The apartment has a living room, a kitchen, a master bedroom, and a bathroom. "
        "The living room is adjacent to the kitchen. "
        "The master bedroom is next to the bathroom. "
        "The kitchen is near the master bedroom. "
        "The bathroom is far from the living room."
    ),
    "5-Room House (Valid)": (
        "The house contains a foyer, living room, dining room, kitchen, and patio. "
        "The foyer is adjacent to the living room. "
        "The living room is connected to the dining room. "
        "The dining room is next to the kitchen. "
        "The kitchen is adjacent to the patio. "
        "The patio is far from the foyer."
    ),
    "Contradictory Layout (Invalid)": (
        "The living room is adjacent to the kitchen. "
        "The kitchen is far from the living room. "
        "The master bedroom is near the dining room."
    ),
}

class SpatialIRApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Spatial IR Desktop Workbench")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        self.parser = SpatialNLParser()
        self.validator = SpatialValidator()
        self.current_img_tk: Optional[Any] = None

        self._configure_styles()
        self._build_ui()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Dark theme color palette
        self.bg_color = "#1E1E2E"
        self.card_color = "#2A2A3C"
        self.text_color = "#CDD6F4"
        self.accent_color = "#89B4FA"
        self.success_color = "#A6E3A1"
        self.error_color = "#F38BA8"

        self.root.configure(bg=self.bg_color)
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Helvetica", 10))
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"), foreground=self.accent_color)
        style.configure("TButton", background=self.card_color, foreground=self.text_color, font=("Helvetica", 10, "bold"), padding=6)
        style.map("TButton", background=[("active", self.accent_color)], foreground=[("active", "#11111B")])

    def _build_ui(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=16, pady=12)

        title_lbl = ttk.Label(header_frame, text="🏗️ Spatial IR Parser & Validator Workbench", style="Header.TLabel")
        title_lbl.pack(side=tk.LEFT)

        # Main paned window (Left: Input & Presets, Right: Results & Viz)
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        # Left Column (Input Controls)
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)

        input_lbl = ttk.Label(left_frame, text="Natural Language Description:", font=("Helvetica", 11, "bold"))
        input_lbl.pack(anchor=tk.W, pady=(0, 6))

        # Sample Preset Dropdown
        preset_frame = ttk.Frame(left_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(preset_frame, text="Load Preset:").pack(side=tk.LEFT, padx=(0, 6))
        self.preset_var = tk.StringVar()
        preset_cb = ttk.Combobox(preset_frame, textvariable=self.preset_var, values=list(SAMPLE_DESCRIPTIONS.keys()), state="readonly", width=28)
        preset_cb.pack(side=tk.LEFT)
        preset_cb.bind("<<ComboboxSelected>>", self._load_preset)

        # Text Input Box
        self.input_text = tk.Text(
            left_frame, wrap=tk.WORD, height=10, bg=self.card_color, fg=self.text_color,
            insertbackground=self.text_color, font=("Consolas", 10), relief=tk.FLAT, padx=8, pady=8
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        self.input_text.insert(tk.END, SAMPLE_DESCRIPTIONS["4-Room Apartment (Valid)"])

        # Action Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)

        parse_btn = ttk.Button(btn_frame, text="▶ Parse & Validate", command=self.process_text)
        parse_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        clear_btn = ttk.Button(btn_frame, text="Clear", command=self._clear_input)
        clear_btn.pack(side=tk.RIGHT)

        # Right Column (Tabs for Output)
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=2)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Validation Report
        self.report_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.report_tab, text="Validation Report")

        self.status_lbl = tk.Label(
            self.report_tab, text="Status: Ready", font=("Helvetica", 12, "bold"),
            bg=self.card_color, fg=self.accent_color, pady=8, anchor="w", padx=12
        )
        self.status_lbl.pack(fill=tk.X, pady=(8, 8))

        self.report_text = tk.Text(
            self.report_tab, wrap=tk.WORD, bg=self.card_color, fg=self.text_color,
            font=("Consolas", 10), relief=tk.FLAT, padx=8, pady=8
        )
        self.report_text.pack(fill=tk.BOTH, expand=True)

        # Tab 2: JSON Spatial IR
        self.json_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.json_tab, text="Spatial IR (JSON)")

        self.json_text = tk.Text(
            self.json_tab, wrap=tk.WORD, bg=self.card_color, fg=self.text_color,
            font=("Consolas", 10), relief=tk.FLAT, padx=8, pady=8
        )
        self.json_text.pack(fill=tk.BOTH, expand=True)

        # Tab 3: Graph Visualization
        self.graph_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_tab, text="Adjacency Graph")

        self.img_lbl = ttk.Label(self.graph_tab, text="Graph visualization will appear here after validation.")
        self.img_lbl.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Initial Process
        self.process_text()

    def _load_preset(self, event=None):
        selected = self.preset_var.get()
        if selected in SAMPLE_DESCRIPTIONS:
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert(tk.END, SAMPLE_DESCRIPTIONS[selected])
            self.process_text()

    def _clear_input(self):
        self.input_text.delete("1.0", tk.END)

    def process_text(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter a natural language description.")
            return

        # 1. Parse into Spatial IR
        spatial_ir = self.parser.parse(text)

        # Update JSON tab
        self.json_text.delete("1.0", tk.END)
        self.json_text.insert(tk.END, spatial_ir.to_json(indent=2))

        # 2. Validate
        result = self.validator.validate(spatial_ir)

        # Update Status Badge & Report
        self.report_text.delete("1.0", tk.END)
        if result.is_valid:
            self.status_lbl.config(text="Status: VALID ✔", bg="#1E3A29", fg=self.success_color)
            report_str = "SUCCESS: All spatial constraints passed!\n\n"
        else:
            self.status_lbl.config(text=f"Status: INVALID ✖ ({len(result.errors)} errors)", bg="#3A1E29", fg=self.error_color)
            report_str = "ERRORS DETECTED:\n" + "\n".join(f" - {e}" for e in result.errors) + "\n\n"

        if result.warnings:
            report_str += "WARNINGS:\n" + "\n".join(f" - {w}" for w in result.warnings) + "\n\n"

        report_str += "METRICS:\n" + json.dumps(result.metrics, indent=2)
        self.report_text.insert(tk.END, report_str)

        # 3. Render Graph PNG
        try:
            output_png = "current_graph.png"
            visualize(spatial_ir, output_path=output_png, title="Spatial Adjacency Graph")
            
            if PIL_AVAILABLE and os.path.exists(output_png):
                img = Image.open(output_png)
                img.thumbnail((600, 450))
                self.current_img_tk = ImageTk.PhotoImage(img)
                self.img_lbl.config(image=self.current_img_tk, text="")
            else:
                self.img_lbl.config(text=f"Graph saved to: {output_png}", image="")
        except Exception as err:
            self.img_lbl.config(text=f"Could not render graph visualization: {err}", image="")

def main():
    root = tk.Tk()
    app = SpatialIRApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
