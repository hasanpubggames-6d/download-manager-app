"""
AI Studio Download Manager - Android Version
Converted to Kivy for Android compatibility
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBase
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest

import os
import json
import threading
import time
from urllib.parse import urlparse, unquote
from typing import Optional, List, Dict, Any

# Import local modules
from config import Config
from download_manager import DownloadManager, DownloadItem, DownloadStatus
from ui_styles import AppStyles
from utils import Utils
from metadata_worker import MetadataWorker

# KV Language UI Definition
Builder.load_string('''
#:import dp kivy.metrics.dp
#:import rgba kivy.utils.get_color_from_hex

<DownloadItemWidget@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(80)
    padding: dp(8)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: rgba('#F5F5F5')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.7

        Label:
            id: filename_label
            text: root.filename if hasattr(root, 'filename') else 'Unknown'
            font_size: dp(14)
            bold: True
            color: rgba('#212121')
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            size_hint_y: None
            height: dp(24)

        ProgressBar:
            id: progress_bar
            value: root.progress if hasattr(root, 'progress') else 0
            max: 100
            size_hint_y: None
            height: dp(8)

        Label:
            id: status_label
            text: root.status if hasattr(root, 'status') else 'Pending'
            font_size: dp(11)
            color: rgba('#757575')
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            size_hint_y: None
            height: dp(20)

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.3
        spacing: dp(4)

        Button:
            id: pause_btn
            text: '⏸' if root.is_downloading else '▶'
            font_size: dp(18)
            size_hint_y: 0.5
            on_press: root.pause_resume()

        Button:
            id: cancel_btn
            text: '✕'
            font_size: dp(18)
            size_hint_y: 0.5
            on_press: root.cancel_download()

<MainScreen>:
    orientation: 'vertical'
    padding: dp(8)
    spacing: dp(8)

    # Header
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        canvas.before:
            Color:
                rgba: rgba('#2196F3')
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(8)]

        Label:
            text: 'AI Studio Download Manager'
            font_size: dp(20)
            bold: True
            color: rgba('#FFFFFF')

    # URL Input Section
    BoxLayout:
        size_hint_y: None
        height: dp(60)
        padding: dp(8)

        TextInput:
            id: url_input
            hint_text: 'Enter download URL...'
            multiline: False
            font_size: dp(14)
            size_hint_x: 0.8

        Button:
            id: add_btn
            text: '+ Add'
            font_size: dp(14)
            bold: True
            size_hint_x: 0.2
            background_color: rgba('#4CAF50')
            on_press: root.add_download()

    # Tabs
    TabbedPanel:
        id: tabs
        do_default_tab: False

        TabbedPanelItem:
            text: 'Downloads'
            BoxLayout:
                orientation: 'vertical'

                ScrollView:
                    RecycleView:
                        id: download_list
                        viewclass: 'DownloadItemWidget'
                        data: []

                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(4)

                    Button:
                        text: 'Start All'
                        on_press: root.start_all()
                        size_hint_x: 0.33

                    Button:
                        text: 'Pause All'
                        on_press: root.pause_all()
                        size_hint_x: 0.33

                    Button:
                        text: 'Clear Done'
                        on_press: root.clear_completed()
                        size_hint_x: 0.33

        TabbedPanelItem:
            text: 'Settings'
            SettingsWidget:

        TabbedPanelItem:
            text: 'About'
            AboutWidget:

<SettingsWidget@BoxLayout>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(16)

    Label:
        text: 'Download Settings'
        font_size: dp(18)
        bold: True
        size_hint_y: None
        height: dp(40)

    BoxLayout:
        size_hint_y: None
        height: dp(50)

        Label:
            text: 'Download Path:'
            size_hint_x: 0.4
            halign: 'left'

        TextInput:
            id: path_input
            size_hint_x: 0.6

    BoxLayout:
        size_hint_y: None
        height: dp(50)

        Label:
            text: 'Max Connections:'
            size_hint_x: 0.4
            halign: 'left'

        Spinner:
            id: connections_spinner
            values: ['1', '2', '3', '4', '5', '6', '8', '10']
            size_hint_x: 0.6

    BoxLayout:
        size_hint_y: None
        height: dp(50)

        Label:
            text: 'Max Speed (KB/s):'
            size_hint_x: 0.4
            halign: 'left'

        TextInput:
            id: speed_input
            input_filter: 'int'
            size_hint_x: 0.6
            hint_text: '0 = Unlimited'

    Button:
        text: 'Save Settings'
        size_hint_y: None
        height: dp(50)
        background_color: rgba('#2196F3')
        on_press: app.save_settings()

<AboutWidget@BoxLayout>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(8)

    Label:
        text: 'AI Studio Download Manager'
        font_size: dp(24)
        bold: True

    Label:
        text: 'Version 2.0 (Android Edition)'
        font_size: dp(14)
        color: rgba('#757575')

    Label:
        text: 'A powerful download manager built with Kivy for Android compatibility.'
        font_size: dp(12)
        text_size: self.size
        halign: 'center'

    Label:
        text: 'Features:\\n- Multi-threaded downloads\\n- Pause/Resume support\\n- Queue management\\n- Speed limiting\\n- Metadata extraction'
        font_size: dp(11)
        text_size: self.size
        halign: 'left'
        size_hint_y: None
        height: dp(150)
''')


class DownloadItemWidget(BoxLayout):
    """Widget representing a single download item"""
    filename = StringProperty('')
    progress = NumericProperty(0)
    status = StringProperty('Pending')
    is_downloading = BooleanProperty(False)
    download_id = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def pause_resume(self):
        if self.is_downloading:
            self.app.dm.pause_download(self.download_id)
        else:
            self.app.dm.resume_download(self.download_id)

    def cancel_download(self):
        self.app.dm.cancel_download(self.download_id)


class DownloadListRecycleView(RecycleView):
    """RecycleView for download list"""
    pass


class MainScreen(BoxLayout):
    """Main application screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        Clock.schedule_once(self._setup, 0)

    def _setup(self, dt):
        pass

    def add_download(self):
        url = self.ids.url_input.text.strip()
        if url:
            self.app.add_download(url)
            self.ids.url_input.text = ''

    def start_all(self):
        self.app.dm.start_all()

    def pause_all(self):
        self.app.dm.pause_all()

    def clear_completed(self):
        self.app.dm.clear_completed()

    def update_download_list(self, downloads):
        """Update the download list view"""
        data = []
        for dl in downloads:
            data.append({
                'filename': dl.filename,
                'progress': dl.progress,
                'status': dl.status_text,
                'is_downloading': dl.status == DownloadStatus.DOWNLOADING,
                'download_id': dl.id
            })
        self.ids.download_list.data = data


