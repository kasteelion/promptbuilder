# -*- coding: utf-8 -*-
"""Image cropping dialog for character photos."""

import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    ImageTk = None

from ui.widgets import ScrollableCanvas
from themes import ThemeManager

class ImageCropperDialog:
    """Dialog for cropping and positioning character photos."""

    def __init__(self, parent, image_path, theme_manager=None):
        """Initialize dialog.

        Args:
            parent: Parent window
            image_path: Path to source image
            theme_manager: ThemeManager instance
        """
        if not HAS_PIL:
            return

        self.parent = parent
        self.image_path = image_path
        self.theme_manager = theme_manager
        self.result_image = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Crop Photo")
        self.dialog.geometry("600x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Apply theme
        if self.theme_manager:
            self.theme_manager.theme_toplevel(self.dialog)

        # State
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Load source image
        try:
            self.source_image = Image.open(self.image_path).convert("RGBA")
        except Exception:
            self.dialog.destroy()
            return

        # Target size (for the crop result, high res)
        self.target_size = 512 # save as 512x512

        self._build_ui()
        self._center_image()
        self._update_image()

    def _build_ui(self):
        """Build the UI."""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Instructions
        ttk.Label(
            main_frame, 
            text="Drag to Position • Scroll to Zoom", 
            font=("Lexend", 10, "bold"),
            anchor="center"
        ).pack(fill="x", pady=(0, 10))

        # Canvas container (clipped)
        # We want a square view area to represent the crop
        self.view_size = 400
        
        # Frame with border to show crop area
        canvas_frame = tk.Frame(
            main_frame, 
            width=self.view_size, 
            height=self.view_size, 
            bg="black", 
            highlightthickness=2, 
            highlightbackground="#0078d7" # Accent color placeholder
        )
        canvas_frame.pack()
        canvas_frame.pack_propagate(False) # Strict size

        self.canvas = tk.Canvas(
            canvas_frame, 
            width=self.view_size, 
            height=self.view_size, 
            bg="#333333", 
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_move)
        self.canvas.bind("<MouseWheel>", self._on_zoom) # Windows
        self.canvas.bind("<Button-4>", self._on_zoom)   # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_zoom)   # Linux scroll down

        # Zoom slider
        slider_frame = ttk.Frame(main_frame)
        slider_frame.pack(fill="x", pady=10)
        
        ttk.Label(slider_frame, text="Zoom:").pack(side="left")
        self.zoom_var = tk.DoubleVar(value=1.0)
        self.scale_slider = ttk.Scale(
            slider_frame, 
            from_=0.1, 
            to=5.0, 
            variable=self.zoom_var, 
            command=self._on_slider_change
        )
        self.scale_slider.pack(side="left", fill="x", expand=True, padx=10)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(
            btn_frame, text="Cancel", command=self.dialog.destroy
        ).pack(side="left", expand=True)
        
        ttk.Button(
            btn_frame, text="Save Crop", command=self._save_crop, style="TButton"
        ).pack(side="right", expand=True)

    def _center_image(self):
        """Initial scale to fit cover."""
        # Calculate scale to cover the view_size
        img_w, img_h = self.source_image.size
        scale_w = self.view_size / img_w
        scale_h = self.view_size / img_h
        self.scale = max(scale_w, scale_h)
        self.zoom_var.set(self.scale)
        
        # Center
        self.offset_x = (self.view_size - (img_w * self.scale)) / 2
        self.offset_y = (self.view_size - (img_h * self.scale)) / 2

    def _update_image(self):
        """Redraw image on canvas."""
        # Resample for display
        w = int(self.source_image.width * self.scale)
        h = int(self.source_image.height * self.scale)
        
        if w <= 0 or h <= 0: return

        # Performance: Use Nearest for fast interaction if very large, otherwise Bilinear
        method = Image.Resampling.BILINEAR
        
        resized = self.source_image.resize((w, h), method)
        self.tk_image = ImageTk.PhotoImage(resized)
        
        self.canvas.delete("all")
        self.canvas.create_image(
            self.offset_x, 
            self.offset_y, 
            image=self.tk_image, 
            anchor="nw"
        )

    def _on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.last_offset_x = self.offset_x
        self.last_offset_y = self.offset_y

    def _on_drag_move(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.offset_x = self.last_offset_x + dx
        self.offset_y = self.last_offset_y + dy
        self._update_image()

    def _on_zoom(self, event):
        """Handle scroll zoom."""
        if event.num == 5 or event.delta < 0:
            factor = 0.9
        else:
            factor = 1.1
            
        new_scale = self.scale * factor
        # Clamp
        new_scale = max(0.1, min(new_scale, 10.0))
        
        # Zoom towards center of view (simplified)
        # To zoom towards mouse, we need complex offset calc
        # For now, just center zoom or top-left?
        # Let's do center zoom logic
        
        center_x = self.view_size / 2
        center_y = self.view_size / 2
        
        # Calculate position of center relative to image
        rel_x = (center_x - self.offset_x) / self.scale
        rel_y = (center_y - self.offset_y) / self.scale
        
        self.scale = new_scale
        self.zoom_var.set(self.scale)
        
        # Adjust offset to keep relative position
        self.offset_x = center_x - (rel_x * self.scale)
        self.offset_y = center_y - (rel_y * self.scale)
        
        self._update_image()

    def _on_slider_change(self, val):
        val = float(val)
        if abs(val - self.scale) > 0.01:
            # Center zoom again
            center_x = self.view_size / 2
            center_y = self.view_size / 2
            rel_x = (center_x - self.offset_x) / self.scale
            rel_y = (center_y - self.offset_y) / self.scale
            
            self.scale = val
            self.offset_x = center_x - (rel_x * self.scale)
            self.offset_y = center_y - (rel_y * self.scale)
            
            self._update_image()

    def _save_crop(self):
        """Perform the crop and close."""
        # Calculate source rectangle
        # Viewport is (0, 0, view_size, view_size)
        # Image is at (offset_x, offset_y) with scale
        
        # Inverse projection
        # source_x = (view_x - offset_x) / scale
        
        left = (0 - self.offset_x) / self.scale
        top = (0 - self.offset_y) / self.scale
        right = (self.view_size - self.offset_x) / self.scale
        bottom = (self.view_size - self.offset_y) / self.scale
        
        # Crop
        try:
            cropped = self.source_image.crop((left, top, right, bottom))
            # Resize to standardized target size (512x512) for quality
            self.result_image = cropped.resize((512, 512), Image.Resampling.LANCZOS)
            self.dialog.destroy()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to crop image: {e}")

    def show(self):
        self.parent.wait_window(self.dialog)
        return self.result_image
