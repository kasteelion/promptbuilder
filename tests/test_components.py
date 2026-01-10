import tkinter as tk
from unittest.mock import MagicMock, patch
from ui.components.toolbar import ToolbarComponent
from ui.components.status_bar import StatusBarComponent

def test_status_bar_logic():
    root = MagicMock()
    # Mock Label creation
    with patch('tkinter.Label') as MockLabel:
        sb = StatusBarComponent(root)
        label_instance = MockLabel.return_value
        
        sb.update_status("New Status")
        label_instance.config.assert_called_with(text="New Status")
        
        sb.apply_theme({"bg": "#000", "border": "#fff"})
        label_instance.config.assert_called_with(bg="#000", fg="#fff")

def test_toolbar_logic():
    root = MagicMock()
    callbacks = {
        "save_preset": MagicMock(),
        "undo": MagicMock()
    }
    
    with patch('tkinter.Button') as MockButton:
        # We need to mock Frame as well since it's used as parent
        with patch('tkinter.ttk.Frame'):
            tb = ToolbarComponent(root, callbacks)
            
            # Check buttons created
            assert len(tb.buttons) > 0
            
            # Verify callbacks passed correctly (checking first button for now)
            # This is a bit loose but confirms structural integrity
            assert MockButton.call_count >= 2
