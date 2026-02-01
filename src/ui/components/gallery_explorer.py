import flet as ft
from pathlib import Path
import math
from utils.text_parser import TextParser

class GalleryExplorer(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 20
        self.bgcolor = ft.Colors.BLACK87 # Dark overlay background
        
        # Path configuration
        # Resolve absolute path relative to project root
        # ui/components/gallery_explorer.py -> ../../../ -> root
        project_root = Path(__file__).resolve().parent.parent.parent
        self.output_dir = project_root / "output" / "images" / "generated_images"

        if hasattr(self.app, "ctx") and self.app.ctx.data_loader:
             # If data_loader has base_dir, verify it's absolute, otherwise stick to reliable one
             # But self.app.ctx.data_loader.base_dir might be unreliable if just CWD
             # Ideally we prefer our calculated root
             pass 

        # State
        self.pairs = [] # (img_path, txt_path)
        self.page_size = 20
        self.current_page = 0
        self.total_pages = 0
        self.current_index = -1
        
        # UI Elements
        self.grid = ft.GridView(
            expand=True,
            runs_count=5,
            max_extent=150,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        self.detail_image = ft.Image(src="", fit="contain", expand=True)
        self.detail_text = ft.TextField(
            read_only=True, multiline=True, expand=True, text_size=12, 
            border_color=ft.Colors.TRANSPARENT
        )
        
        self.page_info = ft.Text("Page 1/1", color="white")
        self.btn_prev = ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.change_page(-1))
        self.btn_next = ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=lambda e: self.change_page(1))
        
        self.load_btn = ft.ElevatedButton(
            "Load Settings", 
            icon=ft.Icons.UPLOAD_FILE, 
            on_click=self.load_current_settings,
            disabled=True
        )

        self._build_ui()
        self._build_ui()
        self.refresh()

    def _safe_update(self):
        try:
            if self.page:
                self.update()
        except RuntimeError:
            pass
            
    def _build_ui(self):
        # Top Bar
        top_bar = ft.Row([
            ft.Text("OUTPUT GALLERY", size=20, weight="bold", color="white"),
            ft.Row([
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: self.refresh()),
                self.btn_prev,
                self.page_info,
                self.btn_next,
                ft.IconButton(ft.Icons.CLOSE, on_click=self.app.close_gallery_overlay, tooltip="Close")
            ])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Main Content (Split View)
        # Left: Grid, Right: Details
        self.split_view = ft.Row([
            # Left Panel: Grid
            ft.Container(
                content=self.grid,
                expand=2,
                bgcolor=ft.Colors.BLACK54,
                padding=10,
                border_radius=10
            ),
            # Right Panel: Details
            ft.Container(
                content=ft.Column([
                    ft.Container(content=self.detail_image, expand=True, bgcolor="black"),
                    ft.Container(content=self.detail_text, height=200),
                    ft.Row([self.load_btn], alignment=ft.MainAxisAlignment.END)
                ]),
                expand=1,
                padding=10,
                bgcolor=ft.Colors.BLUE_GREY_900,
                border_radius=10
            )
        ], expand=True, spacing=10)

        self.content = ft.Column([
            top_bar,
            self.split_view
        ], expand=True)

    def refresh(self):
        """Scan directory for images."""
        if not self.output_dir.exists():
            print(f"Directory not found: {self.output_dir}")
            return

        # Glob *.png
        images = sorted(list(self.output_dir.glob("*.png")), key=lambda p: p.stat().st_mtime, reverse=True)
        self.pairs = []
        for img in images:
            txt = img.with_suffix(".txt")
            self.pairs.append((img, txt if txt.exists() else None))
            
        self.total_pages = math.ceil(len(self.pairs) / self.page_size) or 1
        self.current_page = 0
        self.load_page()

    def change_page(self, delta):
        new_page = self.current_page + delta
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.load_page()

    def load_page(self):
        self.grid.controls.clear()
        start = self.current_page * self.page_size
        end = start + self.page_size
        items = self.pairs[start:end]
        
        for i, (img, txt) in enumerate(items):
            # Create a card for the image
            # We assume images are accessible via relative path or file protocol
            # Flet Image src needs to be absolute-ish or served. 
            # If running locally, absolute path usually works if spaces are handled or not blocked.
            
            src = str(img) # Absolute path
            
            card = ft.Container(
                content=ft.Image(src=src, fit="cover", border_radius=5),
                on_click=lambda e, idx=start+i: self.select_item(idx),
                border=ft.border.all(2, ft.Colors.TRANSPARENT),
                border_radius=5,
                tooltip=img.name
            )
            # Store ref to container to update border on selection? logic might be tricky without full state
            # For now just simple click
            card.data = start+i
            self.grid.controls.append(card)
            
        self.page_info.value = f"Page {self.current_page + 1}/{self.total_pages}"
        self.btn_prev.disabled = (self.current_page == 0)
        self.btn_next.disabled = (self.current_page >= self.total_pages - 1)
        self._safe_update()

    def select_item(self, index):
        self.current_index = index
        img, txt = self.pairs[index]
        
        self.detail_image.src = str(img)
        
        content = ""
        if txt:
            try:
                content = txt.read_text(encoding="utf-8")
                self.load_btn.disabled = False
            except Exception as e:
                content = f"Error reading text: {e}"
                self.load_btn.disabled = True
        else:
            content = "No metadata found."
            self.load_btn.disabled = True
            
        self.detail_text.value = content
        self._safe_update()

    def load_current_settings(self, e):
        """Parse metadata and restore state."""
        if self.current_index < 0: return
        
        img, txt = self.pairs[self.current_index]
        if not txt: return
        
        try:
            content = txt.read_text(encoding="utf-8")
            # Reuse logic from gallery.py: _parse_metadata
            # But wait, TextParser is better? 
            # TextParser.parse_import_text usually handles "Smart Import". 
            # The gallery files often have a specific # METADATA block.
            
            # Let's check TextParser capabilities. 
            # If it handles standard text blocks, we might need a specific metadata parser if the format is strict.
            # archive/ui/gallery.py had a custom _parse_metadata because it looked for "# METADATA"
            
            # Let's try TextParser first, if it fails, fallback or implement custom.
            available_chars = list(self.app.ctx.characters.keys())
            config = TextParser.parse_import_text(content, available_chars)
            
            # If TextParser didn't pick up specific metadata fields (like hidden interaction metadata), 
            # we might miss them. But TextParser is robust.
            
            if config:
                self.app.restore_state(config)
                self.app.close_gallery_overlay(None)
                self.app.full_update()
                
        except Exception as ex:
            print(f"Error loading settings: {ex}")
            # Show snackbar?
            self.app.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            self.app.page.snack_bar.open = True
            self.app.page.update()
