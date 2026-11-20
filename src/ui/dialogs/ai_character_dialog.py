import flet as ft
from core.flet_theme_manager import ThemeManager
import pathlib
import threading
import re
from utils.gemma_client import GemmaClient

class AICharacterDialog(ft.AlertDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.modal = True
        # Reuse initialized and configured app-level AI client
        self.gemma = getattr(getattr(self.app, "state", None), "ctx", None).gemma_client or GemmaClient()
        
        # --- Header ---
        self.title = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.PERSON_ADD_ALT_1, color="#ffffff", size=20),
                    width=36, height=36,
                    border_radius=18,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                        colors=["#7c3aed", ThemeManager.colors["accent"]]
                    ),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text("AI Character Creator", size=16, weight=ft.FontWeight.W_700),
                    ft.Text("Generate a character from a concept", size=11, color=ThemeManager.colors["text_secondary"]),
                ], spacing=2, tight=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(bottom=5),
        )
        
        # --- Concept Input ---
        self.concept_input = ft.TextField(
            label="Character Concept",
            hint_text="e.g., A stoic dwarven blacksmith with a cybernetic arm...",
            multiline=True,
            min_lines=3,
            max_lines=5,
            text_size=13,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )
        
        # --- Generate Button & Status ---
        self.generate_btn = ft.ElevatedButton(
            "Generate",
            icon=ft.Icons.AUTO_AWESOME,
            style=ft.ButtonStyle(
                bgcolor=ThemeManager.colors["accent"],
                color="#ffffff",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self._on_generate
        )
        
        self.progress_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ThemeManager.colors["accent"], visible=False)
        self.status_text = ft.Text("", size=12, color=ThemeManager.colors["text_secondary"])
        
        self.generate_row = ft.Row([
            self.generate_btn,
            self.progress_ring,
            self.status_text
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        # --- Preview/Edit Area ---
        self.preview_input = ft.TextField(
            label="Generated Markdown",
            multiline=True,
            min_lines=15,
            max_lines=15,
            text_size=12,
            text_style=ft.TextStyle(font_family="Consolas"),
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
            visible=False
        )
        
        # --- Dialog Content ---
        self.content = ft.Container(
            content=ft.Column([
                self.concept_input,
                self.generate_row,
                self.preview_input
            ], spacing=15, tight=True),
            width=600,
            padding=10
        )
        
        # --- Actions ---
        self.save_btn = ft.TextButton("Save Character", icon=ft.Icons.SAVE, disabled=True, on_click=self._on_save)
        self.cancel_btn = ft.TextButton("Cancel", on_click=self._close)
        
        self.actions = [self.cancel_btn, self.save_btn]
        self.actions_padding = 15

    def _close(self, _):
        self.open = False
        self.app.page.update()

    def _on_generate(self, _):
        concept = self.concept_input.value.strip()
        if not concept:
            return
            
        self.generate_btn.disabled = True
        self.progress_ring.visible = True
        self.status_text.value = "Generating..."
        self.preview_input.visible = False
        self.save_btn.disabled = True
        self.update()
        
        threading.Thread(target=self._run_generation, args=(concept,), daemon=True).start()
        
    def _run_generation(self, concept):
        markdown_result = self.gemma.generate_character_markdown(concept)
        
        if markdown_result.startswith("Error:"):
            self.status_text.value = markdown_result
            self.status_text.color = "#ef4444"
        else:
            self.status_text.value = "Generated successfully!"
            self.status_text.color = "#22c55e"
            self.preview_input.value = markdown_result
            self.preview_input.visible = True
            self.save_btn.disabled = False
            
        self.generate_btn.disabled = False
        self.progress_ring.visible = False
        
        # Use page.run_task to safely update UI from background thread if needed, or just update if we have reference
        if self.app.page:
            self.app.page.update()

    def _on_save(self, _):
        markdown_content = self.preview_input.value
        if not markdown_content:
            return
            
        # Try to extract character name from the first heading
        name_match = re.search(r"###\s+(.*)", markdown_content)
        if not name_match:
            # Fallback
            name_match = re.search(r"\*\*(?:Name|Character):\*\*\s*(.*)", markdown_content)
            
        if name_match:
            char_name = name_match.group(1).strip()
        else:
            char_name = "New Character"
            
        # Format filename: lower case, replace spaces with underscores
        filename = char_name.lower().replace(" ", "_")
        filename = re.sub(r'[^a-z0-9_]', '', filename) + ".md"
        
        data_dir = pathlib.Path("assets/data/characters")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = data_dir / filename
        
        try:
            file_path.write_text(markdown_content, encoding="utf-8")
            self.status_text.value = f"Saved as {filename}!"
            self.status_text.color = "#22c55e"
            self.save_btn.disabled = True
            self.app.page.update()
            
            # Refresh app state
            self.app.refresh_assets()
            
            # Trigger portrait generation
            if hasattr(self.app.state.ctx, "automation_controller") and self.app.state.ctx.automation_controller:
                self.app.state.ctx.automation_controller.generate_character_portrait(char_name)
            
            # Close dialog after a short delay
            threading.Timer(1.0, lambda: self._close(None)).start()
        except Exception as e:
            self.status_text.value = f"Error saving: {e}"
            self.status_text.color = "#ef4444"
            self.app.page.update()
