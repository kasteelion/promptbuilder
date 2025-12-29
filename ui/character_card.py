# -*- coding: utf-8 -*-
"""Visual character card widget with photo support."""

import shutil
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ui.widgets import FlowFrame, ScrollableCanvas
from utils import create_tooltip, logger

from .constants import CHARACTER_CARD_SIZE
from .searchable_combobox import SearchableCombobox

# Optional PIL import for image handling
try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.info("PIL/Pillow not available. Character photos will not be displayed.")
    logger.info("Install Pillow for photo support: pip install Pillow")

import threading

# Simple in-memory cache for resized/cropped PIL images keyed by (path, w, h)
_IMAGE_CACHE: dict = {}
# Shared executor for image loading to avoid thread explosion
_IMAGE_EXECUTOR = None


class CharacterCard(ttk.Frame):
    """A visual card showing character with photo, name, and quick actions with accordion behavior."""

    def __init__(
        self,
        parent,
        character_name,
        character_data,
        data_loader,
        prefs,
        theme_manager=None,
        on_add_callback=None,
        on_photo_change=None,
        on_tag_click=None,
        theme_colors=None,
        categorized_tags_map=None,
    ):
        """Initialize character card.

        Args:
            parent: Parent widget
            character_name: Name of the character
            character_data: Character data dict
            data_loader: DataLoader instance
            prefs: PreferencesManager instance
            theme_manager: Optional ThemeManager instance
            on_add_callback: Function to call when adding character
            on_photo_change: Function to call when photo is changed
            on_tag_click: Function to call when a tag is clicked
            theme_colors: Theme color dict
            categorized_tags_map: Map of categories to tags for sorting
        """
        super().__init__(parent, style="Card.TFrame")

        self.character_name = character_name
        self.character_data = character_data
        self.data_loader = data_loader
        self.prefs = prefs
        self.theme_manager = theme_manager
        self.on_add_callback = on_add_callback
        self.on_photo_change = on_photo_change
        self.on_tag_click = on_tag_click
        self.theme_colors = theme_colors or {}
        self.categorized_tags_map = categorized_tags_map or {}
        
        self.photo_image = None  # Keep reference to prevent GC
        self._expanded = True # Accordion state
        self.is_used = False # State for "Added" indicator

        self._build_ui()
        
        if self.theme_manager:
            self.theme_manager.register(self, self._update_theme_overrides)

    @classmethod
    def _get_executor(cls):
        global _IMAGE_EXECUTOR
        if _IMAGE_EXECUTOR is None:
            from concurrent.futures import ThreadPoolExecutor
            import os
            # Use number of cores or at least 4
            workers = min(32, (os.cpu_count() or 4) + 1)
            _IMAGE_EXECUTOR = ThreadPoolExecutor(max_workers=workers)
        return _IMAGE_EXECUTOR

    def set_used_state(self, is_used):
        """Update visual state to show if character is already in prompt."""
        if self.is_used == is_used:
            return
        self.is_used = is_used
        
        if is_used:
            # Show "Added" indicator
            if not hasattr(self, "used_label"):
                accent = self.theme_colors.get("accent", "#0078d7")
                self.used_label = tk.Label(
                    self.photo_canvas, 
                    text="✓", 
                    bg="#4caf50", # Keep green for success/added
                    fg="white", 
                    font=("Lexend", 10, "bold")
                )
                # Place in top-right corner of photo
                self.photo_canvas.create_window(
                    int(self.photo_canvas.cget("width")) - 12, 
                    12, 
                    window=self.used_label, 
                    anchor="center",
                    tags="used_indicator"
                )
            
            # Apply subtle highlight to card - Refactor 3
            self.configure(style="Selected.Card.TFrame")
        else:
            # Remove indicator
            self.photo_canvas.delete("used_indicator")
            if hasattr(self, "used_label"):
                self.used_label.destroy()
                del self.used_label
            
            # Restore normal style
            self.configure(style="Card.TFrame")

    def _on_enter(self, event):
        """Handle mouse enter (hover)."""
        self.configure(style="Selected.Card.TFrame" if self._expanded else "Card.TFrame")
        try:
            self.name_label.config(foreground=self.theme_colors.get("accent", "#0078d7"))
        except Exception:
            pass

    def _on_leave(self, event):
        """Handle mouse leave."""
        self.configure(style="Card.TFrame")
        try:
            self.name_label.config(foreground=self.theme_colors.get("fg", "white"))
        except Exception:
            pass

    def _build_ui(self):
        """Build the card UI with a vertical stacked layout. (Refactor 3)"""
        self.configure(relief="flat", borderwidth=0, padding=10)
        
        # Theme colors
        pbg = self.theme_colors.get("panel_bg", self.theme_colors.get("text_bg", "#1e1e1e"))
        fg = self.theme_colors.get("fg", "white")
        accent = self.theme_colors.get("accent", "#0078d7")
        border = self.theme_colors.get("border", self.theme_colors.get("bg", "#333333"))
        muted = "gray" # Default fallback for muted text

        # Main container (Vertical stack)
        container = ttk.Frame(self, style="TFrame")
        container.pack(fill="both", expand=True)

        # Photo frame on Top
        photo_size = int(CHARACTER_CARD_SIZE) # Use full increased base size (140px)
        self.photo_canvas = tk.Canvas(
            container,
            width=photo_size,
            height=photo_size,
            bg=pbg,
            highlightthickness=1,
            highlightbackground=border,
            cursor="hand2",
        )
        self.photo_canvas.pack(pady=(0, 10))
        self.photo_canvas.bind("<Button-1>", lambda e: self._on_photo_click())

        center = photo_size // 2
        self.placeholder_text = self.photo_canvas.create_text(
            center,
            center,
            text="📷",
            fill=fg,
            font=("Lexend", 14), 
            justify="center",
        )

        # Name Row (Centered)
        name_frame = ttk.Frame(container)
        name_frame.pack(fill="x")

        self.name_label = ttk.Label(
            name_frame,
            text=self.character_name,
            style="Bold.TLabel",
            wraplength=240,
            justify="center",
            anchor="center"
        )
        self.name_label.pack(fill="x")

        # Use explicit summary if present
        summary = self.character_data.get("summary")
        if not summary:
            appearance = self.character_data.get("appearance", "")
            first_line = appearance.split("\n")[0] if appearance else ""
            summary = (first_line[:120] + "...") if len(first_line) > 120 else first_line

        # Description (Centered, Wrapped)
        self.desc_label = ttk.Label(
            container,
            text=summary,
            style="Muted.TLabel", # Use themed muted style
            wraplength=240,
            justify="center",
            anchor="center"
        )
        self.desc_label.pack(pady=(4, 8), fill="x")

        # Tags display (Centered)
        raw_tags = self.character_data.get("tags") or []
        if isinstance(raw_tags, str):
            raw_tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
        
        tags = self._sort_tags_by_category(raw_tags, self.categorized_tags_map)

        if tags:
            # Show all tags (Refactor 3 Fix)
            tags_frame = FlowFrame(container, padding_x=2, padding_y=2)
            tags_frame.pack(pady=(0, 10), fill="x")
            
            for t in tags:
                pill = tk.Frame(tags_frame, bg=accent, padx=1, pady=1)
                lbl = tk.Label(
                    pill, 
                    text=t, 
                    bg=pbg, 
                    fg=accent,
                    font=("Lexend", 8, "bold"),
                    padx=10,
                    pady=4,
                    cursor="hand2"
                )
                lbl.pack()
                lbl.bind("<Button-1>", lambda e, v=t: self._handle_tag_click(v))
                tags_frame._children.append(pill)
            
            tags_frame._schedule_reflow()

        # Action Buttons (Pill Style)
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x")

        # Add button: Primary
        self.add_btn = ttk.Button(
            btn_frame, 
            text="➕ ADD", 
            command=self._on_add_clicked, 
            width=8,
            style="TButton"
        )
        self.add_btn.pack(side="left", expand=True, padx=2)

        # Edit button: Ghost
        self.edit_btn = tk.Button(
            btn_frame, 
            text="✏️", 
            command=self._on_edit_clicked, 
            width=3,
            bg=pbg,
            fg=accent,
            highlightbackground=accent,
            highlightthickness=2,
            relief="flat"
        )
        self.edit_btn.pack(side="left", padx=2)
        
        # Hover for edit
        def on_edit_enter(e): self.edit_btn.config(bg=self.theme_colors.get("hover_bg", self.theme_colors.get("selected_bg", "#333333")))
        def on_edit_leave(e): self.edit_btn.config(bg=self.theme_colors.get("panel_bg", self.theme_colors.get("bg", "#1e1e1e")))
        
        self.edit_btn.bind("<Enter>", on_edit_enter)
        self.edit_btn.bind("<Leave>", on_edit_leave)
        
        self.fav_btn_var = tk.StringVar()
        self.fav_btn = tk.Button(
            btn_frame, 
            textvariable=self.fav_btn_var,
            command=self._toggle_favorite,
            bg=self.theme_colors.get("panel_bg", self.theme_colors.get("bg", "#1e1e1e")),
            fg=self.theme_colors.get("accent", "#0078d7"),
            relief="flat",
            font=("Lexend", 11)
        )
        self.fav_btn.pack(side="right")
        
        def on_fav_enter(e): self.fav_btn.config(bg=self.theme_colors.get("hover_bg", self.theme_colors.get("selected_bg", "#333333")))
        def on_fav_leave(e): self.fav_btn.config(bg=self.theme_colors.get("panel_bg", pbg))
        self.fav_btn.bind("<Enter>", on_fav_enter)
        self.fav_btn.bind("<Leave>", on_fav_leave)
        
        self._update_fav_star()


    def toggle_visibility(self, event=None):
        """Toggle the visibility of the card contents. (Refactor 3)"""
        if self._expanded:
            self.container.pack_forget()
            self.toggle_indicator.config(text="▶")
            self._expanded = False
        else:
            self.container.pack(fill="both", expand=True)
            self.toggle_indicator.config(text="▼")
            self._expanded = True
        
        # Trigger parent scroll update
        try:
            self.master.master.master.scrollable_canvas.update_scroll_region()
        except Exception: pass

    def _sort_tags_by_category(self, tags, categorized_map):
        """Sort tags based on category priority."""
        if not categorized_map:
            return sorted(tags)
            
        priority = ["Demographics", "Body Type", "Style", "Vibe", "Other"]
        
        # Create a reverse map for lookup
        tag_to_cat = {}
        for cat, tag_list in categorized_map.items():
            for t in tag_list:
                tag_to_cat[t.lower()] = cat
        
        def sort_key(tag):
            cat = tag_to_cat.get(tag.lower(), "Other")
            try:
                return (priority.index(cat), tag.lower())
            except ValueError:
                return (len(priority), tag.lower())
                
        return sorted(tags, key=sort_key)

        edit_btn = ttk.Button(btn_frame, text="✏️ Edit", command=self._on_edit_clicked, width=10)
        edit_btn.pack(side="left")

    def _on_photo_click(self):
        """Handle photo canvas click - preview if photo exists, change if not."""
        photo_path = self.character_data.get("photo")
        if photo_path:
            # If a photo path is present, check whether the file actually exists.
            try:
                chars_dir = self.data_loader._find_characters_dir()
                photo_file = chars_dir / photo_path
                if not photo_file.exists():
                    # Photo metadata points to a missing file — prompt user to add one.
                    if messagebox.askyesno(
                        "Photo Missing",
                        "The referenced photo file is missing. Would you like to select a replacement file?",
                    ):
                        self._change_photo()
                    return
            except Exception:
                from utils import logger

                logger.exception("Auto-captured exception")
                # If anything goes wrong resolving the path, fall back to change flow
                self._change_photo()
                return

            # Show preview
            self._preview_photo()
        else:
            # Change/add photo
            self._change_photo()

    def _handle_tag_click(self, tag_value: str):
        """Handle tag button click: invoke callback if provided."""
        try:
            if self.on_tag_click:
                self.on_tag_click(tag_value)
        except Exception:
            from utils import logger

            logger.exception("Error in tag click handler")

    def _toggle_favorite(self):
        """Toggle favorite status of this character."""
        if self.prefs:
            self.prefs.toggle_favorite("favorite_characters", self.character_name)
            self._update_fav_star()
            # If the parent has a _display_characters method, refresh it if favorites-only is on
            try:
                # CharacterCard -> cards_container -> ScrollableCanvas -> CharacterGalleryPanel
                panel = self.master.master.master
                if hasattr(panel, "fav_only_var") and panel.fav_only_var.get():
                    panel._display_characters()
            except Exception:
                pass

    def _update_fav_star(self):
        """Update favorite star icon based on preference."""
        if self.prefs:
            is_fav = self.prefs.is_favorite("favorite_characters", self.character_name)
            self.fav_btn_var.set("★" if is_fav else "☆")
            
            accent = self.theme_colors.get("accent", "#0078d7")
            panel_bg = self.theme_colors.get("panel_bg", self.theme_colors.get("bg", "#1e1e1e"))
            
            if is_fav:
                # Primary style for favorite
                self.fav_btn.configure(bg=accent, fg="white")
            else:
                # Ghost style for non-favorite
                self.fav_btn.configure(bg=panel_bg, fg=accent)

    def _preview_photo(self):
        """Show full-size photo preview in a popup window."""
        photo_path = self.character_data.get("photo")
        if not photo_path:
            return

        try:
            # Find the photo file
            chars_dir = self.data_loader._find_characters_dir()
            photo_file = chars_dir / photo_path
            if not photo_file.exists():
                photo_file = Path(photo_path)

            if not photo_file.exists():
                messagebox.showwarning("Photo Not Found", "Could not find the photo file.")
                return

            # Create preview window
            preview_window = tk.Toplevel(self.winfo_toplevel())
            preview_window.title(f"{self.character_name} - Photo")
            preview_window.geometry("600x700")
            preview_window.transient(self.winfo_toplevel())

            # Apply basic top-level theme
            if self.theme_manager:
                self.theme_manager.theme_toplevel(preview_window)

            # Main frame
            main_frame = ttk.Frame(preview_window, padding=10)
            main_frame.pack(fill="both", expand=True)

            # Title
            title = ttk.Label(main_frame, text=self.character_name, style="Title.TLabel")
            title.pack(pady=(0, 10))

            if HAS_PIL:
                # Load and display image
                img = Image.open(photo_file)

                # Resize to fit window while maintaining aspect ratio
                max_size = (560, 560)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                photo_tk = ImageTk.PhotoImage(img)

                # Canvas for image
                canvas = tk.Canvas(main_frame, width=img.width, height=img.height, bg="white")
                canvas.pack(pady=(0, 10))
                canvas.create_image(img.width // 2, img.height // 2, image=photo_tk)
                canvas.image = photo_tk  # Keep reference
            else:
                # Show message if PIL not available
                msg_label = ttk.Label(
                    main_frame, text="Install Pillow to preview photos:\npip install Pillow"
                )
                msg_label.pack(pady=20)

            # Buttons frame
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill="x", pady=(10, 0))

            ttk.Button(
                btn_frame,
                text="Change Photo",
                command=lambda: [preview_window.destroy(), self._change_photo()],
            ).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="Close", command=preview_window.destroy).pack(
                side="right", padx=5
            )

        except Exception as e:
            from utils import logger

            logger.exception("Auto-captured exception")
            messagebox.showerror("Error", f"Failed to preview photo:\n{str(e)}")

    def _on_edit_clicked(self):
        """Handle edit button click - open character editor."""
        from .character_creator import CharacterCreatorDialog

        root = self.winfo_toplevel()
        # Open character editor dialog with existing character data
        dialog = CharacterCreatorDialog(
            root, self.data_loader, None, edit_character=self.character_name
        )
        dialog.show()

    def _sanitize_photo_path(self, photo_path):
        """Ensure photo path is within characters directory.

        Args:
            photo_path: Relative or absolute path to photo

        Returns:
            Path: Validated absolute path

        Raises:
            ValueError: If path is outside characters directory
        """
        from utils import logger

        chars_dir = self.data_loader._find_characters_dir().resolve()

        # Try relative path first
        full_path = (chars_dir / photo_path).resolve()

        # Check if it's within the characters directory
        try:
            full_path.relative_to(chars_dir)
            return full_path
        except ValueError:
            # Path is outside characters directory
            logger.exception(f"Photo path outside characters directory: {photo_path}")
            raise ValueError("Photo path must be within characters directory")

    def _load_photo(self):
        """Kick off async load of character photo if it exists.

        Image decoding and resizing is done in a background thread; final
        PhotoImage creation and canvas drawing happen on the main thread.
        """
        photo_path = self.character_data.get("photo")
        if not photo_path:
            return

        try:
            photo_file = self._sanitize_photo_path(photo_path)
        except ValueError as e:
            logger.warning(f"Invalid photo path for {self.character_name}: {e}", exc_info=True)
            return

        if not photo_file.exists():
            return

        # Determine target canvas size
        try:
            canvas_w = int(self.photo_canvas.cget("width"))
            canvas_h = int(self.photo_canvas.cget("height"))
        except Exception:
            canvas_w = CHARACTER_CARD_SIZE
            canvas_h = CHARACTER_CARD_SIZE

        key = (str(photo_file.resolve()), canvas_w, canvas_h)
        if key in _IMAGE_CACHE:
            pil_img = _IMAGE_CACHE[key]
            # Display immediately on main thread
            self._display_photo_from_image(pil_img)
            return

        # Background loader
        def _bg_load(path, w, h, widget_ref):
            try:
                # Early check: if widget is gone, don't bother
                try:
                    if not widget_ref.winfo_exists():
                        return
                except Exception:
                    return

                img = Image.open(path).convert("RGBA")

                # Cover-resize: scale to fill the canvas and crop center
                scale = max(w / img.width, h / img.height)
                new_size = (int(img.width * scale) + 2, int(img.height * scale) + 2)
                
                # Performance: Use BILINEAR for thumbnails instead of LANCZOS (much faster)
                img = img.resize(new_size, Image.Resampling.BILINEAR)

                left = (img.width - w) // 2
                top = (img.height - h) // 2
                right = left + w
                bottom = top + h
                img = img.crop((left, top, right, bottom))

                # Cache the processed PIL image
                _IMAGE_CACHE[(str(path.resolve()), w, h)] = img

                # Schedule UI update on main thread
                try:
                    if widget_ref.winfo_exists():
                        widget_ref.after(0, lambda: widget_ref._display_photo_from_image(img))
                except Exception:
                    pass
            except Exception:
                # Silently fail background load if widget is gone or file is invalid
                pass

        # Submit to shared thread pool
        self._get_executor().submit(_bg_load, photo_file, canvas_w, canvas_h, self)

    def _display_photo(self, photo_path):
        """Display a photo in the canvas.

        Args:
            photo_path: Path to photo file
        """
        if not HAS_PIL:
            # Show placeholder if PIL not available
            self.photo_canvas.delete("all")
            center = CHARACTER_CARD_SIZE // 2
            self.photo_canvas.create_text(
                center,
                center,
                text="📷\nPIL not\ninstalled",
                fill=self.theme_colors.get("fg", "#666666"),
                font=("Lexend", 8),
                justify="center",
            )
            return

        try:
            # If caller passed a PIL Image already, display directly
            if hasattr(photo_path, "convert") and hasattr(photo_path, "size"):
                self._display_photo_from_image(photo_path)
                return

            # Otherwise sanitize and delegate to async loader (to avoid blocking UI)
            photo_file = self._sanitize_photo_path(photo_path)
            # Kick off async load (will use cache if available)
            self._load_photo()

        except Exception as e:
            from utils import logger

            logger.error(f"Error displaying photo: {e}")
            # Show error indicator
            self.photo_canvas.delete("all")
            center = CHARACTER_CARD_SIZE // 2
            self.photo_canvas.create_text(
                center,
                center,
                text="❌\nInvalid\nimage",
                fill="red",
                font=("Lexend", 8),
                justify="center",
            )

    def _display_photo_from_image(self, pil_img):
        """Create a PhotoImage from a PIL Image and draw it on the canvas.

        This must be called on the main/UI thread.
        """
        try:
            if not self.winfo_exists():
                return
            if not hasattr(self, "photo_canvas") or not self.photo_canvas.winfo_exists():
                return

            self.photo_image = ImageTk.PhotoImage(pil_img)
            self.photo_canvas.delete("all")
            self.photo_canvas.create_image(0, 0, image=self.photo_image, anchor="nw")
        except tk.TclError:
            # Widget likely destroyed
            pass
        except Exception:
            logger.exception("Failed to create PhotoImage from PIL image")

    def _change_photo(self):
        """Open file dialog to change character photo."""
        filepath = filedialog.askopenfilename(
            title=f"Select photo for {self.character_name}",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"), ("All files", "*.*")],
        )

        if not filepath:
            return

        # Copy to characters folder
        try:
            chars_dir = self.data_loader._find_characters_dir()
            chars_dir.mkdir(parents=True, exist_ok=True)

            source = Path(filepath)
            # Create safe filename
            safe_name = self.character_name.lower().replace(" ", "_")
            safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
            dest = chars_dir / f"{safe_name}_photo{source.suffix}"

            # Copy file
            try:
                shutil.copy2(source, dest)
            except PermissionError:
                # Destination file may be locked by another process (preview open).
                # Try a unique filename fallback (timestamp) to avoid overwrite conflicts.
                import time

                ts = int(time.time())
                dest = chars_dir / f"{safe_name}_photo_{ts}{source.suffix}"
                try:
                    shutil.copy2(source, dest)
                except Exception:
                    from utils import logger

                    logger.exception("Auto-captured exception")
                    raise

            # Update character data
            relative_path = dest.name
            self.character_data["photo"] = relative_path

            # Update the character file
            self._update_character_file(relative_path)

            # Display the photo
            self._display_photo(dest)

            # Callback
            if self.on_photo_change:
                self.on_photo_change(self.character_name, relative_path)

        except Exception as e:
            from utils import logger

            logger.exception("Auto-captured exception")
            messagebox.showerror("Error", f"Failed to set photo:\n{str(e)}")

    def _update_character_file(self, photo_path):
        """Update character markdown file with photo path.

        Args:
            photo_path: Relative path to photo
        """
        try:
            # Find character file
            chars_dir = self.data_loader._find_characters_dir()
            char_files = list(chars_dir.glob("*.md"))

            # Find the file containing this character
            for char_file in char_files:
                content = char_file.read_text(encoding="utf-8")

                if f"### {self.character_name}" in content:
                    # Add photo metadata after character name
                    lines = content.split("\n")
                    new_lines = []
                    skip_next = False

                    for i, line in enumerate(lines):
                        if skip_next:
                            skip_next = False
                            continue

                        new_lines.append(line)

                        # Add photo line after character heading
                        if line.strip() == f"### {self.character_name}":
                            # Check if photo line already exists
                            if i + 1 < len(lines) and lines[i + 1].startswith("**Photo:**"):
                                # Replace existing photo line
                                new_lines.append(f"**Photo:** {photo_path}")
                                skip_next = True
                            else:
                                # Add new photo line
                                new_lines.append(f"**Photo:** {photo_path}")

                    # Write back
                    char_file.write_text("\n".join(new_lines), encoding="utf-8")
                    break

        except Exception as e:
            from utils import logger

            logger.error(f"Error updating character file: {e}")

    def _on_add_clicked(self):
        """Handle add button click."""
        if self.on_add_callback:
            self.on_add_callback(self.character_name)


