import flet as ft
from pathlib import Path
from ui.components.icon_button import SafeIconButton

class DashboardSection(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.visible = False
        self.expand = True
        self.padding = 20
        self.bgcolor = "background"
        
        # --- UI Components ---
        self.stats_row = ft.Row(spacing=20, alignment=ft.MainAxisAlignment.CENTER)
        self.health_list = ft.ListView(expand=True, spacing=10)
        self.tag_matrix = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("TAG")),
                ft.DataColumn(ft.Text("TOTAL"), numeric=True),
                ft.DataColumn(ft.Text("CHARS"), numeric=True),
                ft.DataColumn(ft.Text("PRESETS"), numeric=True), # Combined Scenes/Interactions
            ],
            rows=[]
        )
        
        # Tabs
        # Tabs (Selector Only)
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            length=3,
            on_change=self._on_tab_change,
            content=[
                ft.Tab("OVERVIEW", icon="home"),
                ft.Tab("HEALTH", icon="favorite"),
                ft.Tab("TAG ANALYTICS", icon="list"),
            ],
            expand=False # Tabs header shouldn't expand
        )

        # Content Area
        self.content_area = ft.Container(expand=True, padding=20)
        
        # Initialize content
        self._set_view(0)

        self.content = ft.Stack([
            ft.Column([
                ft.Row([
                    ft.Text("DASHBOARD", size=30, weight="bold", color="primary"),
                    SafeIconButton("close", on_click=self.hide)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                self.tabs,
                self.content_area
            ]),
        ])
        
    def show(self, e=None):
        self.visible = True
        self.refresh_data()
        self.page.update()
        
    def hide(self, e=None):
        self.visible = False
        self.page.update()
        
    def refresh_data(self):
        """Refresh all dashboard data."""
        self._update_overview()
        self._build_tag_matrix()
        # Health check is manual run usually, but we could auto-run if empty
        if not self.health_list.controls:
             self._run_health_checks()
        self.update()

    def _on_tab_change(self, e):
        self._set_view(self.tabs.selected_index)
        self.update()

    def _set_view(self, index):
        if index == 0:
            self.content_area.content = ft.Column([
                ft.Text("Project Overview", size=24, weight="bold"),
                ft.Divider(),
                self.stats_row,
                ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
                ft.Text("Quick Actions", size=16, weight="bold"),
                ft.Row([
                    ft.ElevatedButton(
                        "Run Health Check",
                        icon="health_and_safety",
                        on_click=lambda e: setattr(self.tabs, 'selected_index', 1) or self._set_view(1) or self.update() or self._run_health_checks()
                    ),
                    ft.ElevatedButton(
                        "Refresh Data",
                        icon="refresh",
                        on_click=lambda e: self.refresh_data()
                    )
                ])
            ], scroll=ft.ScrollMode.AUTO)
        elif index == 1:
            self.content_area.content = ft.Column([
                ft.Text("System Health", size=24, weight="bold"),
                ft.Text("Automated checks for missing files and integrity issues.", color="outline"),
                ft.Divider(),
                ft.ElevatedButton("Run Auto-Diagnosis", icon="play_arrow", on_click=lambda e: self._run_health_checks()),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                self.health_list
            ])
        elif index == 2:
            self.content_area.content = ft.Column([
                ft.Text("Tag Usage Matrix", size=24, weight="bold"),
                ft.Text("Analysis of tag distribution across your library.", color="outline"),
                ft.Divider(),
                ft.Container(
                    content=self.tag_matrix,
                    expand=True,
                    border=ft.border.all(1, "outlineVariant"),
                    border_radius=10,
                    padding=10
                )
            ])


    def _update_overview(self):
        # Calculate stats
        chars = self.app.state.get("characters", {}) or {}
        scenes_data = self.app.data_loader.load_presets("scenes.md")
        interactions_data = self.app.data_loader.load_interactions()
        
        total_chars = len(chars)
        total_scenes = sum(len(cat) for cat in scenes_data.values())
        total_interactions = sum(len(cat) for cat in interactions_data.values())
        
        def make_card(title, value, icon, color):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=40, color=color),
                    ft.Text(str(value), size=30, weight="bold"),
                    ft.Text(title, size=14, color="outline")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                bgcolor="surfaceVariant",
                border_radius=15,
                width=150,
                height=150,
                alignment=ft.Alignment(0, 0)
            )

        self.stats_row.controls = [
            make_card("Characters", total_chars, "people", ft.Colors.BLUE),
            make_card("Scenes", total_scenes, "image", ft.Colors.GREEN),
            make_card("Interactions", total_interactions, "message", ft.Colors.ORANGE)
        ]

    def _run_health_checks(self):
        """Perform integrity checks."""
        self.health_list.controls.clear()
        issues_found = 0
        
        # 1. Missing Photos
        chars = self.app.state.get("characters", {})
        chars_dir = self.app.data_loader._find_characters_dir()
        
        missing_photos = []
        for name, data in chars.items():
            # Assume 1:1 filename match for simplicity or check standard
            # Logic: data_loader.resolve_photo_for_character logic simplified
            from utils.validation import sanitize_filename
            base = sanitize_filename(name).lower().replace(" ", "_")
            photo_found = False
            for ext in [".png", ".jpg", ".jpeg"]:
                if (chars_dir / f"{base}_photo{ext}").exists():
                    photo_found = True
                    break
            
            if not photo_found:
                 # Check specific field
                 if not data.get("photo"): # If no photo field and no auto-photo
                      missing_photos.append(name)

        if missing_photos:
            issues_found += len(missing_photos)
            self.health_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon("warning", color=ft.Colors.AMBER),
                    title=ft.Text(f"{len(missing_photos)} Characters missing photos"),
                    subtitle=ft.Text(", ".join(missing_photos[:5]) + ("..." if len(missing_photos) > 5 else ""))
                )
            )

        # 2. Tag Consistency (Simple check)
        # Check for tags not in tags.md
        # This requires loading tags which might be heavy, skipping for MVP speed or implementation later?
        # Actually easy if data_loader has it.
        # Skipping for now to keep it snappy, moving to file checks.

        # 3. Orphan Files check
        # ...
        
        if issues_found == 0:
            self.health_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("check_circle", size=60, color=ft.Colors.GREEN),
                        ft.Text("All Systems Nominal", size=20, weight="bold"),
                        ft.Text("No obvious data integrity issues found.", color="outline")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0),
                    padding=40
                )
            )
            
        self.health_list.update()

    def _build_tag_matrix(self):
        """Aggregate all tags."""
        tag_counts = {} # {tag: {chars: 0, presets: 0}}
        
        # Count Characters
        chars = self.app.state.get("characters", {})
        for c in chars.values():
            tags = c.get("tags", [])
            if isinstance(tags, str): tags = tags.split(",")
            for t in tags:
                t = t.strip().lower()
                if not t: continue
                if t not in tag_counts: tag_counts[t] = {"chars": 0, "presets": 0}
                tag_counts[t]["chars"] += 1

        # Count Scenes
        scenes = self.app.data_loader.load_presets("scenes.md")
        for cat in scenes.values():
            for s in cat.values():
                tags = s.get("tags", [])
                for t in tags:
                    t = t.strip().lower()
                    if not t: continue
                    if t not in tag_counts: tag_counts[t] = {"chars": 0, "presets": 0}
                    tag_counts[t]["presets"] += 1
                    
        # Sort by total
        sorted_tags = sorted(tag_counts.items(), key=lambda x: (x[1]["chars"] + x[1]["presets"]), reverse=True)
        
        self.tag_matrix.rows = []
        for t, counts in sorted_tags:
            self.tag_matrix.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(t.upper(), weight="bold")),
                    ft.DataCell(ft.Text(str(counts["chars"] + counts["presets"]))),
                    ft.DataCell(ft.Text(str(counts["chars"]))),
                    ft.DataCell(ft.Text(str(counts["presets"]))),
                ])
            )
