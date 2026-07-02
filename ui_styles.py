"""
UI Styles Module for AI Studio Download Manager
Kivy-based styling and theming
"""

from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivy.core.window import Window


class ColorPalette:
    """App color palette"""

    # Primary colors
    PRIMARY = '#2196F3'
    PRIMARY_DARK = '#1976D2'
    PRIMARY_LIGHT = '#BBDEFB'

    # Secondary colors
    SECONDARY = '#FF4081'
    SECONDARY_DARK = '#C51162'

    # Accent colors
    ACCENT = '#FF5722'

    # Status colors
    SUCCESS = '#4CAF50'
    WARNING = '#FFC107'
    ERROR = '#F44336'
    INFO = '#2196F3'

    # Semantic colors
    BACKGROUND = '#FFFFFF'
    BACKGROUND_DARK = '#F5F5F5'
    SURFACE = '#FFFFFF'
    CARD = '#FFFFFF'

    # Text colors
    TEXT_PRIMARY = '#212121'
    TEXT_SECONDARY = '#757575'
    TEXT_DISABLED = '#BDBDBD'
    TEXT_LIGHT = '#FFFFFF'

    # Border colors
    BORDER = '#BDBDBD'
    BORDER_LIGHT = '#E0E0E0'
    BORDER_DARK = '#9E9E9E'

    # Download status colors
    STATUS_NEW = '#2196F3'
    STATUS_DOWNLOADING = '#4CAF50'
    STATUS_PAUSED = '#FFC107'
    STATUS_COMPLETED = '#4CAF50'
    STATUS_FAILED = '#F44336'
    STATUS_CANCELLED = '#9E9E9E'


