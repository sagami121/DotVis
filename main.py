import sys
import os
import toml
from PySide6.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QWidget, 
                               QSplitter, QStatusBar, QTabWidget, QVBoxLayout, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QFont, QKeySequence, QShortcut, QIcon
from ui.sidebar import Sidebar
from ui.editor import ConfigEditor
from ui.settings_page import SettingsPage
from ui.help_page import HelpPage
from ui.edit_page import EditPage
from utils.version_utils import get_app_version

# get_app_version moved to utils.version_utils

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        version = get_app_version()
        self.setWindowTitle(f"DotVis")
        self.resize(1000, 750) 
        self.setWindowIcon(QIcon("assets/icon.png"))
        self.setAcceptDrops(True)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # --- 1. ファイルタブ ---
        self.file_tab = QWidget()
        file_layout = QHBoxLayout(self.file_tab)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Horizontal)
        self.sidebar = Sidebar()
        self.editor = ConfigEditor()
        
        self.sidebar.file_selected.connect(self.editor.load_file)
        self.sidebar.file_selected.connect(self._update_status)
        self.sidebar.file_cleared.connect(self.editor.clear_editor)
        self.sidebar.file_cleared.connect(lambda: self.statusBar().showMessage("準備完了"))
        
        self.editor.request_new_file.connect(self.sidebar.create_file_dialog)
        self.editor.request_open_file.connect(self.sidebar.open_file_dialog)
        self.editor.data_changed.connect(self._sync_edit_page)
        
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.editor)
        self.splitter.setSizes([250, 750]) 
        self.splitter.setHandleWidth(1)

        
        file_layout.addWidget(self.splitter)
        self.tabs.addTab(self.file_tab, "ファイル")
        
        self.edit_page = EditPage()
        self.tabs.addTab(self.edit_page, "編集")
        
        self.settings_page = SettingsPage()
        self.settings_page.settings_changed.connect(self._apply_settings)
        self.tabs.addTab(self.settings_page, "設定")
        
        self.help_page = HelpPage()
        self.tabs.addTab(self.help_page, "ヘルプ")
        
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("準備完了")
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.editor.save)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.sidebar.open_file_dialog)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.sidebar.create_file_dialog)
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(lambda: self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % self.tabs.count()))

    def _sync_edit_page(self, path, data):
        self.edit_page.update_info(path, data)

    def _apply_settings(self, settings):
        font = QApplication.font()
        font.setPointSize(settings["font_size"])
        QApplication.setFont(font)
        self.statusBar().showMessage("設定を適用しました", 3000)

    def _update_status(self, path):
        self.statusBar().showMessage(f"編集中のファイル: {path}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.sidebar.dropEvent(event)

def get_dark_qss():
    return """
        QMainWindow { background-color: #2d2d2d; }
        QTabWidget::pane { border: none; background-color: #1e1e1e; border-top: 1px solid #333; }
        QTabBar::tab { background-color: #252525; color: #888; padding: 10px 25px; border: none; font-weight: bold; margin-right: 1px; }
        QTabBar::tab:hover { background-color: #333; color: #ccc; }
        QTabBar::tab:selected { background-color: #1e1e1e; color: #fff; border-bottom: 2px solid #007acc; }
        #sidebar { background-color: #252525; border-right: 1px solid #333; }
        #sidebarSeparator { background-color: #333; height: 1px; min-height: 1px; }
        #editorHeader { background-color: #252525; border-bottom: 1px solid #333; color: #ccc; min-height: 50px; max-height: 50px; }
        QGroupBox { color: #aaa; font-weight: bold; border: 1px solid #333; margin-top: 15px; padding-top: 15px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
        QTreeWidget { background-color: #1e1e1e; border: none; alternate-background-color: #222222; }
        QTreeWidget::item { border-bottom: 1px solid #282828; color: #ccc; padding: 2px 4px; min-height: 24px; }
        QTreeWidget::item:selected { background-color: #007acc; color: #fff; }
        QHeaderView::section { background-color: #2d2d2d; color: #888; border: none; border-bottom: 1px solid #333; padding: 2px 5px; font-weight: bold; font-size: 10px; }
        QLineEdit { border: 1px solid #333; border-radius: 2px; padding: 2px 6px; background-color: #252525; color: #eee; min-height: 22px; }
        QPushButton { border: 1px solid #333; border-radius: 4px; padding: 4px 10px; background-color: #252525; color: #ccc; min-height: 24px; }


        QPushButton:hover { background-color: #333; color: #fff; }
        QStatusBar { background-color: #007acc; color: #fff; min-height: 22px; }
        QTextBrowser { background-color: #1e1e1e; color: #ccc; border: none; }
        QScrollBar:vertical { border: none; background: #1e1e1e; width: 10px; margin: 0px; }
        QScrollBar::handle:vertical { background: #333; min-height: 20px; }
        QScrollBar::handle:vertical:hover { background: #444; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    """

def setup_dark_theme(app):
    app.setStyle("Fusion")
    p = QPalette()
    p.setColor(QPalette.Window, QColor(45, 45, 45))
    p.setColor(QPalette.WindowText, QColor(220, 220, 220))
    p.setColor(QPalette.Base, QColor(30, 30, 30))
    p.setColor(QPalette.Text, QColor(220, 220, 220))
    p.setColor(QPalette.Button, QColor(55, 55, 55))
    p.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    p.setColor(QPalette.Highlight, QColor(42, 130, 218))
    app.setPalette(p)
    app.setStyleSheet(get_dark_qss())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    setup_dark_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
