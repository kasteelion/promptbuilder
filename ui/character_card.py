# -*- coding: utf-8 -*-
"""Visual character card widget with photo support."""

import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ui.widgets import ScrollableCanvas
from utils import logger

from .constants import CHARACTER_CARD_SIZE

# Optional PIL import for image handling
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.info("PIL/Pillow not available. Character photos will not be displayed.")
    logger.info("Install Pillow for photo support: pip install Pillow")


class CharacterCard(ttk.Frame):
    """A visual card showing character with photo, name, and quick actions."""
    
    def __init__(self, parent, character_name, character_data, data_loader, 
                 on_add_callback=None, on_photo_change=None, theme_colors=None):
        """Initialize character card.
        
        Args:
            parent: Parent widget
            character_name: Name of the character
            character_data: Character data dict
            data_loader: DataLoader instance
            on_add_callback: Function to call when adding character
            on_photo_change: Function to call when photo is changed
            theme_colors: Theme color dict
        """
        super().__init__(parent, style="Card.TFrame")
        
        self.character_name = character_name
        self.character_data = character_data
        self.data_loader = data_loader
        self.on_add_callback = on_add_callback
        self.on_photo_change = on_photo_change
        self.theme_colors = theme_colors or {}
        
        self.photo_image = None  # Keep reference to prevent GC
        
        self._build_ui()
        self._load_photo()
        
        # Add hover effect to card
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Handle mouse enter (hover)."""
        # Keep borderwidth constant to prevent jitter, just change relief
        self.configure(relief="solid")
    
    def _on_leave(self, event):
        """Handle mouse leave."""
        self.configure(relief="raised")
    
    def _build_ui(self):
        """Build the card UI."""
        self.configure(relief="raised", borderwidth=1, padding=6)
        
        # Photo frame at top
        photo_frame = ttk.Frame(self, style="Card.TFrame")
        photo_frame.pack(fill="x", pady=(0, 4))
        
        # Photo canvas with click to preview
        self.photo_canvas = tk.Canvas(
            photo_frame, 
            width=CHARACTER_CARD_SIZE, 
            height=CHARACTER_CARD_SIZE, 
            bg=self.theme_colors.get("text_bg", "#ffffff"),
            highlightthickness=1,
            highlightbackground=self.theme_colors.get("border", "#cccccc"),
            cursor="hand2"
        )
        self.photo_canvas.pack()
        
        # Click to preview photo (or change if no photo)
        self.photo_canvas.bind("<Button-1>", lambda e: self._on_photo_click())
        
        # Placeholder text
        center = CHARACTER_CARD_SIZE // 2
        self.placeholder_text = self.photo_canvas.create_text(
            center, center,
            text="📷\nClick to\nadd photo",
            fill=self.theme_colors.get("fg", "#666666"),
            font=("Segoe UI", 8),
            justify="center"
        )
        
        # Character name with wrapping
        name_label = ttk.Label(
            self, 
            text=self.character_name,
            font=("Segoe UI", 9, "bold"),
            wraplength=110,
            justify="center"
        )
        name_label.pack(pady=(0, 2))
        
        # Quick info - more compact
        appearance = self.character_data.get("appearance", "")
        # Get first line or first 45 chars
        quick_desc = appearance.split('\n')[0][:45]
        if len(appearance.split('\n')[0]) > 45:
            quick_desc += "..."
        
        desc_label = ttk.Label(
            self,
            text=quick_desc,
            font=("Segoe UI", 7),
            foreground="gray",
            wraplength=110,
            justify="center"
        )
        desc_label.pack(pady=(0, 6))
        
        # Button frame for compact layout
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x")
        
        # Add button - more compact
        add_btn = ttk.Button(
            btn_frame,
            text="➕ Add",
            command=self._on_add_clicked,
            width=7
        )
        add_btn.pack(side="left", expand=True, fill="x", padx=(0, 2))
        
        # Edit button
        edit_btn = ttk.Button(
            btn_frame,
            text="✏️ Edit",
            command=self._on_edit_clicked,
            width=7
        )
        edit_btn.pack(side="right", expand=True, fill="x", padx=(2, 0))
    
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
                    if messagebox.askyesno("Photo Missing", "The referenced photo file is missing. Would you like to select a replacement file?"):
                        self._change_photo()
                    return
            except Exception:
                # If anything goes wrong resolving the path, fall back to change flow
                self._change_photo()
                return

            # Show preview
            self._preview_photo()
        else:
            # Change/add photo
            self._change_photo()
    
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
            
            # Main frame
            main_frame = ttk.Frame(preview_window, padding=10)
            main_frame.pack(fill="both", expand=True)
            
            # Title
            title = ttk.Label(main_frame, text=self.character_name, font=("Segoe UI", 14, "bold"))
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
                canvas.create_image(img.width//2, img.height//2, image=photo_tk)
                canvas.image = photo_tk  # Keep reference
            else:
                # Show message if PIL not available
                msg_label = ttk.Label(main_frame, text="Install Pillow to preview photos:\npip install Pillow")
                msg_label.pack(pady=20)
            
            # Buttons frame
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill="x", pady=(10, 0))
            
            ttk.Button(btn_frame, text="Change Photo", command=lambda: [preview_window.destroy(), self._change_photo()]).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="Close", command=preview_window.destroy).pack(side="right", padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview photo:\n{str(e)}")
    
    def _on_edit_clicked(self):
        """Handle edit button click - open character editor."""
        from .character_creator import CharacterCreatorDialog
        
        root = self.winfo_toplevel()
        # Open character editor dialog with existing character data
        dialog = CharacterCreatorDialog(root, self.data_loader, None, edit_character=self.character_name)
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
            logger.warning(f"Photo path outside characters directory: {photo_path}")
            raise ValueError("Photo path must be within characters directory")
    
    def _load_photo(self):
        """Load character photo if exists."""
        photo_path = self.character_data.get("photo")
        if not photo_path:
            return
        
        # Try to load the image
        try:
            photo_file = self._sanitize_photo_path(photo_path)
            
            if photo_file.exists():
                self._display_photo(photo_file)
        except ValueError as e:
            from utils import logger
            logger.warning(f"Invalid photo path for {self.character_name}: {e}")
        except Exception as e:
            from utils import logger
            logger.error(f"Error loading photo for {self.character_name}: {e}")
    
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
                center, center,
                text="📷\nPIL not\ninstalled",
                fill=self.theme_colors.get("fg", "#666666"),
                font=("Segoe UI", 8),
                justify="center"
            )
            return
        
        try:
            # Validate path is safe
            safe_path = self._sanitize_photo_path(photo_path)
            # Load and resize image
            img = Image.open(safe_path)
            
            # Resize to fit while maintaining aspect ratio
            img.thumbnail((CHARACTER_CARD_SIZE, CHARACTER_CARD_SIZE), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(img)
            
            # Clear canvas
            self.photo_canvas.delete("all")
            
            # Center the image
            x = (CHARACTER_CARD_SIZE - img.width) // 2
            y = (CHARACTER_CARD_SIZE - img.height) // 2
            
            self.photo_canvas.create_image(
                x, y,
                image=self.photo_image,
                anchor="nw"
            )
            
        except Exception as e:
            from utils import logger
            logger.error(f"Error displaying photo: {e}")
            # Show error indicator
            self.photo_canvas.delete("all")
            center = CHARACTER_CARD_SIZE // 2
            self.photo_canvas.create_text(
                center, center,
                text="❌\nInvalid\nimage",
                fill="red",
                font=("Segoe UI", 8),
                justify="center"
            )
    
    def _change_photo(self):
        """Open file dialog to change character photo."""
        filepath = filedialog.askopenfilename(
            title=f"Select photo for {self.character_name}",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All files", "*.*")
            ]
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
            shutil.copy2(source, dest)
            
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
            messagebox.showerror(
                "Error",
                f"Failed to set photo:\n{str(e)}"
            )
    
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
                content = char_file.read_text(encoding='utf-8')
                
                if f"### {self.character_name}" in content:
                    # Add photo metadata after character name
                    lines = content.split('\n')
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
                    char_file.write_text('\n'.join(new_lines), encoding='utf-8')
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
    
    def __init__(self, parent, data_loader, on_add_callback, theme_colors=None):
        """Initialize character gallery.
        
        Args:
            parent: Parent widget
            data_loader: DataLoader instance
            on_add_callback: Function to call when adding character
            theme_colors: Theme color dict
        """
        super().__init__(parent, style="TFrame")
        
        self.data_loader = data_loader
        self.on_add_callback = on_add_callback
        self.theme_colors = theme_colors or {}
        self.characters = {}
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the gallery UI."""
        # Header with title and count
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=6, pady=(6, 2))
        
        self.title_label = ttk.Label(
            header,
            text="👥 Characters",
            font=("Segoe UI", 11, "bold")
        )
        self.title_label.pack(anchor="w")
        
        self.count_label = ttk.Label(
            header,
            text="0 characters",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        self.count_label.pack(anchor="w")
        
        # Search box with placeholder effect
        search_frame = ttk.Frame(self, style="TFrame")
        search_frame.pack(fill="x", padx=6, pady=(2, 6))
        
        self.search_var = tk.StringVar()
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill="x", ipady=2)
        search_entry.insert(0, "Search...")
        search_entry.config(foreground="gray")
        
        # Clear placeholder on focus
        def on_focus_in(e):
            if search_entry.get() == "Search...":
                search_entry.delete(0, tk.END)
                search_entry.config(foreground="black")
        
        def on_focus_out(e):
            if not search_entry.get():
                search_entry.insert(0, "Search...")
                search_entry.config(foreground="gray")
        
        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)
        
        # Use ScrollableCanvas for cards
        self.scrollable_canvas = ScrollableCanvas(self)
        self.scrollable_canvas.pack(fill="both", expand=True, padx=4, pady=4)
        
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
        self._display_characters()
    
    def _display_characters(self):
        """Display character cards."""
        # Clear existing cards
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        
        # Get search filter (ignore placeholder text)
        search_term = self.search_var.get().lower()
        if search_term == "search...":
            search_term = ""
        
        # Create cards
        row = 0
        col = 0
        max_cols = 1  # 1 card per row for better visibility in narrow panel
        displayed_count = 0
        
        for name, data in sorted(self.characters.items()):
            # Apply search filter
            if search_term and search_term not in name.lower():
                continue
            
            displayed_count += 1
            
            card = CharacterCard(
                self.cards_container,
                name,
                data,
                self.data_loader,
                on_add_callback=self.on_add_callback,
                theme_colors=self.theme_colors
            )
            card.grid(row=row, column=col, padx=4, pady=4, sticky="new")
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Configure column weights
        for c in range(max_cols):
            self.cards_container.columnconfigure(c, weight=1, uniform="card")
        
        # Update count label
        total = len(self.characters)
        if hasattr(self, 'count_label'):
            if search_term:
                self.count_label.config(text=f"{displayed_count} of {total} characters")
            else:
                self.count_label.config(text=f"{total} character{'s' if total != 1 else ''}")
        
        # Update scroll region and refresh mousewheel bindings after adding new content
        self.scrollable_canvas.refresh_mousewheel_bindings()
        self.after_idle(self.scrollable_canvas.update_scroll_region)
    
    def _filter_characters(self):
        """Filter characters based on search."""
        self._display_characters()
    
    def _refresh_display(self):
        """Refresh the display (used when theme changes)."""
        # Update canvas background
        self.scrollable_canvas.canvas.configure(bg=self.theme_colors.get("bg", "#f0f0f0"))
        # Redisplay all characters to update their theme colors
        self._display_characters()
