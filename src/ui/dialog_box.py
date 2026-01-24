"""Dialog system UI"""

import logging
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from panda3d.core import TextNode

logger = logging.getLogger(__name__)


class DialogBox:
    """Dialog box UI"""
    
    def __init__(self, base):
        """
        Initialize dialog box
        
        Args:
            base: ShowBase instance
        """
        self.base = base
        self.is_visible = False
        
        # Current dialog
        self.current_npc = None
        self.current_dialog = None
        self.on_close_callback = None
        self.option_buttons = []  # For choice dialogs
        
        # Create UI elements
        self._create_ui()
        self.hide()
        
        logger.info("DialogBox initialized")
    
    def _create_ui(self):
        """Create dialog UI elements"""
        # Get font with Cyrillic support if available
        font = None
        if hasattr(self.base, 'cyrillic_font') and self.base.cyrillic_font:
            font = self.base.cyrillic_font
        
        # Background frame (will be resized when showing options)
        self.frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-1.2, 1.2, -0.3, 0.3),
            pos=(0, 0, -0.4)  # Moved higher for better visibility of all buttons
        )
        
        # NPC name label
        self.name_label = DirectLabel(
            text="",
            text_scale=0.08,
            text_fg=(1, 1, 0, 1),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            pos=(-1.1, 0, 0.2),
            parent=self.frame,
            text_font=font
        )
        # Apply font to label text component
        if font:
            self._apply_font_to_label(self.name_label, font)
        
        # Dialog text label
        self.text_label = DirectLabel(
            text="",
            text_scale=0.06,
            text_fg=(1, 1, 1, 1),
            text_align=TextNode.ALeft,
            text_wordwrap=20,
            frameColor=(0, 0, 0, 0),
            pos=(-1.1, 0, 0.05),
            parent=self.frame,
            text_font=font
        )
        # Apply font to label text component
        if font:
            self._apply_font_to_label(self.text_label, font)
        
        # Continue button
        self.continue_btn = DirectButton(
            text="Continue [Space]",
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.3, 0.3, 0.3, 1),
            frameSize=(-0.3, 0.3, -0.05, 0.05),
            pos=(0.8, 0, -0.2),
            command=self.on_continue,
            parent=self.frame,
            text_font=font
        )
        # Apply font to button components
        if font:
            self._apply_font_to_button(self.continue_btn, font)
    
    def _apply_font_to_button(self, button, font):
        """Apply font to all text components of a button"""
        try:
            button['text_font'] = font
            # Try to get text component and set font directly
            for i in range(4):  # DirectButton has text0, text1, text2, text3
                text_comp = button.component(f'text{i}')
                if text_comp:
                    text_comp.setFont(font)
        except Exception as e:
            pass  # Silent fail
    
    def _apply_font_to_label(self, label, font):
        """Apply font to label text component"""
        try:
            label['text_font'] = font
            text_comp = label.component('text')
            if text_comp:
                text_comp.setFont(font)
        except Exception as e:
            pass  # Silent fail
    
    def show(self, npc, dialog: dict, on_close=None):
        """
        Show dialog
        
        Args:
            npc: NPC object (or None for system dialogs)
            dialog: Dialog dict with 'text' and optional 'options'
            on_close: Callback when dialog closes
        """
        # Clear previous options
        self._clear_options()
        
        self.current_npc = npc
        self.current_dialog = dialog
        self.on_close_callback = on_close
        
        # Update UI
        if npc:
            self.name_label['text'] = npc.name
        else:
            self.name_label['text'] = dialog.get('title', '')
        self.text_label['text'] = dialog['text']
        
        # Show options if available
        if dialog.get('options'):
            self._show_options(dialog['options'])
            self.continue_btn.hide()
        else:
            self.continue_btn.show()
        
        # Resize frame if needed - make it larger to fit all options
        if dialog.get('options'):
            num_options = len(dialog['options'])
            # Compact layout: start_y = -0.08, button_height = 0.06, spacing = 0.08
            # Last button position: start_y - (num_options-1) * (button_height + spacing)
            # Last button bottom: last_button_y - 0.03
            # Add margin: 0.1 below last button for safety
            button_height = 0.06
            spacing = 0.08
            start_y = -0.08
            last_button_y = start_y - ((num_options - 1) * (button_height + spacing))
            last_button_bottom = last_button_y - 0.03
            bottom = last_button_bottom - 0.15  # Extra margin below last button to ensure visibility
            # Make sure frame is large enough to show all buttons
            self.frame['frameSize'] = (-1.2, 1.2, bottom, 0.3)
            logger.info(f"Dialog frame resized for {num_options} options: bottom={bottom:.3f}, top=0.3, buttons from {start_y:.3f} to {last_button_y:.3f}")
        else:
            self.frame['frameSize'] = (-1.2, 1.2, -0.3, 0.3)
        
        # Show frame
        self.frame.show()
        self.is_visible = True
        
        logger.info(f"Dialog shown: {npc.name if npc else 'System'}")
    
    def _clear_options(self):
        """Clear option buttons"""
        for btn in self.option_buttons:
            btn.destroy()
        self.option_buttons.clear()
    
    def _show_options(self, options: list):
        """Show dialog options as buttons
        
        Args:
            options: List of (text, callback) tuples
        """
        font = None
        if hasattr(self.base, 'cyrillic_font') and self.base.cyrillic_font:
            font = self.base.cyrillic_font
        
        num_options = len(options)
        start_y = -0.08  # Start position for first button
        button_height = 0.06  # Height of each button
        spacing = 0.08  # Space between buttons (reduced for compact layout)
        
        logger.info(f"Creating {num_options} option buttons with compact layout")
        for i, (text, callback) in enumerate(options):
            # Calculate Y position: start from top, going down
            y_pos = start_y - (i * (button_height + spacing))
            
            # Create a wrapper function to capture the callback properly
            def make_callback(cb):
                return lambda: self._on_option_selected(cb)
            
            btn = DirectButton(
                text=text,
                text_scale=0.045,  # Slightly smaller text for compact layout
                text_fg=(1, 1, 1, 1),
                frameColor=(0.3, 0.3, 0.5, 1),
                frameSize=(-0.75, 0.75, -0.03, 0.03),  # Compact button size
                pos=(0, 0, y_pos),
                command=make_callback(callback),
                parent=self.frame,
                text_font=font,
                relief=1  # Raised relief for better visibility
            )
            if font:
                self._apply_font_to_button(btn, font)
            self.option_buttons.append(btn)
            logger.info(f"Created option button {i+1}/{num_options}: '{text}' at y={y_pos:.3f}")
    
    def _on_option_selected(self, callback):
        """Handle option selection"""
        logger.info(f"Option selected! Callback type: {type(callback)}, callback: {callback}")
        if callback:
            try:
                logger.info("Calling callback...")
                callback()
                logger.info("Callback executed successfully")
            except Exception as e:
                logger.error(f"Error in option callback: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("No callback provided!")
        self.hide()
    
    def hide(self):
        """Hide dialog"""
        self._clear_options()
        self.frame.hide()
        self.is_visible = False
        
        if self.on_close_callback:
            self.on_close_callback()
            self.on_close_callback = None
    
    def on_continue(self):
        """Handle continue button"""
        if self.current_npc:
            # Move to next dialog
            self.current_npc.next_dialog()
            next_dialog = self.current_npc.get_current_dialog()
            
            if next_dialog:
                self.show(self.current_npc, next_dialog, self.on_close_callback)
            else:
                # No more dialogs
                self.current_npc.reset_dialog()
                self.hide()
        else:
            self.hide()
    
    def cleanup(self):
        """Cleanup"""
        self.frame.destroy()
