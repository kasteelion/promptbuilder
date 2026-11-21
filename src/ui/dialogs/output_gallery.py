import flet as ft
import os
import base64
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.flet_theme_manager import ThemeManager


class OutputGalleryDialog(ft.AlertDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        
        # Absolute project root resolution
        self.project_root = Path(__file__).resolve().parents[3]
        self.images_dir = str(self.project_root / "output" / "images" / "generated_images")
        self.prompts_dir = str(self.project_root / "output" / "prompts")
        
        # Fallback creation if directories missing
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.prompts_dir, exist_ok=True)
        
        # State
        self.current_mode = "images"  # "images" or "prompts"
        self.directory = self.images_dir
        self.items = []          # List of item dicts
        self.all_file_paths = [] # Paths of all discovered files in active directory
        self.selected_item = None
        self.current_index = -1
        self.page_size = 12
        self.loaded_count = 0
        self._thumb_cache: Dict[str, str] = {}
        
        # Counts for tabs
        self.images_count = 0
        self.prompts_count = 0
        
        # UI Components
        self.grid = ft.GridView(
            expand=True,
            runs_count=4,
            max_extent=220,
            child_aspect_ratio=1.0,
            spacing=12,
            run_spacing=12,
        )
        
        self.main_content = ft.Container(
            content=self.grid,
            expand=True,
            width=960,
            height=620
        )
        
        self.content = self.main_content
        
        # Mode selector buttons
        self.mode_images_btn = ft.FilledButton(
            "Images (0)",
            icon=ft.Icons.IMAGE,
            on_click=lambda _: self.switch_mode("images"),
            style=ft.ButtonStyle(
                color=ThemeManager.colors.get("header_fg", "#ffffff"),
                bgcolor=ThemeManager.colors.get("accent", "#3b82f6"),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6)
            )
        )
        self.mode_prompts_btn = ft.OutlinedButton(
            "Prompts (0)",
            icon=ft.Icons.TEXT_SNIPPET,
            on_click=lambda _: self.switch_mode("prompts"),
            style=ft.ButtonStyle(
                color=ThemeManager.colors.get("text_primary", "#ffffff"),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6)
            )
        )
        
        self.title = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.PHOTO_LIBRARY_ROUNDED, color=ThemeManager.colors.get("accent", "#3b82f6"), size=24),
                ft.Text("Output Gallery", weight=ft.FontWeight.BOLD, size=18),
            ], spacing=8),
            ft.Row([
                self.mode_images_btn,
                self.mode_prompts_btn,
            ], spacing=6),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.actions = [
            ft.TextButton("Open Folder", on_click=self.handle_open_folder, icon=ft.Icons.FOLDER_OPEN),
            ft.TextButton("Refresh", on_click=self.handle_refresh, icon=ft.Icons.REFRESH),
            ft.TextButton("Close", on_click=self.handle_close),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END
        
        # Load Initial Data
        self.load_initial_data()

    def _safe_update(self):
        try:
            if self.page:
                self.update()
        except Exception:
            pass

    def switch_mode(self, mode: str):
        if self.current_mode == mode:
            return
        self.current_mode = mode
        self.directory = self.images_dir if mode == "images" else self.prompts_dir
        
        # Update button styles
        accent_color = ThemeManager.colors.get("accent", "#3b82f6")
        text_primary = ThemeManager.colors.get("text_primary", "#ffffff")
        
        if mode == "images":
            self.mode_images_btn.style.bgcolor = accent_color
            self.mode_images_btn.style.color = text_primary
            self.mode_prompts_btn.style.bgcolor = None
            self.mode_prompts_btn.style.color = ThemeManager.colors.get("text_secondary", "#94a3b8")
        else:
            self.mode_prompts_btn.style.bgcolor = accent_color
            self.mode_prompts_btn.style.color = text_primary
            self.mode_images_btn.style.bgcolor = None
            self.mode_images_btn.style.color = ThemeManager.colors.get("text_secondary", "#94a3b8")
            
        self.content = self.main_content
        self.load_initial_data()

    def _update_tab_counts(self):
        try:
            img_exts = ('.png', '.jpg', '.jpeg', '.webp')
            if os.path.exists(self.images_dir):
                self.images_count = sum(1 for f in os.listdir(self.images_dir) if f.lower().endswith(img_exts))
            else:
                self.images_count = 0
                
            if os.path.exists(self.prompts_dir):
                self.prompts_count = sum(1 for f in os.listdir(self.prompts_dir) if f.lower().endswith('.txt'))
            else:
                self.prompts_count = 0
                
            if hasattr(self.mode_images_btn, "content"):
                self.mode_images_btn.content = f"Images ({self.images_count})"
            elif hasattr(self.mode_images_btn, "text"):
                self.mode_images_btn.text = f"Images ({self.images_count})"
                
            if hasattr(self.mode_prompts_btn, "content"):
                self.mode_prompts_btn.content = f"Prompts ({self.prompts_count})"
            elif hasattr(self.mode_prompts_btn, "text"):
                self.mode_prompts_btn.text = f"Prompts ({self.prompts_count})"
        except Exception:
            pass

    def load_initial_data(self):
        self._update_tab_counts()
        
        if not os.path.exists(self.directory):
            self.grid.controls = [ft.Text("Output directory not found.", color=ThemeManager.colors.get("error", "red"))]
            self._safe_update()
            return
            
        try:
            if self.current_mode == "images":
                exts = ('.png', '.jpg', '.jpeg', '.webp')
                all_files = [
                    os.path.join(self.directory, f)
                    for f in os.listdir(self.directory)
                    if f.lower().endswith(exts)
                ]
            else:
                all_files = [
                    os.path.join(self.directory, f)
                    for f in os.listdir(self.directory)
                    if f.lower().endswith('.txt')
                ]
                
            # Sort newest first by modified timestamp
            all_files.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
            self.all_file_paths = all_files
        except Exception as e:
            self.grid.controls = [ft.Text(f"Failed to scan directory: {e}", color="red")]
            self._safe_update()
            return
            
        self.load_items(append=False)

    def load_items(self, append=False):
        if not self.all_file_paths:
            if not append:
                msg = "No generated images found." if self.current_mode == "images" else "No saved prompt runs found."
                self.grid.controls = [
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(
                                ft.Icons.PHOTO_ALBUM_OUTLINED if self.current_mode == "images" else ft.Icons.DESCRIPTION_OUTLINED,
                                size=48, color=ThemeManager.colors.get("text_secondary", "grey")
                            ),
                            ft.Text(f"{msg}\nRun Automation to generate assets!", italic=True, text_align=ft.TextAlign.CENTER, color=ThemeManager.colors.get("text_secondary", "grey")),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                        padding=40
                    )
                ]
                self._safe_update()
            return

        start = self.loaded_count if append else 0
        end = start + self.page_size
        batch = self.all_file_paths[start:end]
        
        if not batch and append:
            self.app.show_toast("All items loaded.", color="orange")
            return

        if not append:
            self.items = []
            self.loaded_count = 0
            self.grid.controls = []

        for full_path in batch:
            filename = os.path.basename(full_path)
            mtime = os.path.getmtime(full_path) if os.path.exists(full_path) else 0
            formatted_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
            
            if self.current_mode == "images":
                txt_name = filename.rsplit('.', 1)[0] + ".txt"
                txt_path = os.path.join(self.directory, txt_name)
                
                prompt_text = ""
                if os.path.exists(txt_path):
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as tf:
                            prompt_text = tf.read().strip()
                    except Exception:
                        prompt_text = ""
                        
                meta = self.parse_prompt_metadata(prompt_text)
                
                item_dict = {
                    "mode": "images",
                    "path": full_path,
                    "name": filename,
                    "prompt_path": txt_path if os.path.exists(txt_path) else None,
                    "prompt": prompt_text,
                    "metadata": meta,
                    "mtime": mtime,
                    "time_str": formatted_time,
                }
                self.items.append(item_dict)
                self.grid.controls.append(self.create_image_card(item_dict))
            else:
                prompt_text = ""
                try:
                    with open(full_path, 'r', encoding='utf-8') as tf:
                        prompt_text = tf.read().strip()
                except Exception:
                    prompt_text = ""
                    
                meta = self.parse_prompt_metadata(prompt_text)
                item_dict = {
                    "mode": "prompts",
                    "path": full_path,
                    "name": filename,
                    "prompt": prompt_text,
                    "metadata": meta,
                    "mtime": mtime,
                    "time_str": formatted_time,
                }
                self.items.append(item_dict)
                self.grid.controls.append(self.create_prompt_card(item_dict))
                
            self.loaded_count += 1
            
        # Clean up any existing load_more buttons before appending fresh one
        self.grid.controls = [c for c in self.grid.controls if getattr(c, "data", None) != "load_more"]
        
        # Add "Load More" button if more items remain
        if self.loaded_count < len(self.all_file_paths):
            load_more_btn = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=32, color=ThemeManager.colors.get("accent", "#3b82f6")),
                    ft.Text(f"Load More ({self.loaded_count}/{len(self.all_file_paths)})", size=12, weight=ft.FontWeight.BOLD, color=ThemeManager.colors.get("text_primary", "#ffffff"))
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ThemeManager.colors.get("surface_variant", ThemeManager.colors.get("panel_bg", "#1e293b")),
                border_radius=10,
                border=ft.Border.all(1, ThemeManager.colors.get("outline", "#334155")),
                on_click=lambda _: self.load_items(append=True),
                alignment=ft.Alignment(0, 0),
                data="load_more",
                ink=True,
                height=200, width=200
            )
            self.grid.controls.append(load_more_btn)
            
        self._safe_update()

    def _get_thumbnail_base64(self, file_path: str, max_dim: int = 240) -> str:
        """Fast, compressed thumbnail generator for web mode WebSocket safety."""
        if not getattr(self.app, 'is_web', False):
            return ""
            
        mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
        cache_key = f"{file_path}_{mtime}_{max_dim}"
        if cache_key in self._thumb_cache:
            return self._thumb_cache[cache_key]
            
        try:
            from PIL import Image
            import io
            with Image.open(file_path) as img:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                if img.mode in ("RGBA", "P"):
                    img.save(buf, format="PNG", optimize=True)
                else:
                    img.save(buf, format="JPEG", quality=80)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                self._thumb_cache[cache_key] = b64
                return b64
        except Exception:
            try:
                with open(file_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    self._thumb_cache[cache_key] = b64
                    return b64
            except Exception:
                return ""

    def _get_display_image_src(self, file_path: str, max_dim: int = 1200) -> str:
        """Returns src formatted for either web (base64) or desktop (file path)."""
        if not getattr(self.app, 'is_web', False):
            return file_path
            
        # Web Mode: resized base64 to avoid huge WS frames
        mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
        cache_key = f"{file_path}_{mtime}_full_{max_dim}"
        if cache_key in self._thumb_cache:
            return f"data:image/png;base64,{self._thumb_cache[cache_key]}"
            
        try:
            from PIL import Image
            import io
            with Image.open(file_path) as img:
                # Resize if excessively large (e.g. > 1400px)
                if img.width > max_dim or img.height > max_dim:
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                if img.mode in ("RGBA", "P"):
                    img.save(buf, format="PNG", optimize=True)
                else:
                    img.save(buf, format="JPEG", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                self._thumb_cache[cache_key] = b64
                return f"data:image/png;base64,{b64}"
        except Exception:
            try:
                with open(file_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    self._thumb_cache[cache_key] = b64
                    return f"data:image/png;base64,{b64}"
            except Exception:
                return ""

    def create_image_card(self, item: dict):
        blank_pixel = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        if getattr(self.app, 'is_web', False):
            b64_str = self._get_thumbnail_base64(item["path"], max_dim=240) or blank_pixel
            img_src = f"data:image/png;base64,{b64_str}"
        else:
            img_src = item["path"]
            
        img_control = ft.Image(
            src=img_src,
            fit="cover",
            border_radius=ft.BorderRadius.all(8),
            expand=True
        )
        
        score = item["metadata"].get("score")
        score_badge = ft.Container(
            content=ft.Text(f"★ {score}", size=10, weight=ft.FontWeight.BOLD, color="white"),
            bgcolor=ft.Colors.with_opacity(0.85, "#10b981" if score and score >= 200 else "#f59e0b"),
            padding=ft.Padding.symmetric(horizontal=5, vertical=2),
            border_radius=4,
            top=6, right=6,
            visible=bool(score is not None)
        )

        return ft.Container(
            content=ft.Stack([
                img_control,
                score_badge,
                ft.Container(
                    content=ft.Text(item["time_str"], size=9, color="white70"),
                    bgcolor=ft.Colors.BLACK_54,
                    padding=ft.Padding.symmetric(horizontal=4, vertical=2),
                    border_radius=4,
                    bottom=4, left=4
                )
            ]),
            data=item,
            on_click=self.handle_item_click,
            border=ft.Border.all(1, ThemeManager.colors.get("outline", "#334155")),
            border_radius=10,
            tooltip=f"{item['name']}\n{item['time_str']}",
            ink=True
        )

    def create_prompt_card(self, item: dict):
        preview_text = item["prompt"][:140].replace("\n", " ").strip()
        if len(item["prompt"]) > 140:
            preview_text += "..."
            
        score = item["metadata"].get("score")
        base_style = item["metadata"].get("base_prompt") or "Default"
        
        chars = [c.get("name", "") for c in item["metadata"].get("selected_characters", [])]
        chars_str = ", ".join(chars[:2]) if chars else "None"
        if len(chars) > 2:
            chars_str += f" +{len(chars)-2}"
            
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.DESCRIPTION, size=16, color=ThemeManager.colors.get("accent", "#3b82f6")),
                        ft.Text(item["name"][:18] + (".." if len(item["name"]) > 18 else ""), size=11, weight=ft.FontWeight.BOLD),
                    ], spacing=4),
                    ft.Container(
                        content=ft.Text(f"★ {score}", size=9, weight=ft.FontWeight.BOLD, color="white"),
                        bgcolor=ft.Colors.with_opacity(0.85, "#10b981" if score and score >= 200 else "#f59e0b"),
                        padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                        border_radius=4,
                        visible=bool(score is not None)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(preview_text, size=11, max_lines=4, overflow=ft.TextOverflow.ELLIPSIS, color=ThemeManager.colors.get("text_secondary", "grey")),
                ft.Row([
                    ft.Text(f"Style: {base_style}", size=9, color=ThemeManager.colors.get("accent", "#3b82f6"), weight=ft.FontWeight.W_600),
                    ft.Text(item["time_str"], size=9, color=ThemeManager.colors.get("text_secondary", "grey")),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            bgcolor=ThemeManager.colors.get("surface_variant", ThemeManager.colors.get("panel_bg", "#1e293b")),
            border=ft.Border.all(1, ThemeManager.colors.get("outline", "#334155")),
            border_radius=10,
            data=item,
            on_click=self.handle_item_click,
            tooltip=f"{item['name']}\n{item['time_str']}",
            ink=True
        )

    def handle_item_click(self, e):
        item_data = e.control.data
        for i, item in enumerate(self.items):
            if item["path"] == item_data["path"]:
                self.current_index = i
                break
        self.show_detail_view(item_data)

    def handle_next(self, e):
        if not self.items:
            return
        self.current_index = (self.current_index + 1) % len(self.items)
        self.show_detail_view(self.items[self.current_index])

    def handle_prev(self, e):
        if not self.items:
            return
        self.current_index = (self.current_index - 1) % len(self.items)
        self.show_detail_view(self.items[self.current_index])

    def handle_copy_prompt(self, prompt: str):
        if not prompt:
            self.app.show_toast("No prompt to copy.", color="orange")
            return
        try:
            from __main__ import PlatformUtils
            if PlatformUtils.copy_to_clipboard(self.app.page, prompt, is_web=getattr(self.app, 'is_web', False)):
                self.app.show_toast("Prompt copied to clipboard!", color="green")
            else:
                self.app.show_toast("Failed to copy prompt to clipboard.", color="red")
        except Exception as e:
            self.app.show_toast(f"Copy error: {e}", color="red")

    def handle_load_settings(self, prompt_text: str):
        """Restores prompt configurations and metadata directly into the workspace app state."""
        if not prompt_text:
            self.app.show_toast("No prompt configuration found to restore.", color="orange")
            return
            
        try:
            meta = self.parse_prompt_metadata(prompt_text)
            
            # If metadata didn't find characters, fallback to TextParser
            if not meta.get("selected_characters"):
                from utils.text_parser import TextParser
                available_chars = list(self.app.ctx.characters_metadata.keys()) if hasattr(self.app, "ctx") else []
                parsed = TextParser.parse_import_text(prompt_text, available_chars)
                if parsed.get("selected_characters"):
                    meta["selected_characters"] = parsed["selected_characters"]
                if not meta.get("base_prompt") and parsed.get("base_prompt"):
                    meta["base_prompt"] = parsed["base_prompt"]
                if not meta.get("scene") and parsed.get("scene"):
                    meta["scene"] = parsed["scene"]

            applied_count = 0
            
            # 1. Base Prompt / Style
            if meta.get("base_prompt") and hasattr(self.app, "state"):
                self.app.state.state["base_prompt"] = meta["base_prompt"]
                applied_count += 1
                
            # 2. Scene
            if meta.get("scene") and hasattr(self.app, "state"):
                self.app.state.state["scene"] = meta["scene"]
                applied_count += 1
                
            # 3. Notes / Interaction
            if meta.get("interaction") and hasattr(self.app, "state"):
                self.app.state.state["notes"] = meta["interaction"]

            # 4. Characters
            if meta.get("selected_characters") and hasattr(self.app, "state"):
                self.app.state.state["selected_characters"] = []
                for char_conf in meta["selected_characters"]:
                    name = char_conf.get("name")
                    if not name:
                        continue
                    if hasattr(self.app.state, "ensure_character_loaded"):
                        self.app.state.ensure_character_loaded(name)
                        
                    if hasattr(self.app, "char_controller"):
                        self.app.char_controller.add_character(name)
                    elif hasattr(self.app, "add_character"):
                        self.app.add_character(name)

                    if self.app.state.state.get("selected_characters"):
                        new_char = self.app.state.state["selected_characters"][-1]
                        
                        def _set(obj, k, v):
                            if hasattr(obj, k):
                                setattr(obj, k, v)
                            elif isinstance(obj, dict):
                                obj[k] = v
                                
                        if char_conf.get("outfit"):
                            _set(new_char, "outfit", char_conf["outfit"])
                        if char_conf.get("color_scheme"):
                            _set(new_char, "color_scheme", char_conf["color_scheme"])
                        if char_conf.get("pose_preset"):
                            _set(new_char, "pose_preset", char_conf["pose_preset"])
                applied_count += 1

            # Refresh application UI sections
            if hasattr(self.app, "sidebar") and hasattr(self.app.sidebar, "populate_data"):
                self.app.sidebar.populate_data()
            if hasattr(self.app, "refresh_roster"):
                self.app.refresh_roster()
            if hasattr(self.app, "update_preview"):
                self.app.update_preview()
            if hasattr(self.app, "gallery") and hasattr(self.app.gallery, "refresh"):
                self.app.gallery.refresh()

            self.app.show_toast("Gallery configuration loaded into workspace!", color="green")
            self.handle_close(None)
            
        except Exception as err:
            self.app.show_toast(f"Failed to load settings: {err}", color="red")

    def show_detail_view(self, item_data: dict):
        self.selected_item = item_data
        
        # Left Panel (Image or Prompt Text Reader)
        if item_data["mode"] == "images":
            img_src = self._get_display_image_src(item_data["path"], max_dim=1200)
            left_view = ft.Container(
                content=ft.Image(
                    src=img_src,
                    fit="contain",
                    border_radius=10,
                ),
                expand=2,
                bgcolor=ft.Colors.BLACK_54,
                border_radius=10,
                padding=6,
                alignment=ft.Alignment(0, 0)
            )
        else:
            left_view = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.TEXT_SNIPPET, color=ThemeManager.colors.get("accent", "#3b82f6")),
                        ft.Text("PROMPT TEXT CONTENT", size=12, weight=ft.FontWeight.BOLD, color="grey"),
                    ], spacing=6),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(item_data["prompt"] or "Empty prompt file.", size=13, selectable=True, font_family="Consolas"),
                        ], scroll=ft.ScrollMode.ALWAYS, expand=True),
                        bgcolor=ThemeManager.colors.get("surface_variant", ThemeManager.colors.get("panel_bg", "#1e293b")),
                        border=ft.Border.all(1, ThemeManager.colors.get("outline", "#334155")),
                        border_radius=8,
                        padding=12,
                        expand=True
                    )
                ], expand=True, spacing=10),
                expand=2,
                padding=6
            )
            
        # Metadata Badges
        meta = item_data["metadata"]
        meta_chips = []
        if meta.get("score") is not None:
            meta_chips.append(
                ft.Container(
                    content=ft.Text(f"Score: {meta['score']}", size=11, weight=ft.FontWeight.BOLD, color="white"),
                    bgcolor=ft.Colors.with_opacity(0.85, "#10b981" if meta['score'] >= 200 else "#f59e0b"),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=6
                )
            )
        if meta.get("base_prompt"):
            meta_chips.append(
                ft.Container(
                    content=ft.Text(f"Style: {meta['base_prompt']}", size=11, color="white"),
                    bgcolor=ThemeManager.colors.get("accent", "#3b82f6"),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=6
                )
            )
        if meta.get("scene"):
            meta_chips.append(
                ft.Container(
                    content=ft.Text(f"Scene: {meta['scene'][:24]}", size=11, color=ThemeManager.colors.get("text_primary", "white")),
                    bgcolor=ThemeManager.colors.get("surface_variant", "#334155"),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=6
                )
            )
            
        chars = meta.get("selected_characters", [])
        if chars:
            char_names = ", ".join([c.get("name", "") for c in chars if c.get("name")])
            meta_chips.append(
                ft.Container(
                    content=ft.Text(f"Characters: {char_names}", size=11, color=ThemeManager.colors.get("text_primary", "white")),
                    bgcolor=ThemeManager.colors.get("surface_variant", "#334155"),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=6
                )
            )

        # Right Inspector Panel
        info_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(item_data["name"], weight=ft.FontWeight.BOLD, size=15),
                        ft.Text(f"Saved: {item_data['time_str']}", size=11, color=ThemeManager.colors.get("text_secondary", "grey")),
                    ], spacing=2, expand=True),
                ]),
                ft.Row(meta_chips, wrap=True, spacing=6) if meta_chips else ft.Container(),
                ft.Divider(height=10),
                ft.Text("PROMPT / METADATA:", size=11, weight=ft.FontWeight.BOLD, color="grey"),
                ft.Container(
                    content=ft.Column([
                        ft.Text(item_data["prompt"] or "No prompt data found for this asset.", size=12, selectable=True, font_family="Consolas"),
                    ], scroll=ft.ScrollMode.ALWAYS, expand=True),
                    padding=10,
                    bgcolor=ThemeManager.colors.get("surface_variant", ThemeManager.colors.get("panel_bg", "#1e293b")),
                    border_radius=6,
                    expand=True,
                    border=ft.Border.all(1, ThemeManager.colors.get("outline", "#334155"))
                ),
                ft.Row([
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, on_click=self.handle_prev, tooltip="Previous Item"),
                        ft.Text(f"{self.current_index + 1} / {len(self.items)}", size=12, weight=ft.FontWeight.BOLD),
                        ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, on_click=self.handle_next, tooltip="Next Item"),
                    ], spacing=6),
                    ft.FilledButton(
                        "Load Settings",
                        icon=ft.Icons.RESTORE,
                        tooltip="Restore character and scene configuration into workspace",
                        on_click=lambda _: self.handle_load_settings(item_data["prompt"]),
                        style=ft.ButtonStyle(
                            bgcolor=ThemeManager.colors.get("accent", "#3b82f6"),
                            color=ThemeManager.colors.get("header_fg", "#ffffff")
                        )
                    ),
                    ft.OutlinedButton(
                        "Back",
                        icon=ft.Icons.GRID_VIEW,
                        on_click=self.handle_back_to_grid
                    ),
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.COPY,
                            tooltip="Copy Prompt",
                            on_click=lambda _: self.handle_copy_prompt(item_data["prompt"])
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            tooltip="Delete Item",
                            icon_color="red",
                            on_click=lambda _: self.handle_delete(item_data)
                        )
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=8, expand=True),
            expand=1,
            padding=10
        )
        
        detail_layout = ft.Row([left_view, info_panel], expand=True, spacing=16)
        
        self.content = ft.Container(
            content=detail_layout,
            width=1000,
            height=660
        )
        self._safe_update()

    def handle_back_to_grid(self, e):
        self.content = self.main_content
        self._safe_update()

    def handle_refresh(self, e):
        self.load_initial_data()
        self.content = self.main_content
        self._safe_update()

    def handle_open_folder(self, e):
        if getattr(self.app, 'is_web', False):
            # Web mode: copy path to clipboard
            try:
                from __main__ import PlatformUtils
                PlatformUtils.copy_to_clipboard(self.app.page, self.directory, is_web=True)
                self.app.show_toast(f"Directory path copied: {self.directory}")
            except Exception:
                self.app.show_toast("File browsing is only available in desktop mode.", color="orange")
            return
            
        if os.path.exists(self.directory):
            from __main__ import PlatformUtils
            PlatformUtils.open_path(self.directory)
        else:
            self.app.show_toast(f"Directory not found: {self.directory}", color="orange")

    def handle_delete(self, item_data: dict):
        try:
            # Delete primary file
            if os.path.exists(item_data["path"]):
                os.remove(item_data["path"])
            
            # Delete prompt file if it was an image
            if item_data.get("prompt_path") and os.path.exists(item_data["prompt_path"]):
                os.remove(item_data["prompt_path"])
            
            self.app.show_toast(f"Deleted {item_data['name']}")
            
            # Refresh items and return to grid
            self.load_initial_data()
            self.content = self.main_content
            self._safe_update()
        except Exception as err:
            self.app.show_toast(f"Delete failed: {err}", color="red")

    def handle_close(self, e):
        self.app.close_dialog(self)

    @staticmethod
    def parse_prompt_metadata(text: str) -> Dict[str, Any]:
        """Extract structured metadata from # METADATA blocks or inline prompt text."""
        config: Dict[str, Any] = {
            "base_prompt": "",
            "scene": "",
            "interaction": "",
            "score": None,
            "selected_characters": []
        }
        if not text:
            return config
            
        if "# METADATA" in text:
            meta_part = text.split("# METADATA", 1)[1]
            for line in meta_part.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("Base_Prompt:"):
                    config["base_prompt"] = line.split(":", 1)[1].strip()
                elif line.startswith("Scene:"):
                    config["scene"] = line.split(":", 1)[1].strip()
                elif line.startswith("Interaction:"):
                    config["interaction"] = line.split(":", 1)[1].strip()
                elif line.startswith("Score:"):
                    try:
                        config["score"] = int(line.split(":", 1)[1].strip())
                    except Exception:
                        pass
                elif line.startswith("Character:"):
                    parts = [p.strip() for p in line.split("|")]
                    char_data = {"name": "", "outfit": "Base", "pose_preset": "", "color_scheme": ""}
                    for p in parts:
                        if p.startswith("Character:"):
                            char_data["name"] = p.split(":", 1)[1].strip()
                        elif p.startswith("Outfit:"):
                            char_data["outfit"] = p.split(":", 1)[1].strip() or "Base"
                        elif p.startswith("Pose:"):
                            char_data["pose_preset"] = p.split(":", 1)[1].strip()
                        elif p.startswith("Color_Scheme:"):
                            char_data["color_scheme"] = p.split(":", 1)[1].strip()
                    if char_data["name"]:
                        config["selected_characters"].append(char_data)
        return config