class AppStyles:
    """Application styles and theming"""

    # Color references
    colors = ColorPalette

    # Font sizes
    FONT_SMALL = dp(11)
    FONT_BODY = dp(14)
    FONT_SUBTITLE = dp(16)
    FONT_TITLE = dp(20)
    FONT_HEADLINE = dp(24)

    # Spacing
    SPACING_XS = dp(4)
    SPACING_SM = dp(8)
    SPACING_MD = dp(16)
    SPACING_LG = dp(24)
    SPACING_XL = dp(32)

    # Border radius
    RADIUS_SM = dp(4)
    RADIUS_MD = dp(8)
    RADIUS_LG = dp(12)
    RADIUS_ROUND = dp(24)

    @staticmethod
    def apply(app: App):
        """Apply styles to the application"""
        # Set window background
        Window.clearcolor = AppStyles.hex_to_rgba(ColorPalette.BACKGROUND)

        # Try to set status bar color on Android
        try:
            from android.runnable import run_on_ui_thread
            from jnius import autoclass
            Color = autoclass('android.graphics.Color')
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity

            @run_on_ui_thread
            def set_status_bar():
                if mActivity.getWindow():
                    mActivity.getWindow().setStatusBarColor(
                        Color.parseColor(AppStyles.colors.PRIMARY_DARK)
                    )

            set_status_bar()
        except:
            pass

    @staticmethod
    def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple:
        """Convert hex color to RGBA tuple"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, alpha)

    @staticmethod
    def get_status_color(status_text: str) -> tuple:
        """Get color for download status"""
        status_colors = {
            'pending': ColorPalette.SECONDARY,
            'queued': ColorPalette.INFO,
            'downloading': ColorPalette.SUCCESS,
            'paused': ColorPalette.WARNING,
            'completed': ColorPalette.SUCCESS,
            'failed': ColorPalette.ERROR,
            'cancelled': ColorPalette.BORDER_DARK,
        }

        status_lower = status_text.lower()
        for key, color in status_colors.items():
            if key in status_lower:
                return AppStyles.hex_to_rgba(color)

        return AppStyles.hex_to_rgba(ColorPalette.TEXT_SECONDARY)

    @staticmethod
    def show_popup(title: str, message: str, duration: float = 2.0):
        """Show a temporary popup message"""
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))

        # Message label
        content.add_widget(Label(
            text=message,
            font_size=AppStyles.FONT_BODY,
            color=AppStyles.hex_to_rgba(ColorPalette.TEXT_PRIMARY),
            halign='center',
            valign='middle',
            size_hint=(1, 1)
        ))

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.3),
            auto_dismiss=True,
        )

        popup.open()

        # Auto dismiss after duration
        from kivy.clock import Clock
        Clock.schedule_once(lambda *args: popup.dismiss(), duration)

        return popup

    @staticmethod
    def show_confirmation(title: str, message: str, on_confirm, on_cancel=None):
        """Show a confirmation dialog"""
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(16))

        # Message
        content.add_widget(Label(
            text=message,
            font_size=AppStyles.FONT_BODY,
            color=AppStyles.hex_to_rgba(ColorPalette.TEXT_PRIMARY),
            size_hint=(1, 0.7)
        ))

        # Buttons
        btn_layout = BoxLayout(spacing=dp(8), size_hint=(1, 0.3))
        btn_layout.add_widget(Button(
            text='Cancel',
            background_color=AppStyles.hex_to_rgba(ColorPalette.BORDER)
        ))
        btn_layout.add_widget(Button(
            text='Confirm',
            background_color=AppStyles.hex_to_rgba(ColorPalette.PRIMARY)
        ))
        content.add_widget(btn_layout)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.85, 0.35)
        )

        # Bind buttons
        btn_layout.children[0].bind(on_press=lambda x: (on_confirm(), popup.dismiss()))
        btn_layout.children[1].bind(on_press=lambda x: (on_cancel() if on_cancel else None, popup.dismiss()))

        popup.open()
        return popup

    @staticmethod
    def create_card(width: float = None, height: float = None, padding: float = None):
        """Create a card-like container"""
        from kivy.uix.floatlayout import FloatLayout

        card = FloatLayout(
            size_hint=(1, None) if not width else (None, None),
            size=(width or 0, height or dp(100)),
            padding=padding or AppStyles.SPACING_MD
        )

        # Add card background
        with card.canvas.before:
            Color(rgba=AppStyles.hex_to_rgba(ColorPalette.CARD))
            RoundedRectangle(
                pos=card.pos,
                size=card.size,
                radius=[AppStyles.RADIUS_MD]
            )
            Color(rgba=AppStyles.hex_to_rgba(ColorPalette.BORDER_LIGHT))
            Line(
                rounded_rectangle=(card.x, card.y, card.width, card.height, AppStyles.RADIUS_MD),
                width=dp(1)
            )

        return card

    @staticmethod
    def create_button(text: str, style: str = 'primary', size: tuple = None):
        """Create a styled button"""
        styles = {
            'primary': (ColorPalette.PRIMARY, ColorPalette.TEXT_LIGHT),
            'secondary': (ColorPalette.SECONDARY, ColorPalette.TEXT_LIGHT),
            'success': (ColorPalette.SUCCESS, ColorPalette.TEXT_LIGHT),
            'warning': (ColorPalette.WARNING, ColorPalette.TEXT_PRIMARY),
            'error': (ColorPalette.ERROR, ColorPalette.TEXT_LIGHT),
            'default': (ColorPalette.BORDER_LIGHT, ColorPalette.TEXT_PRIMARY),
        }

        bg_color, text_color = styles.get(style, styles['default'])

        return Button(
            text=text,
            background_color=AppStyles.hex_to_rgba(bg_color),
            color=AppStyles.hex_to_rgba(text_color),
            font_size=AppStyles.FONT_BODY,
            size_hint=size or (1, 1)
        )

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(size_bytes) < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def format_speed(bytes_per_second: int) -> str:
        """Format download speed"""
        return f"{AppStyles.format_size(bytes_per_second)}/s"

    @staticmethod
    def format_time(seconds: int) -> str:
        """Format time duration"""
        if seconds < 0:
            return 'Calculating...'
        elif seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class ThemeManager:
    """Manage app themes"""

    THEMES = {
        'light': {
            'background': ColorPalette.BACKGROUND,
            'surface': ColorPalette.SURFACE,
            'text_primary': ColorPalette.TEXT_PRIMARY,
            'text_secondary': ColorPalette.TEXT_SECONDARY,
        },
        'dark': {
            'background': '#121212',
            'surface': '#1E1E1E',
            'text_primary': '#FFFFFF',
            'text_secondary': '#B0B0B0',
        }
    }

    current_theme = 'light'

    @classmethod
    def set_theme(cls, theme_name: str):
        """Set the current theme"""
        if theme_name in cls.THEMES:
            cls.current_theme = theme_name
            cls._apply_theme()

    @classmethod
    def _apply_theme(cls):
        """Apply current theme to the app"""
        theme = cls.THEMES[cls.current_theme]
        Window.clearcolor = AppStyles.hex_to_rgba(theme['background'])

    @classmethod
    def toggle_theme(cls):
        """Toggle between light and dark theme"""
        cls.current_theme = 'dark' if cls.current_theme == 'light' else 'light'
        cls._apply_theme()

    @classmethod
    def get_color(cls, color_name: str) -> tuple:
        """Get a color from current theme"""
        theme = cls.THEMES[cls.current_theme]
        hex_color = theme.get(color_name, ColorPalette.TEXT_PRIMARY)
        return AppStyles.hex_to_rgba(hex_color)
