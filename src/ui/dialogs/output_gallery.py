import flet as ft
import os
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
            width=900, height=600 # Explicit size for desktop feel
        )
        
        self.content = self.main_content
        self.actions = [
            ft.TextButton("Close", on_click=self.handle_close)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END
        
        # Load Data
        self.load_images()
        
    def load_images(self):
        if not os.path.exists(self.directory):
            self.grid.controls = [ft.Text("Output directory not found.")]
            return

        files = sorted(os.listdir(self.directory), reverse=True) # Newest first
        pngs = [f for f in files if f.lower().endswith('.png')]
        
        self.images = []
        for f in pngs:
            full_path = os.path.join(self.directory, f)
            txt_name = f.rsplit('.', 1)[0] + ".txt"
            txt_path = os.path.join(self.directory, txt_name)
            
            prompt_text = "No prompt data found."
            if os.path.exists(txt_path):
                try:
                    with open(txt_path, 'r', encoding='utf-8') as tf:
                        prompt_text = tf.read().strip()
                except:
                    pass
            
            self.images.append({
                "path": full_path,
                "name": f,
                "prompt": prompt_text
            })
            
        # Build Grid
        self.grid.controls = [
            self.create_thumbnail(img) for img in self.images
        ]
        
    def create_thumbnail(self, img_data):
        return ft.Container(
            content=ft.Image(
                src=img_data["path"],
                fit="cover",
                border_radius=ft.BorderRadius.all(10),
            ),
            data=img_data,
            on_click=self.handle_image_click,
            border=ft.Border.all(2, "transparent"), # Placeholder for selection
            border_radius=10,
            tooltip=img_data["name"],
            ink=True
        )

    def handle_image_click(self, e):
        img_data = e.control.data
        self.show_detail_view(img_data)

    def show_detail_view(self, img_data):
        # Create Detail Layout
        
        # Image Panel
        img_panel = ft.Container(
            content=ft.Image(
                src=img_data["path"],
                fit="contain",
                border_radius=10
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
                    content=ft.Text(img_data["prompt"], size=13, selectable=True, font_family="Consolas"),
                    padding=10,
                    bgcolor=ThemeManager.colors["input_bg"],
                    border_radius=5,
                    expand=True,
                    border=ft.Border.all(1, ThemeManager.colors["outline"])
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "Back to Grid",
                        icon=ft.Icons.GRID_VIEW,
                        on_click=self.handle_back_to_grid
                    ),
                    ft.IconButton(
                        ft.Icons.COPY,
                        tooltip="Copy Prompt",
                        on_click=lambda _: self.app.page.set_clipboard(img_data["prompt"])
                    )
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

    def handle_close(self, e):
        self.app.close_dialog(self)