class CharacterGalleryPanel(ttk.Frame):
    """Side panel showing character cards in a scrollable gallery."""

    def __init__(self, parent, data_loader, prefs, on_add_callback, theme_manager=None, theme_colors=None):
        """Initialize character gallery.

        Args:
            parent: Parent widget
            data_loader: DataLoader instance
            prefs: PreferencesManager instance
            on_add_callback: Function to call when adding character
            theme_manager: Optional ThemeManager instance
            theme_colors: Theme color dict
        """
        super().__init__(parent, style="TFrame")

        self.data_loader = data_loader
        self.prefs = prefs
        self.on_add_callback = on_add_callback
        self.theme_manager = theme_manager
        self.theme_colors = theme_colors or {}
        self.characters = {}
        self.load_queue = []  # Queue for lazy loading images
        self._render_job_id = None # ID for cancelling pending render batches
        self._search_after_id = None # ID for debouncing search
        self._current_filtered_chars = [] # List of currently filtered character names
        
        # Load categorized tags map for sorting logic
        try:
            self.categorized_tags_map = self.data_loader.load_categorized_tags()
        except Exception:
            self.categorized_tags_map = {}

        self._build_ui()
        
        if self.theme_manager:
            self.theme_manager.register(self, self._refresh_display)

    def _build_ui(self):
        """Build the gallery UI."""
        # Header with title, count, and random button - Refactor 1
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=12, pady=(15, 5))

        # Title and Count in a sub-frame
        title_frame = ttk.Frame(header, style="TFrame")
        title_frame.pack(side="left", fill="x", expand=True)

        # Refactor 5: Semantic Typography (UPPERCASE)
        self.title_label = ttk.Label(title_frame, text="👥 CHARACTERS", style="Title.TLabel")
        self.title_label.pack(anchor="w")

        self.count_label = ttk.Label(
            title_frame, text="0 characters", style="Muted.TLabel"
        )
        self.count_label.pack(anchor="w")

        # Random button on the right of header
        self.random_btn = ttk.Button(
            header, text="🎲", width=3, command=self._add_random_character, style="Ghost.TButton"
        )
        self.random_btn.pack(side="right", padx=(2, 0))
        create_tooltip(self.random_btn, "Add a random character from the current list")

        # Search box with placeholder effect
        search_frame = ttk.Frame(self, style="TFrame")
        search_frame.pack(fill="x", padx=15, pady=(5, 15))

        self.search_var = tk.StringVar()

        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, style="TEntry")
        self.search_entry.pack(fill="x", ipady=2)
        self.search_entry.insert(0, "SEARCH...")
        
        # Clear search button (X)
        self.search_clear_btn = tk.Label(
            search_frame, text="✕", font=("Arial", 8), 
            fg="gray", cursor="hand2", bg=self.theme_colors.get("text_bg", "#1e1e1e")
        )
        self.search_clear_btn.bind("<Button-1>", lambda e: self._clear_search())
        
        def _on_search_key(e=None):
            if self.search_var.get() and self.search_var.get() != "SEARCH...":
                self.search_clear_btn.place(relx=1.0, rely=0.5, x=-25, anchor="e")
            else:
                self.search_clear_btn.place_forget()
        
        self.search_var.trace_add("write", lambda *args: _on_search_key())

        # Selected tags area (chips) shown under the search box
        def on_focus_in(e):
            if self.search_entry.get() == "SEARCH...":
                self.search_entry.delete(0, tk.END)

        def on_focus_out(e):
            if not self.search_entry.get():
                self.search_entry.insert(0, "SEARCH...")

        self.search_entry.bind("<FocusIn>", on_focus_in)
        self.search_entry.bind("<FocusOut>", on_focus_out)

        # Sort and Filter row - Refactor 5 (Initialized early to avoid AttributeError)
        sort_filter_frame = ttk.Frame(self, style="TFrame")
        sort_filter_frame.pack(fill="x", padx=15, pady=(0, 15))

        ttk.Label(sort_filter_frame, text="SORT:", style="Muted.TLabel").pack(side="left")
        self.sort_var = tk.StringVar(value="Name")
        sort_combo = ttk.Combobox(
            sort_filter_frame,
            textvariable=self.sort_var,
            state="readonly",
            width=8,
            values=["Name", "Modifier", "Recently Added"],
            font=("Lexend", 8)
        )
        sort_combo.pack(side="left", padx=(6, 10))
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self._display_characters())

        # Refactor 6: Component Semantics (Pill Strategy for Filter)
        self.fav_only_var = tk.BooleanVar(value=False)
        
        try:
            style = ttk.Style()
            pbg = style.lookup("TFrame", "background")
            accent = style.lookup("Tag.TLabel", "bordercolor") or "#0078d7"
        except:
            pbg = "#1e1e1e"
            accent = "#0078d7"

        self.fav_pill_frame = tk.Frame(sort_filter_frame, bg=accent, padx=1, pady=1)
        self.fav_pill_frame.pack(side="left")
        
        self.fav_pill_lbl = tk.Label(
            self.fav_pill_frame, 
            text="☆", 
            bg=pbg, 
            fg=accent,
            font=("Lexend", 10, "bold"),
            padx=8,
            pady=1,
            cursor="hand2"
        )
        self.fav_pill_lbl.pack()
        self.fav_pill_lbl._base_bg = pbg

        def toggle_fav_filter(e=None):
            new_state = not self.fav_only_var.get()
            self.fav_only_var.set(new_state)
            self.fav_pill_lbl.config(text="★" if new_state else "☆")
            self._display_characters()

        def on_f_enter(e):
            hbg = self.theme_colors.get("hover_bg", "#333333")
            self.fav_pill_lbl.config(bg=hbg)
        def on_f_leave(e):
            self.fav_pill_lbl.config(bg=getattr(self.fav_pill_lbl, "_base_bg", "#1e1e1e"))

        self.fav_pill_lbl.bind("<Button-1>", toggle_fav_filter)
        self.fav_pill_lbl.bind("<Enter>", on_f_enter)
        self.fav_pill_lbl.bind("<Leave>", on_f_leave)
        
        create_tooltip(self.fav_pill_lbl, "Show Favorites Only")

        # Selected tags area (chips) shown under the search box
        self.selected_tags = []
        self.selected_tags_frame = FlowFrame(self, padding_x=8, padding_y=6)
        self.selected_tags_frame.pack(fill="x", padx=12, pady=(0, 10))
        # initially empty
        self._render_selected_tags()

        # Tag filter section
        tag_frame = ttk.Frame(self, style="TFrame")
        tag_frame.pack(fill="x", padx=12, pady=(0, 10))
        tag_frame.columnconfigure(1, weight=1)
        tag_frame.columnconfigure(3, weight=1)

        ttk.Label(tag_frame, text="Cat:", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.tag_category_var = tk.StringVar(value="All")
        self.tag_cat_combo = SearchableCombobox(
            tag_frame,
            textvariable=self.tag_category_var,
            on_select=lambda val: self._update_tag_list(),
            placeholder="Category...",
            width=10
        )
        self.tag_cat_combo.grid(row=0, column=1, sticky="ew", padx=(2, 4))

        ttk.Label(tag_frame, text="Tag:", style="Muted.TLabel").grid(row=0, column=2, sticky="w")
        self.tag_var = tk.StringVar()
        self.tag_combo = SearchableCombobox(
            tag_frame,
            textvariable=self.tag_var,
            on_select=self._add_selected_tag,
            placeholder="Search tag...",
            width=12
        )
        self.tag_combo.grid(row=0, column=3, sticky="ew", padx=(2, 4))

        self.clear_tags_btn = ttk.Button(tag_frame, text="✕", width=3, command=self._clear_tag_filter)
        self.clear_tags_btn.grid(row=0, column=4)
        create_tooltip(self.clear_tags_btn, "Clear tag filters")

        # Use ScrollableCanvas for cards
        self.scrollable_canvas = ScrollableCanvas(self)
        self.scrollable_canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # Forward mousewheel events from the selected-tags area to the scrollable canvas
        try:

            def _forward_wheel(e):
                try:
                    self.scrollable_canvas.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
                    return "break"
                except Exception:
                    return None

            self.selected_tags_frame.bind("<MouseWheel>", _forward_wheel)
            # Also bind to any dynamically added children inside the flow frame
            self.selected_tags_frame.bind(
                "<Enter>", lambda e: self.selected_tags_frame.bind("<MouseWheel>", _forward_wheel)
            )
        except Exception:
            pass

        # Get container for cards
        self.cards_container = self.scrollable_canvas.get_container()

        # Set up search trace after UI is built
        self.search_var.trace_add("write", lambda *args: self._filter_characters())

    def load_characters(self, characters):
        """Load and display character cards.

        Args:
            characters: Dict of character data
        """
        self.characters = characters
        
        # Refresh categorized map
        try:
            self.categorized_tags_map = self.data_loader.load_categorized_tags()
        except Exception:
            pass

        # Populate category selector
        categories = ["All"] + sorted(list(self.categorized_tags_map.keys()))
        self.tag_cat_combo.set_values(categories)
        
        # Initialize tag list
        self._update_tag_list()

        self._display_characters()

    def _update_tag_list(self):
        """Update the tag selector based on selected category and character usage."""
        try:
            cat = self.tag_category_var.get()
            
            # Find all tags used by current character set
            used = set()
            for _, data in (self.characters or {}).items():
                char_tags = data.get("tags") or []
                if isinstance(char_tags, str):
                    char_tags = [t.strip().lower() for t in char_tags.split(",") if t.strip()]
                for t in char_tags:
                    if t:
                        used.add(t)

            if cat == "All":
                # Show all used tags, sorted by priority
                priority = ["Demographics", "Body Type", "Style", "Vibe", "Other"]
                tag_to_cat = {}
                for c, tag_list in self.categorized_tags_map.items():
                    for t in tag_list:
                        tag_to_cat[t.lower()] = c
                
                def sort_key(tag):
                    c = tag_to_cat.get(tag.lower(), "Other")
                    try:
                        return (priority.index(c), tag.lower())
                    except ValueError:
                        return (len(priority), tag.lower())

                tag_values = sorted(list(used), key=sort_key)
            else:
                # Show only tags in selected category that are actually used
                cat_tags = set([t.lower() for t in self.categorized_tags_map.get(cat, [])])
                tag_values = sorted(list(used & cat_tags))

            self.tag_combo.set_values(tag_values)
            self.tag_var.set("") # Clear current selection in entry
            
        except Exception:
            from utils import logger
            logger.exception("Failed to update tag list")

    def update_used_status(self, used_names):
        """Update the used status for all visible cards."""
        used_set = set(used_names)
        for widget in self.cards_container.winfo_children():
            if isinstance(widget, CharacterCard):
                is_used = widget.character_name in used_set
                widget.set_used_state(is_used)

    def _clear_search(self):
        """Clear search entry."""
        self.search_var.set("")
        if self.focus_get() != self.search_entry:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, "SEARCH...")
        if hasattr(self, "search_clear_btn"):
            self.search_clear_btn.place_forget()
        self._display_characters()

    def _display_characters(self):
        """Display character cards using incremental rendering."""
        # Cancel any pending render job
        if self._render_job_id:
            try:
                self.after_cancel(self._render_job_id)
            except Exception:
                pass
            self._render_job_id = None

        # Clear existing cards
        for widget in self.cards_container.winfo_children():
            widget.destroy()

        # Reset load queue
        self.load_queue = []

        # Get search filter (ignore placeholder text)
        search_term = self.search_var.get().lower()
        if search_term == "search...":
            search_term = ""

        # Prepare character list for sorting
        char_list = []
        
        # Get favorites list from preferences
        favs = self.prefs.get("favorite_characters", [])
        fav_only = self.fav_only_var.get()

        for name, data in self.characters.items():
            # Apply favorite filter
            is_fav = name in favs
            if fav_only and not is_fav:
                continue

            # Apply search filter (Name, Summary, Appearance, Tags)
            if search_term:
                summary = (data.get("summary") or "").lower()
                appearance = (data.get("appearance") or "").lower()
                modifier = (data.get("modifier") or data.get("gender") or "").lower()
                tags = " ".join(data.get("tags") or []).lower()
                
                matches = (
                    search_term in name.lower() or
                    search_term in summary or
                    search_term in appearance or
                    search_term in modifier or
                    search_term in tags
                )
                if not matches:
                    continue

            # Apply tag filters (AND logic)
            if self.selected_tags:
                char_tags = data.get("tags") or []
                if isinstance(char_tags, str):
                    char_tags = [t.strip() for t in char_tags.split(",") if t.strip()]
                missing = [t for t in self.selected_tags if t not in char_tags]
                if missing:
                    continue
            
            char_list.append((name, data))

        # Store filtered names for random selection
        self._current_filtered_chars = [c[0] for c in char_list]

        # Apply sorting
        sort_by = self.sort_var.get()
        if sort_by == "Name":
            char_list.sort(key=lambda x: x[0].lower())
        elif sort_by == "Modifier":
            # Sort by modifier (fallback to gender) then name
            char_list.sort(key=lambda x: (x[1].get("modifier") or x[1].get("gender", "F"), x[0].lower()))
        elif sort_by == "Recently Added":
            # For now, we don't have true 'date added', so just reverse order
            # which usually matches file discovery order if not sorted.
            char_list.reverse()

        # Update count label
        total = len(self.characters)
        if hasattr(self, "count_label"):
            if search_term or fav_only or self.selected_tags:
                self.count_label.config(text=f"{len(char_list)} of {total} characters")
            else:
                self.count_label.config(text=f"{total} character{'s' if total != 1 else ''}")

        # Start incremental rendering
        # State: (row, col)
        self._render_cards_batch(char_list, 0, 0, 0)

    def _render_cards_batch(self, char_list, start_index, row, col):
        """Render a batch of character cards."""
        BATCH_SIZE = 12 # Slightly larger batch for modern CPUs
        max_cols = 1    # Reverted to 1 column
        
        end_index = min(start_index + BATCH_SIZE, len(char_list))
        
        for i in range(start_index, end_index):
            name, data = char_list[i]
            
            card = CharacterCard(
                self.cards_container,
                name,
                data,
                self.data_loader,
                self.prefs,
                on_add_callback=self.on_add_callback,
                on_tag_click=self._on_tag_selected_from_card,
                theme_colors=self.theme_colors,
                categorized_tags_map=self.categorized_tags_map,
            )
            # wire tag click to set the gallery filter
            try:
                card.on_tag_click = lambda v, panel=self: panel._on_tag_selected_from_card(v)
            except Exception:
                pass
            
            card.grid(row=row, column=col, padx=4, pady=4, sticky="new")
            
            # Add to queue for lazy loading
            self.load_queue.append(card)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Configure column weights (only need to do once really, but safe here)
        for c in range(max_cols):
            self.cards_container.columnconfigure(c, weight=1, uniform="card")

        # If more items remain, schedule next batch
        if end_index < len(char_list):
            self._render_job_id = self.after(
                5, # Smaller delay for faster perceived speed
                lambda: self._render_cards_batch(char_list, end_index, row, col)
            )
        else:
            # Done rendering
            self._render_job_id = None
            self._finalize_rendering(row, max_cols)

        # Process load queue more aggressively during initial render
        self._process_load_queue()

    def _finalize_rendering(self, final_row, max_cols):
        """Finalize rendering: add spacer and update scroll region."""
        try:
            # Rebind mousewheel events
            self.scrollable_canvas.refresh_mousewheel_bindings()

            # Add spacer
            try:
                spacer = ttk.Frame(self.cards_container, height=48)
                spacer.grid(row=final_row, column=0, columnspan=max_cols, sticky="ew")
                try:
                    spacer.grid_propagate(False)
                except Exception:
                    pass
            except Exception:
                pass

            # Update scroll region
            self.scrollable_canvas.update_scroll_region()
        except Exception:
            from utils import logger
            logger.exception("Failed to finalize rendering")

    def _add_random_character(self):
        """Pick a random character from the current filtered list and add it."""
        if not self._current_filtered_chars:
            from utils.notification import notify
            notify(self.winfo_toplevel(), "No Characters", "No characters available in the current list.", level="warning")
            return

        name = random.choice(self._current_filtered_chars)
        
        if self.on_add_callback:
            self.on_add_callback(name)
            
            # Show status feedback
            root = self.winfo_toplevel()
            if hasattr(root, "_update_status"):
                root._update_status(f"Added random character: {name}")

    def _process_load_queue(self):
        """Process the image loading queue in batches."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        if not self.load_queue:
            return

        # Process a small batch to keep UI responsive
        batch_size = 4
        processed = 0
        
        while processed < batch_size and self.load_queue:
            card = self.load_queue.pop(0)
            
            # Check if card still exists (widget might be destroyed if filter changed)
            try:
                if card.winfo_exists():
                    # Trigger the threaded loader
                    card._load_photo()
                    processed += 1
            except Exception:
                # Widget likely destroyed
                pass
        
        # Schedule next batch if items remain
        if self.load_queue:
            try:
                self.after(20, self._process_load_queue)
            except Exception:
                pass

    def _on_tag_selected_from_card(self, tag_value: str):
        """Handle tag click from a card: set tag combobox and refresh display."""
        try:
            # Add the tag to selected chips (this will refresh display)
            self._add_selected_tag(tag_value)
        except Exception:
            from utils import logger

            logger.exception("Error handling tag selection from card")

        # Update scroll region and refresh mousewheel bindings after adding new content
        self.scrollable_canvas.refresh_mousewheel_bindings()
        self.after_idle(self.scrollable_canvas.update_scroll_region)

    def _filter_characters(self):
        """Filter characters based on search with debouncing."""
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        
        # Debounce for 250ms to avoid re-rendering gallery while typing
        self._search_after_id = self.after(250, self._display_characters)

    def _render_selected_tags(self):
        """Render the selected tag chips in the selected_tags_frame."""
        # Clear existing via FlowFrame helper
        try:
            self.selected_tags_frame.clear()
        except Exception:
            # Fallback to destroying children
            for w in self.selected_tags_frame.winfo_children():
                w.destroy()

        if not self.selected_tags:
            return

        for t in self.selected_tags:
            # Render selected tag as a chip-like button with a close action so FlowFrame can reflow
            try:
                # Use the flow frame to create a button which will be managed by its reflow logic
                btn = self.selected_tags_frame.add_button(
                    text=f"{t} ✕",
                    style="Accent.TButton",
                    command=lambda v=t: self._remove_selected_tag(v),
                )
            except Exception:
                # Last-resort: create a standard button and append to _children for reflow
                btn = ttk.Button(
                    self.selected_tags_frame,
                    text=f"{t} ✕",
                    command=lambda v=t: self._remove_selected_tag(v),
                )
                btn.grid(row=0, column=len(getattr(self.selected_tags_frame, "_children", [])))
                if not hasattr(self.selected_tags_frame, "_children"):
                    self.selected_tags_frame._children = []
                self.selected_tags_frame._children.append(btn)

    def _add_selected_tag(self, tag_value: str):
        """Add a tag to the selected tags list and refresh."""
        if not tag_value:
            return
            
        if tag_value not in self.selected_tags:
            self.selected_tags.append(tag_value)
            self._render_selected_tags()
            self._display_characters()
            
        # Reset tag selector for next addition
        self.tag_var.set("")

    def _remove_selected_tag(self, tag_value: str):
        """Remove a tag from the selected tags list and refresh."""
        try:
            if tag_value in self.selected_tags:
                self.selected_tags.remove(tag_value)
                self._render_selected_tags()
                self._display_characters()
        except Exception:
            from utils import logger
            logger.exception("Error removing selected tag")

    def _clear_tag_filter(self):
        """Clear all tag filters and refresh display."""
        try:
            self.tag_category_var.set("All")
            self.tag_var.set("")
            self.selected_tags = []
            self._render_selected_tags()
            self._update_tag_list()
            self._display_characters()
        except Exception:
            from utils import logger
            logger.exception("Error clearing tag filters")

    def _refresh_display(self, theme=None):
        """Refresh the display (used when theme changes)."""
        if theme:
            self.theme_colors = theme
            
        # Update canvas background
        bg = self.theme_colors.get("bg", "#121212")
        self.scrollable_canvas.canvas.configure(bg=bg)
        
        # Update fav pill
        if hasattr(self, "fav_pill_frame"):
            accent = self.theme_colors.get("accent", "#0078d7")
            pbg = self.theme_colors.get("panel_bg", self.theme_colors.get("text_bg", "#1e1e1e"))
            self.fav_pill_frame.config(bg=accent)
            self.fav_pill_lbl.config(bg=pbg, fg=accent)
            self.fav_pill_lbl._base_bg = pbg

        # Redisplay all characters to update their theme colors
        self._display_characters()
        
        # After redisplay, we need to sync used status (Refactor 3)
        try:
            app = self.winfo_toplevel()
            if hasattr(app, "characters_tab"):
                selected_names = [c["name"] for c in app.characters_tab.get_selected_characters()]
                self.update_used_status(selected_names)
        except: pass
