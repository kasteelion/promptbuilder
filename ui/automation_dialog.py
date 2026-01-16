"""UI Dialog for AI Automation (Image/Prompt Generation)."""

import tkinter as tk
from tkinter import ttk, messagebox
import queue

from logic.automation_controller import AutomationController

class AutomationDialog:
    """Dialog for configuring and running AI automation."""

    def __init__(self, root: tk.Tk, ctx, theme_manager, fixed_prompt: str = None):
        self.root = tk.Toplevel(root)
        self.root.title("AI AUTOMATION")
        self.root.geometry("600x500")
        self.root.transient(root)
        self.root.grab_set()
        
        self.ctx = ctx
        self.tm = theme_manager
        self.controller = getattr(ctx, "automation_controller", None) or AutomationController(ctx)
        self.fixed_prompt = fixed_prompt
        
        # UI State
        self.count_var = tk.IntVar(value=1 if fixed_prompt else 5)
        self.prob_var = tk.DoubleVar(value=0.3)
        self.mode_var = tk.StringVar(value="browser" if fixed_prompt else "prompts") # "prompts" or "browser"
        self.is_running = False
        
        # Queue for UI updates from background thread
        self.ui_queue = queue.Queue()
        
        if self.tm:
            self.tm.theme_toplevel(self.root)
            
        self._build_ui()
        
        # Register for theme updates
        if hasattr(root, "dialog_manager"):
             root.dialog_manager._register_dialog(self.root, self._apply_theme)
             
        # Start queue polling
        self.root.after(100, self._poll_queue)
        
        if self.tm:
            self._apply_theme(self.tm.themes.get(self.tm.current_theme, {}))

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Settings Section
        self.settings_frame = ttk.LabelFrame(main_frame, text=" CONFIGURATION ", padding=15)
        self.settings_frame.pack(fill="x", pady=(0, 20))
        
        if self.fixed_prompt:
             accent = self.tm.themes.get(self.tm.current_theme, {}).get("accent", "cyan") if self.tm else "cyan"
             ttk.Label(self.settings_frame, text="SINGLE PROMPT MODE ACTIVE", foreground=accent).pack(pady=5)
             # We still show mode selection, but default to browser

        # Count
        row1 = ttk.Frame(self.settings_frame)
        row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="GENERATION COUNT:", width=25).pack(side="left")
        self.count_spin = ttk.Spinbox(row1, from_=1, to=100, textvariable=self.count_var, width=10)
        self.count_spin.pack(side="left")
        
        if self.fixed_prompt:
            self.count_spin.config(state="disabled")

        # Prob
        row2 = ttk.Frame(self.settings_frame)
        row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="OUTFIT MATCH PROB (0-1):", width=25).pack(side="left")
        self.prob_scale = ttk.Scale(row2, from_=0.0, to=1.0, variable=self.prob_var, orient="horizontal")
        self.prob_scale.pack(side="left", fill="x", expand=True, padx=10)
        self.prob_lbl = ttk.Label(row2, textvariable=self.prob_var, width=5)
        self.prob_lbl.pack(side="left")
        
        if self.fixed_prompt:
             self.prob_scale.config(state="disabled")

        # Mode
        row3 = ttk.Frame(self.settings_frame)
        row3.pack(fill="x", pady=10)
        ttk.Label(row3, text="EXECUTION MODE:", width=25).pack(side="left")
        ttk.Radiobutton(row3, text="PROMPTS ONLY (LOCAL)", variable=self.mode_var, value="prompts").pack(side="left", padx=10)
        ttk.Radiobutton(row3, text="BROWSER (AI STUDIO)", variable=self.mode_var, value="browser").pack(side="left")

        # Progress Section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="both", expand=True)

        self.status_label = ttk.Label(progress_frame, text="Ready to start", style="Muted.TLabel")
        self.status_label.pack(anchor="w", pady=(0, 5))

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # Log Area
        log_frame = ttk.Frame(progress_frame, style="TFrame")
        log_frame.pack(fill="both", expand=True)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=8, font=("Lexend", 9), state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)

        # Controls
        ctrl_frame = ttk.Frame(main_frame, padding=(0, 20, 0, 0))
        ctrl_frame.pack(fill="x")

        self.start_btn = ttk.Button(
            ctrl_frame, 
            text="🚀 GENERATE IMAGE" if self.fixed_prompt else "🚀 START GENERATION", 
            command=self._on_start
        )
        self.start_btn.pack(side="right", padx=5)

        self.stop_btn = ttk.Button(ctrl_frame, text="🛑 STOP", command=self._on_stop, state="disabled")
        self.stop_btn.pack(side="right", padx=5)

        ttk.Button(ctrl_frame, text="CLOSE", command=self.root.destroy).pack(side="left")

    def _on_start(self):
        if self.is_running:
            return
        
        count = self.count_var.get()
        prob = self.prob_var.get()
        prompts_only = self.mode_var.get() == "prompts"

        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress_bar["maximum"] = count
        self.progress_bar["value"] = 0
        
        self._log("Starting generation...")
        
        self.controller.start_generation(
            count=count,
            match_outfits_prob=prob,
            prompts_only=prompts_only,
            on_progress=lambda c, t, m: self.ui_queue.put(("progress", c, t, m)),
            on_complete=lambda r: self.ui_queue.put(("complete", r)),
            on_error=lambda e: self.ui_queue.put(("error", e)),
            fixed_prompt=self.fixed_prompt
        )

    def _on_stop(self):
        self._log("Stopping requested...")
        self.controller.stop()
        self.stop_btn.config(state="disabled")

    def _poll_queue(self):
        """Poll the message queue for UI updates."""
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                msg_type = msg[0]
                
                if msg_type == "progress":
                    current, total, text = msg[1:]
                    self.progress_bar["value"] = current
                    self.status_label.config(text=text)
                    self._log(text)
                
                elif msg_type == "complete":
                    results = msg[1]
                    self.is_running = False
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    self.status_label.config(text="Generation complete!")
                    self._log(f"Success! Generated {len(results)} items.")
                    messagebox.showinfo("Automation", "Generation completed successfully!\nCheck output folder for results.")
                
                elif msg_type == "error":
                    err = msg[1]
                    self.is_running = False
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    self.status_label.config(text="Error occurred")
                    self._log(f"ERROR: {str(err)}")
                    messagebox.showerror("Automation Error", str(err))
                    
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_queue)

    def _log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _apply_theme(self, theme):
        if self.tm:
            self.tm.apply_text_widget_theme(self.log_text, theme)

def show_automation_dialog(parent, ctx, theme_manager, fixed_prompt=None):
    return AutomationDialog(parent, ctx, theme_manager, fixed_prompt=fixed_prompt)
