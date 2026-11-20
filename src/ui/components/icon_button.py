import flet as ft

class SafeIconButton(ft.Container):
    def __init__(self, icon_name, tooltip=None, on_click=None, icon_color=None, data=None, **kwargs):
        # Explicitly pass on_click and event properties to Container
        super().__init__(
            on_click=on_click,
            tooltip=tooltip,
            data=data,
            **kwargs
        )
        self.content = ft.Icon(icon_name, color=icon_color)
        self.padding = ft.Padding.all(8)
        self.border_radius = ft.BorderRadius.all(50)
        self.ink = True
        self.width = 40
        self.height = 40
        self.alignment = ft.Alignment(0, 0)
        
        # Hover effect using the new style
        self.on_hover = self._handle_hover

    def _handle_hover(self, e):
        if e.data == "true":
            self.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
        else:
            self.bgcolor = None
        self.update()
