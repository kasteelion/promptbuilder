import flet as ft
import os
import threading

class AssetGeneratorDialog(ft.AlertDialog):
    def __init__(self, app):
        self.app = app
        super().__init__()
        
        self.title = ft.Text("Asset Studio (Powered by Gemini)", weight="bold")
        
        # Asset Type Dropdown
        self.asset_type_dd = ft.Dropdown(
            label="Asset Type",
            options=[
                ft.dropdown.Option("Outfits"),
                ft.dropdown.Option("Characters"),
                ft.dropdown.Option("Scenes"),
                ft.dropdown.Option("Poses & Interactions")
            ],
            value="Outfits",
            width=200
        )
        
        # Concept Input
        self.concept_input = ft.TextField(
            label="Describe what you want to create (e.g. 'A cyberpunk streetwear outfit')",
            multiline=True,
            min_lines=2,
            max_lines=3,
            expand=True
        )
        
        # Category/Subfolder input (e.g., Combat & Tactical)
        self.category_input = ft.TextField(
            label="Category Folder (e.g., 'Combat & Tactical' or 'New Category')",
            value="Uncategorized",
            width=300
        )
        
        # Output Field (for review)
        self.output_field = ft.TextField(
            label="Generated Markdown",
            multiline=True,
            text_size=12,
            min_lines=10,
            max_lines=15,
            expand=True,
            font_family="Consolas"
        )
        
        self.progress_ring = ft.ProgressRing(visible=False, width=20, height=20)
        self.status_text = ft.Text("", size=12, color="grey")
        
        # Generate Button
        self.generate_btn = ft.FilledButton("Generate Asset", icon=ft.Icons.AUTO_FIX_HIGH, on_click=self.handle_generate)
        
        # Save Button
        self.save_btn = ft.FilledButton("Save to Files", icon=ft.Icons.SAVE, on_click=self.handle_save, disabled=True, style=ft.ButtonStyle(bgcolor="green700"))
        
        self.content = ft.Container(
            width=800,
            content=ft.Column([
                ft.Row([self.asset_type_dd, self.category_input]),
                self.concept_input,
                ft.Row([self.generate_btn, self.progress_ring, self.status_text]),
                ft.Divider(),
                self.output_field
            ], tight=True, spacing=10)
        )
        
        self.actions = [
            ft.TextButton("Close", on_click=self.close),
            self.save_btn
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def handle_generate(self, e):
        concept = self.concept_input.value.strip()
        if not concept:
            self.app.show_toast("Please enter a concept first.", color="orange")
            return
            
        gemma = self.app.state.ctx.gemma_client
        if not gemma:
            self.app.show_toast("AI Client is not available.", color="red")
            return
            
        self.generate_btn.disabled = True
        self.progress_ring.visible = True
        self.status_text.value = "Gemini is thinking..."
        self.output_field.value = ""
        self.save_btn.disabled = True
        self.update()
        
        asset_type = self.asset_type_dd.value
        
        def _run():
            try:
                result = gemma.generate_asset(asset_type, concept)
                if result.startswith("Error:"):
                    self.status_text.value = result
                    self.status_text.color = "red"
                else:
                    self.output_field.value = result
                    self.status_text.value = "Generation complete! Review and edit below before saving."
                    self.status_text.color = "green"
                    self.save_btn.disabled = False
            except Exception as ex:
                self.status_text.value = f"Error: {ex}"
                self.status_text.color = "red"
            finally:
                self.generate_btn.disabled = False
                self.progress_ring.visible = False
                if self.page:
                    self.update()
                    
        threading.Thread(target=_run, daemon=True).start()

    def handle_save(self, e):
        content = self.output_field.value.strip()
        if not content:
            return
            
        asset_type = self.asset_type_dd.value
        category = self.category_input.value.strip() or "Uncategorized"
        
        # Determine paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        data_dir = os.path.join(base_dir, "assets", "data")
        
        target_dir = ""
        filename = ""
        
        if asset_type == "Outfits":
            target_dir = os.path.join(data_dir, "outfits", category)
            # Try to extract outfit name from text or concept
            first_line = content.split('\n')[0].strip()
            # Generate a safe filename
            safe_name = "".join([c if c.isalnum() else "_" for c in self.concept_input.value[:20]])
            filename = f"Generated_Outfit_{safe_name}.txt"
            
        elif asset_type == "Characters":
            target_dir = os.path.join(data_dir, "characters")
            safe_name = "".join([c if c.isalnum() else "_" for c in self.concept_input.value[:20]])
            filename = f"{safe_name.lower()}.md"
            
        elif asset_type == "Scenes":
            target_dir = os.path.join(data_dir, "scenes")
            filename = "Generated_Scenes.md" # Appends instead of overwriting ideally, or user can manually copy
            # Let's save as a new file in scenes
            safe_name = "".join([c if c.isalnum() else "_" for c in self.concept_input.value[:20]])
            filename = f"{safe_name}.md"
            
        else:
            self.app.show_toast("Save not fully implemented for this type yet. Please copy manually.", color="orange")
            return
            
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.app.show_toast(f"Saved to {filepath}!", color="green")
            self.app.refresh_assets() # Reload data in app
            self.close(None)
        except Exception as ex:
            self.app.show_toast(f"Failed to save: {ex}", color="red")

    def close(self, e):
        self.open = False
        self.app.page.update()
