import flet as ft
import os
import base64

def create_character_card(char_name: str, char_data: dict, on_click_callback, is_selected: bool = False):
    """
    Creates a character card component.
    Args:
        char_name: Display name of the character
        char_data: Dictionary containing 'photo' and 'tags'
        on_click_callback: Function to call when card is clicked
        is_selected: Whether this character is in the Active Roster
    """
    # Uses a Vertical Column layout (Image Top, Text Bottom) to avoid Stack rendering issues.
    # Data extraction
    photo_filename = char_data.get("photo", "")
    # Simple path relative to assets_dir root
    photo_path = f"assets/data/characters/{photo_filename}" if photo_filename else ""
    
    is_valid_image = bool(photo_filename) # Trust Flet/Assets since Sanity Check passed
    
    # Tags
    tags_raw = char_data.get("tags", "")
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    else:
        tags = tags_raw or []
        
    display_tags = " • ".join(tags[:3])
    
    # Visual Elements
    
    # 1. Image Component
    if is_valid_image:
        image_component = ft.Image(
            src=photo_path,
            fit="cover",
            width=160,
            height=180, 
            border_radius=ft.BorderRadius.only(top_left=12, top_right=12),
        )
    else:
        # Fallback
        image_component = ft.Container(
            bgcolor=ft.Colors.BLUE_GREY_800,
            alignment=ft.Alignment(0, 0),
            width=160,
            height=180,
            border_radius=ft.BorderRadius.only(top_left=12, top_right=12),
            content=ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.WHITE54)
        )

    
    # 2. Info Panel (Name + Tags) - Polish
    info_panel = ft.Container(
        content=ft.Column([
            ft.Text(char_name, weight="bold", size=13, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.WHITE),
            ft.Text(display_tags, size=10, color=ft.Colors.WHITE70, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        ], spacing=2),
        padding=ft.Padding(10, 8, 10, 8),
        bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK), # Semi-transparent
        border_radius=ft.BorderRadius.only(bottom_left=12, bottom_right=12),
    )
    
    # 3. Selection Badge - Enhanced Pro
    selection_badge = None
    if is_selected:
        selection_badge = ft.Container(
            content=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.BLUE_ACCENT, size=18),
            top=8,
            right=8,
            padding=4,
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK),
            border_radius=ft.BorderRadius.all(20),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_ACCENT))
        )
    
    # Combine all elements
    content_col = ft.Column([
        image_component,
        info_panel
    ],
        spacing=0,
        alignment=ft.MainAxisAlignment.START,
    )

    # Hover Logic (Refined Micro-animations)
    def handle_hover(e):
        c = e.control
        if e.data == "true": # Enter
            c.scale = 1.05
            c.shadow = ft.BoxShadow(
                blur_radius=30, 
                color=ft.Colors.with_opacity(0.5, ft.Colors.BLUE_ACCENT),
                blur_style=ft.ShadowBlurStyle.OUTER
            )
            c.border = ft.Border.all(2, ft.Colors.BLUE_ACCENT)
        else: # Leave
            c.scale = 1.0
            c.shadow = ft.BoxShadow(
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.4, ft.Colors.BLUE_ACCENT)
            ) if is_selected else None
            c.border = ft.Border.all(2, ft.Colors.with_opacity(0.8, ft.Colors.BLUE_ACCENT)) if is_selected else None
            
        c.update()

    # Main Card Container
    card_content = ft.Stack([
        content_col,
        selection_badge
    ]) if selection_badge else content_col
    
    def on_click_wrapper(e):
        print(f"DEBUG_CLICK: Card clicked for {char_name}")
        on_click_callback(char_name)

    return ft.Container(
        content=card_content,
        width=160,
        height=240,
        bgcolor=ft.Colors.BLACK,
        border_radius=12,
        # ...
        animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT_EXPO),
        on_click=on_click_wrapper,
        on_hover=handle_hover
    )
