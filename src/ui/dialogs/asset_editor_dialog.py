import flet as ft
from core.flet_theme_manager import ThemeManager
from scripts.automation.replace_tag import replace_in_outfits, replace_in_scenes, replace_in_interactions, replace_in_poses

class AssetEditorDialog(ft.AlertDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title = ft.Text("Asset Editor", weight="bold")
        
        # Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Tag Manager", icon=ft.Icons.LABEL),
                ft.Tab(text="Metadata", icon=ft.Icons.INFO_OUTLINE), # Placeholder
            ],
            expand=True
        )
        
        # Tag Manager UI
        self.old_tag_field = ft.TextField(label="Find Tag", expand=True)
        self.new_tag_field = ft.TextField(label="Replace With (Empty to Delete)", expand=True)
        self.console_output = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        
        tag_manager_content = ft.Container(
            padding=10,
            content=ft.Column([
                ft.Text("Batch replace or delete tags across all assets.", size=12, color="grey"),
                ft.Row([self.old_tag_field, self.new_tag_field]),
                ft.Row([
                    ft.ElevatedButton("Dry Run (Scan Only)", icon=ft.Icons.SEARCH, on_click=lambda e: self.run_tag_op(dry_run=True)),
                    ft.FilledButton("Execute Changes", icon=ft.Icons.SAVE_ALT, on_click=lambda e: self.run_tag_op(dry_run=False), style=ft.ButtonStyle(bgcolor="red400")),
                ]),
                ft.Divider(),
                ft.Text("Console Output:", weight="bold"),
                ft.Container(
                    content=self.console_output,
                    bgcolor="black",
                    padding=10,
                    border_radius=5,
                    expand=True,
                    height=200
                )
            ])
        )
        
        # Link Tabs
        self.tabs.tabs[0].content = tag_manager_content
        self.tabs.tabs[1].content = ft.Container(content=ft.Text("Metadata Editor Coming Soon"), alignment=ft.alignment.center)

        self.content = ft.Container(
            width=800,
            height=600,
            content=self.tabs
        )
        
        self.actions = [
            ft.TextButton("Close", on_click=self.handle_close)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def log(self, text, color="white"):
        self.console_output.controls.append(ft.Text(text, color=color, font_family="Consolas"))
        if self.page:
            self.update()

    def run_tag_op(self, dry_run=True):
        old = self.old_tag_field.value.strip()
        new = self.new_tag_field.value.strip() or None
        
        if not old:
            self.app.show_toast("Please enter a tag to search for.", color="orange")
            return

        self.console_output.controls.clear()
        self.log(f"Starting {'DRY RUN' if dry_run else 'EXECUTION'}...", "cyan")
        self.log(f"Finding: '{old}' -> Replacing with: '{new if new else 'DELETE'}'")
        self.log("-" * 40)
        
        # Capture stdout? No, let's just rewrite simple wrapper to return logs or print to our method.
        # Since replace_tag.py uses print(), we can either redirect stdout or copy logic.
        # Copying logic is cleaner for UI integration.
        
        # Function to wrap print-based logic into UI logging
        # We'll just call the imported functions and let them print to stdout (console) for now?
        # No, user wants to see it in UI.
        
        # Let's try redirecting stdout briefly
        import io
        import sys
        
        capture = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = capture
        
        try:
            replace_in_outfits(old, new, dry_run)
            replace_in_scenes(old, new, dry_run)
            replace_in_interactions(old, new, dry_run)
            replace_in_poses(old, new, dry_run)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            sys.stdout = original_stdout
            
        # Display captured output
        output_lines = capture.getvalue().splitlines()
        for line in output_lines:
            color = "white"
            if "[MATCH]" in line: color = "green"
            if "Scanning" in line: color = "cyan"
            self.log(line, color)
            
        self.log("-" * 40)
        self.log("Operation Complete.", "green" if not dry_run else "yellow")
        
        if not dry_run:
            self.app.refresh_assets() # Reload data

    def handle_close(self, e):
        self.app.close_dialog(self)
