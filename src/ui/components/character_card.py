import flet as ft
import os
import re
from core.flet_theme_manager import ThemeManager

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
    if photo_filename and photo_filename.endswith(".png"):
        webp_name = photo_filename[:-4] + ".webp"
        webp_disk = os.path.join("assets", "data", "characters", webp_name)
        if os.path.exists(webp_disk):
            photo_filename = webp_name

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
    # Robust age parsing to extract just the core age (e.g., "mid-20s")
    age = ""
    if age_raw:
        # Split on common delimiters or the words presentation/presenting (case insensitive)
        age_clean = re.split(r"(?i)\s*(?:presentation|presenting|;|,)", age_raw)[0].strip()
        age = age_clean[:12] + "..." if len(age_clean) > 15 else age_clean
    
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

    
    # Format subtitle: age + tags
    subtitle_parts = []
    if age:
        subtitle_parts.append(age)
    if tags:
        subtitle_parts.extend(tags[:2])
    card_subtitle = " • ".join(subtitle_parts) if subtitle_parts else display_tags

    # 2. Info Panel (Full Name + Age/Tags)
    info_panel = ft.Container(
        content=ft.Column([
            ft.Text(char_name, weight="bold", size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.WHITE),
            ft.Text(card_subtitle, size=10, color=ft.Colors.WHITE70, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
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
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLUE_GREY_900),
            border_radius=4,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE))
        )
    
    selection_badge = None
    if is_selected:
        selection_badge = ft.Container(
            content=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ThemeManager.colors["accent"], size=18),
            top=8,
            right=8,
            padding=4,
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK),
            border_radius=ft.BorderRadius.all(20),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.3, ThemeManager.colors["accent"]))
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
        accent_color = ThemeManager.colors["accent"]
        if e.data == "true": # Enter
            c.scale = 1.05
            c.shadow = ft.BoxShadow(
                blur_radius=30, 
                color=ft.Colors.with_opacity(0.5, accent_color),
                blur_style=ft.ShadowBlurStyle.OUTER
            )
            c.border = ft.Border.all(2, accent_color)
        else: # Leave
            c.scale = 1.0
            c.shadow = ft.BoxShadow(
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.4, accent_color)
            ) if is_selected else ThemeManager.styles.get("shadow_sm")
            c.border = ft.Border.all(2, ft.Colors.with_opacity(0.8, accent_color)) if is_selected else None
            
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
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.4, ThemeManager.colors["accent"])) if is_selected else ThemeManager.styles.get("shadow_sm"),
        border=ft.Border.all(2, ft.Colors.with_opacity(0.8, ThemeManager.colors["accent"])) if is_selected else None,
        animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT_EXPO),
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        on_click=on_click_wrapper,
        on_hover=handle_hover
    )
