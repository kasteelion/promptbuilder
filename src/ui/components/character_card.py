import flet as ft
import os
import base64
import re

def create_character_card(char_name: str, char_data: dict, on_click_callback, is_selected: bool = False, is_web: bool = False):
    """
    Creates a character card component.
    Args:
        char_name: Display name of the character
        char_data: Dictionary containing 'photo' and 'tags'
        on_click_callback: Function to call when card is clicked
        is_selected: Whether this character is in the Active Roster
        is_web: Whether running in web mode (changes asset path resolution)
    """
    # Uses a Vertical Column layout (Image Top, Text Bottom) to avoid Stack rendering issues.
    # Data extraction
    photo_filename = char_data.get("photo", "")
    # Web mode: /path resolves via Flet's asset server. Desktop: filesystem-relative path.
    if photo_filename:
        photo_path = f"/data/characters/{photo_filename}" if is_web else f"assets/data/characters/{photo_filename}"
    else:
        photo_path = ""
    
    is_valid_image = bool(photo_filename) # Trust Flet/Assets since Sanity Check passed
    
    # Tags
    tags_raw = char_data.get("tags", "")
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    else:
        tags = tags_raw or []
        
    display_tags = " • ".join(tags[:3])
    
    # [NEW] Meta extraction
    vibe = char_data.get("vibe", "")
    age_raw = char_data.get("age_presentation", "")
    # Truncate age to just the core descriptor (e.g. "mid-20s" from "mid-20s presentation; vibrant, grounded")
    age = age_raw.split(";")[0].split("presentation")[0].strip().rstrip(",") if age_raw else ""
    
    # Visual Elements
    
    # 1. Image Component
    if is_valid_image:
        image_component = ft.Image(
            src=photo_path,
            fit="cover",
            width=160,
            height=140, 
            border_radius=ft.BorderRadius.only(top_left=12, top_right=12),
        )
    else:
        # Fallback
        image_component = ft.Container(
            bgcolor=ft.Colors.BLUE_GREY_800,
            alignment=ft.Alignment(0, 0),
            width=160,
            height=140,
            border_radius=ft.BorderRadius.only(top_left=12, top_right=12),
            content=ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.WHITE54)
        )

    
    # 2. Info Panel (Name + Tags + Age) - Polish
    info_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(char_name, weight="bold", size=13, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.WHITE, expand=True),
                ft.Text(age, size=10, color=ft.Colors.WHITE60) if age else ft.Container()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=0),
            ft.Text(display_tags, size=10, color=ft.Colors.WHITE70, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        ], spacing=2),
        padding=ft.Padding(8, 6, 8, 6),
        bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.BLACK), # Semi-transparent
        border_radius=ft.BorderRadius.only(bottom_left=12, bottom_right=12),
    )
    
    # 2b. Vibe Badge - Premium Overlay (Truncated to first segment)
    vibe_badge = None
    if vibe:
        short_vibe = re.split(r",|;|/", vibe)[0].strip()
        vibe_badge = ft.Container(
            content=ft.Text(short_vibe.upper(), size=9, weight="bold", color=ft.Colors.WHITE),
            top=8, left=8,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLUE_GREY_900),
            border_radius=4,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE))
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

    # Main Card Container — filter out None overlays to prevent Flet rendering failures
    overlays = [x for x in [vibe_badge, selection_badge] if x is not None]
    if overlays:
        card_content = ft.Stack([content_col] + overlays)
    else:
        card_content = content_col
    
    def on_click_wrapper(e):
        on_click_callback(char_name)

    return ft.Container(
        content=card_content,
        width=160,
        height=200,
        bgcolor=ft.Colors.BLACK,
        border_radius=12,
        # ...
        animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT_EXPO),
        on_click=on_click_wrapper,
        on_hover=handle_hover
    )
