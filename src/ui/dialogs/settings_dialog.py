import flet as ft
import os
import threading
from core.flet_theme_manager import ThemeManager
from utils.preferences import PreferencesManager
from utils.gemma_client import GemmaClient


class SettingsDialog(ft.AlertDialog):
    """Configuration dialog for AI models (Gemini Flash / Ollama), theme, and preferences."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.modal = True
        self.prefs_mgr = PreferencesManager()

        # Load current preferences
        self.cur_provider = self.prefs_mgr.get("ai_provider", "auto")
        self.cur_gemini_model = self.prefs_mgr.get("gemini_model", "gemini-2.5-flash")
        self.cur_api_key = self.prefs_mgr.get("gemini_api_key", "")
        self.cur_ollama_model = self.prefs_mgr.get("ollama_model", "gemma2")
        self.cur_ollama_url = self.prefs_mgr.get("ollama_base_url", "http://localhost:11434")
        self.cur_temp = float(self.prefs_mgr.get("ai_temperature", 0.7))
        self.cur_style = self.prefs_mgr.get("enhance_style", "cinematic")
        self.cur_theme = self.prefs_mgr.get("last_theme", "Dark")

        # --- Dialog Header ---
        self.title = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.SETTINGS_SUGGEST, color="#ffffff", size=22),
                        width=38,
                        height=38,
                        border_radius=19,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(-1, -1),
                            end=ft.Alignment(1, 1),
                            colors=["#2563eb", ThemeManager.colors["accent"]],
                        ),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text("Application Settings", size=17, weight=ft.FontWeight.W_700),
                        ft.Text("Configure Gemini Flash AI models, API keys, and workflow defaults",
                                size=11, color=ThemeManager.colors["text_secondary"]),
                    ], spacing=2, tight=True),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip="Close",
                    icon_color=ThemeManager.colors["text_secondary"],
                    on_click=lambda _: self.app.close_dialog(self)
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.only(bottom=5),
        )

        # =====================================================================
        #  AI PROVIDER & GEMINI SETTINGS
        # =====================================================================
        provider_map = {
            "auto": "Auto (Gemini Flash Cloud / Local Fallback)",
            "gemini": "Gemini Flash (Google GenAI Cloud)",
            "cloud": "Gemini Flash (Google GenAI Cloud)",
            "ollama": "Ollama (Local Server)",
            "local": "Ollama (Local Server)",
        }
        rev_provider_map = {
            "Auto (Gemini Flash Cloud / Local Fallback)": "auto",
            "Gemini Flash (Google GenAI Cloud)": "gemini",
            "Ollama (Local Server)": "ollama",
        }
        self.rev_provider_map = rev_provider_map

        provider_val = provider_map.get(self.cur_provider, "Auto (Gemini Flash Cloud / Local Fallback)")
        self.provider_dd = ft.Dropdown(
            label="AI Provider Mode",
            options=[
                ft.dropdown.Option("Auto (Gemini Flash Cloud / Local Fallback)"),
                ft.dropdown.Option("Gemini Flash (Google GenAI Cloud)"),
                ft.dropdown.Option("Ollama (Local Server)"),
            ],
            value=provider_val,
            text_size=12,
            height=44,
            content_padding=10,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )
        if hasattr(self.provider_dd, "on_select"):
            self.provider_dd.on_select = self._on_provider_change

        # Gemini Model Dropdown
        known_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        model_is_custom = self.cur_gemini_model not in known_models
        model_dd_val = "Custom" if model_is_custom else self.cur_gemini_model

        self.gemini_model_dd = ft.Dropdown(
            label="Gemini Model",
            options=[
                ft.dropdown.Option("gemini-2.5-flash", "Gemini 2.5 Flash (Recommended - Fastest & Smartest)"),
                ft.dropdown.Option("gemini-2.0-flash", "Gemini 2.0 Flash (Stable Multimodal)"),
                ft.dropdown.Option("gemini-1.5-flash", "Gemini 1.5 Flash (Reliable Fallback)"),
                ft.dropdown.Option("Custom", "Custom Model ID..."),
            ],
            value=model_dd_val,
            text_size=12,
            height=44,
            content_padding=10,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )
        if hasattr(self.gemini_model_dd, "on_select"):
            self.gemini_model_dd.on_select = self._on_model_change

        self.custom_model_input = ft.TextField(
            label="Custom Gemini Model ID",
            value=self.cur_gemini_model if model_is_custom else "",
            text_size=12,
            height=42,
            content_padding=10,
            visible=model_is_custom,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )

        # API Key Field
        env_has_key = bool(os.environ.get("GEMINI_API_KEY"))
        api_hint = "Configured via GEMINI_API_KEY environment variable" if env_has_key else "Paste AI Studio API key here"
        
        self.api_key_input = ft.TextField(
            label="Google Gemini API Key",
            value=self.cur_api_key,
            hint_text=api_hint,
            password=True,
            can_reveal_password=True,
            text_size=12,
            height=44,
            content_padding=10,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
            expand=True,
        )

        env_status_badge = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE if env_has_key else ft.Icons.INFO_OUTLINE,
                    size=14,
                    color="#22c55e" if env_has_key else ThemeManager.colors["text_secondary"],
                ),
                ft.Text(
                    "Env Key Active" if env_has_key else "No Env Key",
                    size=10,
                    color="#22c55e" if env_has_key else ThemeManager.colors["text_secondary"],
                    weight=ft.FontWeight.W_600,
                ),
            ], spacing=4),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.Colors.with_opacity(0.1, "#22c55e" if env_has_key else "#888888"),
            border_radius=6,
        )

        # Ollama settings
        self.ollama_model_input = ft.TextField(
            label="Ollama Model Name",
            value=self.cur_ollama_model,
            hint_text="e.g. gemma2, gemma4, llama3",
            text_size=12,
            height=42,
            content_padding=10,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
            expand=True,
        )

        self.ollama_url_input = ft.TextField(
            label="Ollama Server URL",
            value=self.cur_ollama_url,
            text_size=12,
            height=42,
            content_padding=10,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
            expand=True,
        )

        # Temperature Slider
        self.temp_slider = ft.Slider(
            min=0.0,
            max=1.0,
            divisions=10,
            value=self.cur_temp,
            label="{value}",
            active_color=ThemeManager.colors["accent"],
        )

        # Enhancement Style Dropdown
        self.style_dd = ft.Dropdown(
            label="Default Enhancement Style",
            options=[
                ft.dropdown.Option("cinematic", "Cinematic & Atmospheric (Lighting, Volumetric, Depth)"),
                ft.dropdown.Option("photorealistic", "Photorealistic & Tactile (35mm/85mm, Optics, Texture)"),
                ft.dropdown.Option("compact", "Compact & Dense (Strict Token Constraints)"),
                ft.dropdown.Option("vivid", "Vivid & Dynamic (Vibrant Colors, Energy)"),
            ],
            value=self.cur_style,
            text_size=12,
            height=44,
            content_padding=10,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )

        # Theme Selector
        self.theme_dd = ft.Dropdown(
            label="Application Theme",
            options=[ft.dropdown.Option(name) for name in ThemeManager.get_available_themes()],
            value=self.cur_theme,
            text_size=12,
            height=44,
            content_padding=10,
            border_color=ThemeManager.colors["outline"],
            focused_border_color=ThemeManager.colors["accent"],
        )

        # Test Connection button & status
        self.test_btn = ft.OutlinedButton(
            "Test AI Connection",
            icon=ft.Icons.NETWORK_CHECK,
            on_click=self._on_test_connection,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        self.test_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
        self.test_status = ft.Text("", size=11, selectable=True)

        test_row = ft.Row([
            self.test_btn,
            self.test_ring,
            self.test_status,
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Layout Container
        def _section_card(title, icon, controls, accent=None):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, size=15, color=accent or ThemeManager.colors["accent"]),
                        ft.Text(title, weight=ft.FontWeight.W_600, size=12, color=ThemeManager.colors["text_primary"]),
                    ], spacing=8),
                    *controls,
                ], spacing=10, tight=True),
                padding=12,
                border_radius=8,
                bgcolor=ThemeManager.colors["panel_bg"],
                border=ft.Border.all(1, ThemeManager.colors["outline"]),
            )

        ai_section = _section_card(
            "Gemini Flash & AI Intelligence",
            ft.Icons.AUTO_AWESOME,
            [
                self.provider_dd,
                self.gemini_model_dd,
                self.custom_model_input,
                ft.Row([self.api_key_input, env_status_badge], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([self.ollama_model_input, self.ollama_url_input], spacing=10),
                ft.Row([
                    ft.Text("Creativity / Temperature:", size=11, color=ThemeManager.colors["text_secondary"], width=160),
                    ft.Container(self.temp_slider, expand=True),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                test_row,
            ],
            accent=ThemeManager.colors["accent"],
        )

        workflow_section = _section_card(
            "Workflow & Enhancement Defaults",
            ft.Icons.TUNE,
            [
                self.style_dd,
                self.theme_dd,
            ],
        )

        self.content = ft.Container(
            width=640,
            content=ft.Column([
                ai_section,
                workflow_section,
            ], spacing=12, tight=True, scroll=ft.ScrollMode.AUTO),
        )

        # Dialog Actions
        self.cancel_btn = ft.TextButton("Cancel", on_click=self._on_cancel)
        self.save_btn = ft.FilledButton(
            "Save & Apply",
            icon=ft.Icons.CHECK,
            on_click=self._on_save,
            style=ft.ButtonStyle(
                bgcolor=ThemeManager.colors["accent"],
                color="#ffffff",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        self.actions = [self.cancel_btn, self.save_btn]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _on_provider_change(self, e):
        pass

    def _on_model_change(self, e):
        is_custom = self.gemini_model_dd.value == "Custom"
        self.custom_model_input.visible = is_custom
        self.update()

    def _on_test_connection(self, e):
        self.test_btn.disabled = True
        self.test_ring.visible = True
        self.test_status.value = "Testing connection..."
        self.test_status.color = ThemeManager.colors["text_secondary"]
        self.update()

        # Gather current values for test client
        chosen_provider = self.rev_provider_map.get(self.provider_dd.value, "auto")
        gemini_model = self.custom_model_input.value if self.gemini_model_dd.value == "Custom" else self.gemini_model_dd.value
        api_key = self.api_key_input.value.strip() or None
        ollama_model = self.ollama_model_input.value.strip() or "gemma2"
        ollama_base = self.ollama_url_input.value.strip() or "http://localhost:11434"

        def _test():
            try:
                test_client = GemmaClient(
                    mode=chosen_provider,
                    api_key=api_key,
                    cloud_model=gemini_model,
                    ollama_model=ollama_model,
                    ollama_base=ollama_base,
                )
                success, msg = test_client.test_connection()
                self.test_status.value = msg
                self.test_status.color = "#22c55e" if success else "#ef4444"
            except Exception as ex:
                self.test_status.value = f"Error: {ex}"
                self.test_status.color = "#ef4444"
            finally:
                self.test_btn.disabled = False
                self.test_ring.visible = False
                if self.page:
                    self.update()

        threading.Thread(target=_test, daemon=True).start()

    def _on_save(self, e):
        # Resolve values
        provider = self.rev_provider_map.get(self.provider_dd.value, "auto")
        gemini_model = self.custom_model_input.value.strip() if self.gemini_model_dd.value == "Custom" else self.gemini_model_dd.value
        api_key = self.api_key_input.value.strip()
        ollama_model = self.ollama_model_input.value.strip() or "gemma2"
        ollama_url = self.ollama_url_input.value.strip() or "http://localhost:11434"
        temp = round(float(self.temp_slider.value), 2)
        style = self.style_dd.value
        theme = self.theme_dd.value

        # Persist
        self.prefs_mgr.set("ai_provider", provider)
        self.prefs_mgr.set("gemini_model", gemini_model)
        self.prefs_mgr.set("gemini_api_key", api_key)
        self.prefs_mgr.set("ollama_model", ollama_model)
        self.prefs_mgr.set("ollama_base_url", ollama_url)
        self.prefs_mgr.set("ai_temperature", temp)
        self.prefs_mgr.set("enhance_style", style)
        self.prefs_mgr.set("last_theme", theme)

        # Apply to live app state
        try:
            self.app.state.ctx.gemma_client = GemmaClient(
                mode=provider,
                api_key=api_key or None,
                cloud_model=gemini_model,
                ollama_model=ollama_model,
                ollama_base=ollama_url,
            )
        except Exception as ex:
            print(f"Failed to update live client: {ex}")

        # Apply theme if changed
        if theme != self.cur_theme:
            self.app.set_theme(theme)

        self.app.show_toast(f"Settings saved! Active Model: {gemini_model}", color="green")
        self.app.close_dialog(self)

    def _on_cancel(self, e):
        self.app.close_dialog(self)