class DownloadManagerApp(App):
    """Main Application Class"""

    def build(self):
        self.title = 'AI Studio Download Manager'

        # Initialize configuration
        self.config = Config.load()

        # Initialize download manager
        self.dm = DownloadManager(self.config)

        # Initialize metadata worker
        self.metadata_worker = MetadataWorker(self.config)

        # Apply styles
        AppStyles.apply(self)

        # Create main screen
        self.main_screen = MainScreen()

        # Schedule updates
        Clock.schedule_interval(self.update_ui, 0.5)

        return self.main_screen

    def on_start(self):
        # Request storage permissions on Android
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])
        except ImportError:
            # Running on desktop, permissions not needed
            pass

    def add_download(self, url: str):
        """Add a new download"""
        self.dm.add_download(url)

    def save_settings(self):
        """Save current settings"""
        settings_screen = self.main_screen.ids.tabs.get_children()[0]
        if hasattr(settings_screen, 'ids'):
            self.config.download_path = settings_screen.ids.path_input.text
            self.config.max_connections = int(settings_screen.ids.connections_spinner.text)
            try:
                self.config.max_speed = int(settings_screen.ids.speed_input.text or '0')
            except ValueError:
                self.config.max_speed = 0
            self.config.save()
            AppStyles.show_popup('Success', 'Settings saved successfully!')

    def update_ui(self, dt):
        """Update UI with current download status"""
        downloads = self.dm.get_all_downloads()
        self.main_screen.update_download_list(downloads)

        # Update status bar
        active_count = len([d for d in downloads if d.status == DownloadStatus.DOWNLOADING])
        completed_count = len([d for d in downloads if d.status == DownloadStatus.COMPLETED])

        self.main_screen.ids.status.text = f'Active: {active_count} | Completed: {completed_count}'

    def on_stop(self):
        """Cleanup on app close"""
        self.dm.stop_all()
        self.metadata_worker.stop()


def run_app():
    """Entry point for the application"""
    app = DownloadManagerApp()
    app.run()


if __name__ == '__main__':
    run_app()
