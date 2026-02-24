import flet as ft
from utils.llm_export import generate_llm_export_text, get_content_creation_prompts
from utils.text_parser import TextParser

class LLMExportDialog(ft.AlertDialog):
    def __init__(self, app):
        self.app = app
        text_content = generate_llm_export_text(self.app.ctx)
        
        self.output_field = ft.TextField(
            value=text_content,
            multiline=True,
            read_only=True,
            text_size=12,
            min_lines=15,
            max_lines=20,
            expand=True
        )
        
        super().__init__(
            title=ft.Text("EXPORT FOR LLM CONTEXT", weight="bold"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Copy the context below and paste it into your LLM:", color="grey"),
                    self.output_field
                ], tight=True),
                width=800,
                height=600
            ),
            actions=[
                ft.TextButton("Copy to Clipboard", on_click=self.copy_to_clipboard),
                ft.TextButton("Close", on_click=self.close)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def copy_to_clipboard(self, e):
        self.app.page.set_clipboard(self.output_field.value)
        self.app.show_toast("Context copied to clipboard!")

    def close(self, e):
        self.open = False
        self.app.page.update()

class ImportFromTextDialog(ft.AlertDialog):
    def __init__(self, app):
        self.app = app
        
        self.input_field = ft.TextField(
            label="Paste Prompt Summary or LLM Block",
            multiline=True,
            min_lines=10,
            max_lines=15,
            expand=True,
            text_size=12
        )
        
        super().__init__(
            title=ft.Text("IMPORT FROM TEXT", weight="bold"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Supported: App summaries, interaction templates, and structured LLM config blocks.", size=12, color="grey"),
                    self.input_field
                ], tight=True),
                width=700,
            ),
            actions=[
                ft.TextButton("Import", on_click=self.do_import),
                ft.TextButton("Cancel", on_click=self.close)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def do_import(self, e):
        text = self.input_field.value
        if not text.strip():
            self.app.show_toast("Please paste some text first.")
            return

        try:
            # Use metadata to see ALL available characters
            available_chars = list(self.app.state.ctx.characters_metadata.keys())
            config = TextParser.parse_import_text(text, available_chars)
            
            if config["selected_characters"] or config["base_prompt"] != "Default":
                self.app.restore_state(config)
                self.app.show_toast(f"Imported successfully!")
                self.close(None)
            else:
                self.app.show_toast("No valid valid data found in text.", color="orange")
                
        except Exception as ex:
            self.app.show_toast(f"Import Failed: {ex}", color="red")

    def close(self, e):
        self.open = False
        self.app.page.update()

class LLMContentCreationDialog(ft.AlertDialog):
    def __init__(self, app):
        self.app = app
        prompts = get_content_creation_prompts(self.app.ctx)
        
        # Build Tabs
        tabs = ft.Tabs(
            selected_index=0,
            expand=True,
            tabs=[]
        )
        
        for category, text in prompts.items():
            content_field = ft.TextField(
                value=text,
                multiline=True,
                read_only=True,
                text_size=12,
                expand=True,
                border_color=ft.Colors.TRANSPARENT
            )
            
            # COPY Button specific to this tab? 
            # Actually easier to have a generic copy button that copies active tab
            # But we can embed a Copy button in the content
            
            tab_content = ft.Container(
                content=ft.Column([
                    ft.ElevatedButton("Copy Prompt", icon=ft.Icons.COPY, on_click=lambda e, t=text: self.copy_text(t)),
                    ft.Divider(),
                    content_field
                ], expand=True),
                padding=10
            )
            
            tabs.tabs.append(ft.Tab(text=category.upper(), content=tab_content))

        super().__init__(
            title=ft.Text("LLM CONTENT CREATION GUIDE", weight="bold"),
            content=ft.Container(
                content=tabs,
                width=900,
                height=700,
            ),
            actions=[
                ft.TextButton("Close", on_click=self.close)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def copy_text(self, text):
        self.app.page.set_clipboard(text)
        self.app.show_toast("Prompt copied to clipboard!")

    def close(self, e):
        self.open = False
        self.app.page.update()
