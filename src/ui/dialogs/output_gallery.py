import flet as ft
import os
import base64
from core.flet_theme_manager import ThemeManager


class OutputGalleryDialog(ft.AlertDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title = ft.Text("Output Gallery", weight="bold")
        self.directory = os.path.join(os.getcwd(), "output", "images", "generated_images")
        
        # State
        self.images = []   # List of dicts: {path, name, timestamp, prompt_path}
        self.selected_img = None
        self.current_index = -1
        self.page_size = 48
        self.all_files = [] # Cache for all file names
        self.loaded_count = 0
        
        # UI Components
        self.grid = ft.GridView(
            expand=True,
            runs_count=4,
            max_extent=200,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        self.detail_view = ft.Container(visible=False, expand=True)
        self.main_content = ft.Container(
            content=self.grid, 
            expand=True,
            width=900, height=600
        )
        
        self.content = self.main_content
        self.actions = [
            ft.TextButton("Open Folder", on_click=self.handle_open_folder, icon=ft.Icons.FOLDER_OPEN),
            ft.TextButton("Refresh", on_click=self.handle_refresh, icon=ft.Icons.REFRESH),
            ft.TextButton("Close", on_click=self.handle_close),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END
        
        # Load Initial Data
        self.load_initial_data()
        
    # ---
    # We leave __init__ unmodified and patch the inner methods to be async/threaded where possible,
    # but the simplest fix for "incredibly slow" is just reducing page size and avoiding main-thread b64 processing.
    # Actually, we can just replace load_initial_data and load_images logic.

    def load_initial_data(self):
        if not os.path.exists(self.directory):
            self.grid.controls = [ft.Text("Output directory not found.")]
            return
            
        files = sorted(os.listdir(self.directory), reverse=True) # Newest first
        self.all_files = [f for f in files if f.lower().endswith('.png')]
        
        # Override page size for performance
        self.page_size = 12 
        
        # Defer loading to not block the dialog open animation
        import threading
        threading.Timer(0.1, self._load_images_bg, args=[False]).start()

    def _load_images_bg(self, append=False):
        self.load_images(append=append)

    def load_images(self, append=False):
        if not self.all_files:
            if not append:
                self.grid.controls = [ft.Text("No images found. Run Automation to generate some!", italic=True, color="grey")]
                self._safe_update()
            return

        start = self.loaded_count if append else 0
        end = start + self.page_size
        batch = self.all_files[start:end]
        
        if not batch and append:
            self.app.show_toast("No more images to load.", color="orange")
            return

        if not append:
            self.images = []
            self.loaded_count = 0
            self.grid.controls = []

        for f in batch:
            full_path = os.path.join(self.directory, f)
            txt_name = f.rsplit('.', 1)[0] + ".txt"
            txt_path = os.path.join(self.directory, txt_name)
            
            prompt_text = "No prompt data found."
            if os.path.exists(txt_path):
                try:
                    with open(txt_path, 'r', encoding='utf-8') as tf:
                        prompt_text = tf.read().strip()
                except Exception:
                    pass
            
            img_dict = {
                "path": full_path,
                "name": f,
                "prompt": prompt_text,
                "base64": None # Lazy load
            }
            
            self.images.append(img_dict)
            self.grid.controls.append(self.create_thumbnail(img_dict))
            self.loaded_count += 1
            
        # Add "Load More" if there are more
        if self.loaded_count < len(self.all_files):
            # Clean up any lingering load_more buttons before appending a fresh one
            self.grid.controls = [c for c in self.grid.controls if getattr(c, "data", None) != "load_more"]
                
            load_more_btn = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=30, color=ThemeManager.colors.get("accent", "blue")),
                    ft.Text("Load More", size=12, weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ThemeManager.colors["input_bg"],
                border_radius=10,
                on_click=lambda _: self._load_images_bg(append=True),
                alignment=ft.Alignment(0, 0),
                data="load_more", # Use data instead of custom attr for safety
                ink=True,
                height=200, width=200
            )
            self.grid.controls.append(load_more_btn)
            
        self._safe_update()
            
    def _safe_update(self):
        try:
            if self.page:
                self.update()
        except Exception:
            pass

    def get_base64(self, img_data):
        """Lazy load base64 for web mode."""
        if not getattr(self.app, 'is_web', False):
            return None
        if img_data.get("base64"):
            return img_data["base64"]
            
        try:
            with open(img_data["path"], "rb") as image_file:
                # In Web Mode, base64 payload size for large images kills WS. 
                # Flet doesn't support easy resizing without PIL. We just load it for now since page_size is small.
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                img_data["base64"] = encoded_string
                return encoded_string
        except Exception:
            return None

    def create_thumbnail(self, img_data):
        # 1x1 transparent pixel in base64
        blank_pixel = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        
        # If web, we load base64
        if getattr(self.app, 'is_web', False):
            img_b64 = self.get_base64(img_data)
            b64_str = img_b64 if img_b64 else blank_pixel
            img_control = ft.Image(
                src=f"data:image/png;base64,{b64_str}",
                fit="cover",
                border_radius=ft.BorderRadius.all(10),
            )
        else:
            img_control = ft.Image(
                src=img_data["path"],
                fit="cover",
                border_radius=ft.BorderRadius.all(10),
            )

        return ft.Container(
            content=img_control,
            data=img_data,
            on_click=self.handle_image_click,
            border=ft.Border.all(2, "transparent"),
            border_radius=10,
            tooltip=img_data["name"],
            ink=True
        )

    def handle_image_click(self, e):
        img_data = e.control.data
        # Find index
        for i, img in enumerate(self.images):
            if img["path"] == img_data["path"]:
                self.current_index = i
                break
        self.show_detail_view(img_data)

    def handle_next(self, e):
        if not self.images: return
        self.current_index = (self.current_index + 1) % len(self.images)
        self.show_detail_view(self.images[self.current_index])

    def handle_prev(self, e):
        if not self.images: return
        self.current_index = (self.current_index - 1) % len(self.images)
        self.show_detail_view(self.images[self.current_index])

    def handle_copy_prompt(self, prompt):
        from __main__ import PlatformUtils
        if PlatformUtils.copy_to_clipboard(self.app.page, prompt, is_web=getattr(self.app, 'is_web', False)):
            self.app.show_toast("Prompt copied to clipboard!", color="green")
        else:
            self.app.show_toast("Failed to copy to clipboard", color="red")

    def show_detail_view(self, img_data):
        self.selected_img = img_data
        
        img_src = img_data["path"]
        if getattr(self.app, 'is_web', False):
            img_src = f"data:image/png;base64,{self.get_base64(img_data)}"
            
        # Image Panel
        img_panel = ft.Container(
            content=ft.Image(
                src=img_src,
                fit="contain",
                border_radius=10,
            ),
            expand=2,
            bgcolor=ft.Colors.BLACK54,
            border_radius=10,
            padding=5,
            alignment=ft.Alignment(0, 0)
        )
        
        # Info Panel
        info_panel = ft.Container(
            content=ft.Column([
                ft.Text(img_data["name"], weight="bold", size=16),
                ft.Divider(),
                ft.Text("PROMPT:", size=12, weight="bold", color="grey"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(img_data["prompt"], size=13, selectable=True, font_family="Consolas"),
                    ], scroll=ft.ScrollMode.ALWAYS, expand=True),
                    padding=10,
                    bgcolor=ThemeManager.colors["input_bg"],
                    border_radius=5,
                    expand=True,
                    border=ft.Border.all(1, ThemeManager.colors["outline"])
                ),
                ft.Row([
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, on_click=self.handle_prev, tooltip="Previous Image"),
                        ft.Text(f"{self.current_index + 1} / {len(self.images)}", size=12, weight="bold"),
                        ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, on_click=self.handle_next, tooltip="Next Image"),
                    ], spacing=10),
                    ft.FilledButton(
                        "Back to Grid",
                        icon=ft.Icons.GRID_VIEW,
                        on_click=self.handle_back_to_grid
                    ),
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.COPY,
                            tooltip="Copy Prompt",
                            on_click=lambda _: self.handle_copy_prompt(img_data["prompt"])
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            tooltip="Delete Image",
                            icon_color="red",
                            on_click=lambda _: self.handle_delete(img_data)
                        )
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=10, expand=True),
            expand=1,
            padding=10
        )
        
        detail_layout = ft.Row([img_panel, info_panel], expand=True, spacing=20)
        
        self.content = ft.Container(
            content=detail_layout,
            width=1000, height=700 
        )
        self.update()

    def handle_back_to_grid(self, e):
        self.content = self.main_content
        self.update()

    def handle_refresh(self, e):
        self.load_initial_data()
        self.content = self.main_content
        self.update()

    def handle_open_folder(self, e):
        if getattr(self.app, 'is_web', False):
            self.app.show_toast("File browsing is only available in desktop mode.", color="orange")
            return
        if os.path.exists(self.directory):
            from __main__ import PlatformUtils
            PlatformUtils.open_path(self.directory)
        else:
            self.app.show_toast("Output directory not found.", color="orange")

    def handle_delete(self, img_data):
        try:
            # Delete image file
            if os.path.exists(img_data["path"]):
                os.remove(img_data["path"])
            
            # Delete associated prompt file
            txt_path = img_data["path"].rsplit('.', 1)[0] + ".txt"
            if os.path.exists(txt_path):
                os.remove(txt_path)
            
            self.app.show_toast(f"Deleted {img_data['name']}")
            
            # Refresh and go back to grid
            self.load_images()
            self.content = self.main_content
            self.update()
        except Exception as err:
            self.app.show_toast(f"Delete failed: {err}", color="red")

    def handle_close(self, e):
        self.app.close_dialog(self)
