from collections import deque
import flet as ft
from core.flet_theme_manager import ThemeManager
from utils.preferences import PreferencesManager


class ConsoleSection(ft.Column):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.spacing = 0
        self.previous_prompt = None
        self.prefs_mgr = PreferencesManager()
        self.history: deque = deque(maxlen=20)
        self._active_history_idx = -1

        self.output_field = ft.TextField(
            multiline=True, read_only=True, min_lines=3, max_lines=12, text_size=13,
            border_color=ThemeManager.colors["outline"],
            bgcolor=ft.Colors.with_opacity(0.4, ThemeManager.colors["surface"]),
            color=ThemeManager.colors["text_primary"],
            expand=True,
            cursor_color=ThemeManager.colors["accent"],
        )

        self.enhance_style = self.prefs_mgr.get("enhance_style", "cinematic")
        self.format_mode = "markdown"

        self.format_toggle = ft.SegmentedButton(
            selected=["markdown"],
            allow_multiple_selection=False,
            on_change=self._on_format_changed,
            segments=[
                ft.Segment(
                    value="markdown",
                    label=ft.Text("Markdown", size=10, weight=ft.FontWeight.W_600),
                    icon=ft.Icon(ft.Icons.CODE, size=12),
                ),
                ft.Segment(
                    value="prose",
                    label=ft.Text("🍌 Prose", size=10, weight=ft.FontWeight.W_600),
                    icon=ft.Icon(ft.Icons.AUTO_STORIES, size=12),
                ),
                ft.Segment(
                    value="midjourney",
                    label=ft.Text("MJ", size=10, weight=ft.FontWeight.W_600),
                    icon=ft.Icon(ft.Icons.DIAMOND, size=12),
                ),
                ft.Segment(
                    value="sdxl",
                    label=ft.Text("SDXL", size=10, weight=ft.FontWeight.W_600),
                    icon=ft.Icon(ft.Icons.MEMORY, size=12),
                ),
            ],
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
        )

        self.takes_btn = ft.OutlinedButton(
            "3 Takes",
            icon=ft.Icons.MOVIE_FILTER_OUTLINED,
            on_click=self.handle_director_takes,
            tooltip="Generate 3 diverse cinematic takes with Gemini",
            style=ft.ButtonStyle(
                color=ThemeManager.colors["text_primary"],
                side=ft.BorderSide(1, ft.Colors.with_opacity(0.3, ThemeManager.colors["accent"])),
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            ),
        )

        self.enhance_btn = ft.FilledButton(
            "Enhance",
            icon=ft.Icons.AUTO_FIX_NORMAL,
            on_click=self.handle_enhance,
            style=ft.ButtonStyle(
                color=ThemeManager.colors["text_primary"],
                bgcolor=ft.Colors.with_opacity(0.12, ThemeManager.colors["accent"]),
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            ),
            tooltip="Enhance prompt with Gemini Flash",
        )

        self.style_menu_btn = ft.PopupMenuButton(
            icon=ft.Icons.STYLE_OUTLINED,
            icon_color=ThemeManager.colors["text_secondary"],
            tooltip="Select Enhancement Style",
            items=[
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.MOVIE, size=16), ft.Text("Cinematic & Atmospheric", size=12)], spacing=8),
                    on_click=lambda _: self._set_enhance_style("cinematic"),
                ),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.CAMERA_ALT, size=16), ft.Text("Photorealistic & Optics", size=12)], spacing=8),
                    on_click=lambda _: self._set_enhance_style("photorealistic"),
                ),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.BOLT, size=16), ft.Text("Compact & Dense", size=12)], spacing=8),
                    on_click=lambda _: self._set_enhance_style("compact"),
                ),
                ft.PopupMenuItem(
                    content=ft.Row([ft.Icon(ft.Icons.PALETTE, size=16), ft.Text("Vivid & Colorful", size=12)], spacing=8),
                    on_click=lambda _: self._set_enhance_style("vivid"),
                ),
            ],
        )

        self.revert_btn = ft.IconButton(
            icon=ft.Icons.UNDO,
            icon_color=ThemeManager.colors["text_secondary"],
            tooltip="Revert to pre-enhancement prompt",
            visible=False,
            on_click=self.handle_revert,
        )

        self.console_header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.TERMINAL, color="#ffffff", size=16),
                        width=28, height=28, border_radius=7,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                            colors=[ThemeManager.colors["accent"], "#7c3aed"],
                        ),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text("FINAL PROMPT", weight=ft.FontWeight.W_700, size=14,
                            color=ThemeManager.colors["text_primary"]),
                    self.format_toggle,
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    self.revert_btn,
                    self.takes_btn,
                    self.enhance_btn,
                    self.style_menu_btn,
                    ft.FilledButton(
                        "Copy", icon=ft.Icons.COPY,
                        on_click=lambda e: self.app.handle_copy(e),
                        style=ft.ButtonStyle(
                            color=ThemeManager.colors["text_primary"],
                            bgcolor=ft.Colors.with_opacity(0.08, "#ffffff"),
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        ),
                    ),
                    ft.FilledButton(
                        "Generate", icon=ft.Icons.AUTO_AWESOME,
                        on_click=lambda _: self.app.handle_generate(),
                        style=ft.ButtonStyle(
                            color="#ffffff",
                            bgcolor=ThemeManager.colors["accent"],
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                        ),
                    ),
                ], spacing=6),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0),
                colors=[ThemeManager.colors["panel_bg"], ThemeManager.colors["active_item"]],
            ),
            border_radius=ft.BorderRadius.only(top_left=10, top_right=10),
        )

        self.output_container = ft.Container(
            content=self.output_field,
            border=ft.Border.all(1, ThemeManager.colors["outline"]),
            border_radius=ft.BorderRadius.only(bottom_left=10, bottom_right=10),
            padding=0,
        )

        self.history_header_icon = ft.Icon(ft.Icons.HISTORY, size=14, color=ThemeManager.colors["text_secondary"])
        self.history_header_text = ft.Text("History", size=11, weight=ft.FontWeight.W_600, color=ThemeManager.colors["text_secondary"])
        self.clear_history_btn = ft.IconButton(
            icon=ft.Icons.CLEAR_ALL,
            icon_size=14,
            icon_color=ThemeManager.colors["text_secondary"],
            tooltip="Clear history",
            on_click=self._clear_history,
            style=ft.ButtonStyle(padding=0),
            width=20,
            height=20,
        )
        self.history_header = ft.Row(
            [
                ft.Row([self.history_header_icon, self.history_header_text], spacing=4),
                self.clear_history_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.history_row = ft.Row(
            scroll=ft.ScrollMode.AUTO,
            spacing=4,
            height=32,
        )

        self.history_container = ft.Container(
            content=ft.Column(
                [
                    self.history_header,
                    self.history_row,
                ],
                spacing=2,
            ),
            border=ft.Border(
                left=ft.BorderSide(1, ThemeManager.colors["outline"]),
                right=ft.BorderSide(1, ThemeManager.colors["outline"]),
                bottom=ft.BorderSide(1, ThemeManager.colors["outline"]),
            ),
            border_radius=ft.BorderRadius.only(bottom_left=10, bottom_right=10),
            bgcolor=ft.Colors.with_opacity(0.3, ThemeManager.colors["surface"]),
            padding=ft.Padding.only(left=10, right=10, top=4, bottom=6),
            visible=False,
        )

        self.controls = [
            self.console_header,
            self.output_container,
            self.history_container,
        ]

    def _on_format_changed(self, e):
        selected_items = list(self.format_toggle.selected) if self.format_toggle.selected else ["markdown"]
        selected = selected_items[0] if selected_items else "markdown"
        self.format_mode = selected
        if hasattr(self.app, "update_preview"):
            self.app.update_preview()
        elif hasattr(self.app, "state") and hasattr(self.app.state, "get_prompt"):
            self.update_output(self.app.state.get_prompt(format_type=self.format_mode))
        format_labels = {
            "markdown": "Structured Markdown",
            "prose": "🍌 Nanobanana Prose",
            "midjourney": "Midjourney v6.1",
            "sdxl": "SDXL / ComfyUI Tags",
        }
        self.app.show_toast(f"Format: {format_labels.get(selected, selected)}")

    def handle_director_takes(self, e):
        from ui.dialogs.director_takes_dialog import DirectorTakesDialog

        current_prompt = self.output_field.value
        if not current_prompt:
            self.app.show_toast("No prompt to direct! Select characters or generate first.", color="orange")
            return

        ai_client = self.app.state.ctx.gemma_client
        if not ai_client:
            self.app.show_toast("AI Client not initialized.", color="red")
            return

        self.takes_btn.disabled = True
        self.takes_btn.text = "Directing 3 Takes..."
        self.update()

        async def _direct():
            try:
                import asyncio
                takes = await asyncio.to_thread(ai_client.generate_director_takes, current_prompt, 3)
                if not takes:
                    self.app.show_toast("Could not generate director takes.", color="orange")
                    return

                def _apply_take(selected_prompt: str):
                    self.previous_prompt = self.output_field.value
                    if self.previous_prompt:
                        self._push_to_history(self.previous_prompt)
                    self.output_field.value = selected_prompt
                    self.revert_btn.visible = True
                    self.output_field.update()
                    self.revert_btn.update()

                dialog = DirectorTakesDialog(self.app, takes, on_apply=_apply_take)
                dialog.show()
            except Exception as ex:
                print(f"[AIClient] Director's Takes error: {ex}")
                self.app.show_toast(f"Director error: {ex}", color="red")
            finally:
                self.takes_btn.disabled = False
                self.takes_btn.text = "🎬 3 Takes"
                if self.page:
                    self.page.update()

        if self.page:
            self.page.run_task(_direct)

    def _set_enhance_style(self, style: str):
        self.enhance_style = style
        self.prefs_mgr.set("enhance_style", style)
        self.app.show_toast(f"Enhancement style set to: {style.capitalize()}")

    def handle_revert(self, e):
        if self.previous_prompt:
            self.output_field.value = self.previous_prompt
            self.previous_prompt = None
            self.revert_btn.visible = False
            try:
                self.output_field.update()
                self.revert_btn.update()
            except Exception:
                pass
            self.app.show_toast("Reverted to original prompt.")

    def handle_enhance(self, e):
        if not self.output_field.value:
            self.app.show_toast("No prompt to enhance!", color="orange")
            return

        ai_client = self.app.state.ctx.gemma_client
        if not ai_client:
            self.app.show_toast("AI Client not initialized.", color="red")
            return

        # Cache original prompt for undo/revert
        self.previous_prompt = self.output_field.value

        self.enhance_btn.disabled = True
        self.enhance_btn.text = "Enhancing with Gemini..."
        self.update()

        async def _enhance():
            import sys
            import asyncio
            style = getattr(self, "enhance_style", "cinematic")
            print(f"[AIClient] Enhancing prompt with style '{style}'...")
            sys.stdout.flush()

            try:
                enhanced_text = await asyncio.to_thread(ai_client.enhance_prompt, self.previous_prompt, style=style)

                if enhanced_text and not enhanced_text.startswith("Error:"):
                    if self.previous_prompt:
                        self._push_to_history(self.previous_prompt)
                    self.output_field.value = enhanced_text
                    self.revert_btn.visible = True
                    self.app.show_toast(f"Prompt enhanced with Gemini Flash ({style.capitalize()})!", color="green")
                else:
                    self.app.show_toast(f"Enhancement notice: {enhanced_text}", color="red")
            except Exception as ex:
                print(f"[AIClient] Enhancement error: {ex}")
                self.app.show_toast(f"Enhancement failed: {ex}", color="red")
            finally:
                self.enhance_btn.disabled = False
                self.enhance_btn.text = "✨ Enhance with Gemini"
                if self.page:
                    self.page.update()

        if self.page:
            self.page.run_task(_enhance)

    def _push_to_history(self, prompt: str):
        prompt_str = (prompt or "").strip()
        if not prompt_str:
            return
        if self.history and self.history[0] == prompt_str:
            return
        self.history.appendleft(prompt_str)
        self._active_history_idx = -1
        self._rebuild_history_chips()

    def _clear_history(self, e=None):
        self.history.clear()
        self._active_history_idx = -1
        self._rebuild_history_chips()
        if hasattr(self.app, "show_toast"):
            self.app.show_toast("Prompt history cleared.")

    def _restore_from_history(self, index: int):
        if 0 <= index < len(self.history):
            self.previous_prompt = self.output_field.value
            restored = self.history[index]
            self.output_field.value = restored
            self.revert_btn.visible = True
            self._active_history_idx = index
            self._rebuild_history_chips(active_index=index)
            try:
                self.output_field.update()
                self.revert_btn.update()
            except Exception:
                pass
            if hasattr(self.app, "show_toast"):
                self.app.show_toast("Restored prompt from history.", color="green")

    def _rebuild_history_chips(self, active_index: int = -1):
        self.history_row.controls.clear()
        total = len(self.history)
        for idx, item in enumerate(self.history):
            preview = item.replace("\n", " ").strip()
            if len(preview) > 35:
                preview = preview[:32] + "..."
            is_active = (idx == active_index)
            chip_text = ft.Text(
                f"#{total - idx} {preview}",
                size=10,
                color=ThemeManager.colors["accent"] if is_active else ThemeManager.colors["text_secondary"],
                no_wrap=True,
            )
            chip = ft.TextButton(
                content=chip_text,
                tooltip=item[:200] + ("..." if len(item) > 200 else ""),
                on_click=lambda e, i=idx: self._restore_from_history(i),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    bgcolor=ft.Colors.with_opacity(0.18, ThemeManager.colors["accent"]) if is_active else ft.Colors.with_opacity(0.05, ThemeManager.colors["text_primary"]),
                ),
            )
            self.history_row.controls.append(chip)

        was_visible = self.history_container.visible
        has_items = total > 0
        self.history_container.visible = has_items

        if has_items:
            self.output_container.border_radius = ft.BorderRadius.all(0)
        else:
            self.output_container.border_radius = ft.BorderRadius.only(bottom_left=10, bottom_right=10)

        try:
            if self.page:
                self.history_container.update()
                if was_visible != has_items:
                    self.output_container.update()
        except Exception:
            pass

    def update_output(self, text: str):
        current = (self.output_field.value or "").strip()
        new_text = (text or "").strip()
        if current and current != new_text:
            self._push_to_history(current)

        self.output_field.value = text
        try:
            self.output_field.update()
        except Exception:
            pass

    def refresh_theme(self, update_ui=True):
        self.output_field.border_color = ThemeManager.colors["outline"]
        self.output_field.bgcolor = ft.Colors.with_opacity(0.4, ThemeManager.colors["surface"])
        self.output_field.color = ThemeManager.colors["text_primary"]
        self.console_header.gradient.colors = [ThemeManager.colors["panel_bg"], ThemeManager.colors["active_item"]]
        # Update text color in header
        self.console_header.content.controls[0].controls[1].color = ThemeManager.colors["text_primary"]

        self.output_container.border = ft.Border.all(1, ThemeManager.colors["outline"])

        self.history_header_icon.color = ThemeManager.colors["text_secondary"]
        self.history_header_text.color = ThemeManager.colors["text_secondary"]
        self.clear_history_btn.icon_color = ThemeManager.colors["text_secondary"]
        self.history_container.border = ft.Border(
            left=ft.BorderSide(1, ThemeManager.colors["outline"]),
            right=ft.BorderSide(1, ThemeManager.colors["outline"]),
            bottom=ft.BorderSide(1, ThemeManager.colors["outline"]),
        )
        self.history_container.bgcolor = ft.Colors.with_opacity(0.3, ThemeManager.colors["surface"])

        self._rebuild_history_chips(active_index=self._active_history_idx)

        if update_ui:
            self.update()
