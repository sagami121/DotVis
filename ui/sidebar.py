import os
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QPushButton, QFileDialog, QLabel, QMenu, QFrame, QMessageBox)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QClipboard
from core.config_parser import save_config

class Sidebar(QWidget):
    file_selected = Signal(str)
    file_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(180)
        self.setMaximumWidth(500)
        self.setAcceptDrops(True)

        self.setObjectName("sidebar")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # ... (Headers etc remain same)
        self._init_ui() # I'll refactor slightly to keep it clean

    def _init_ui(self):
        # Header Area
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        self.title_label = QLabel("ファイル一覧")
        header_font = QFont()
        header_font.setPointSize(10)
        header_font.setBold(True)
        self.title_label.setFont(header_font)
        self.title_label.setStyleSheet("color: #888;")
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Toolbar Buttons (Small)
        btn_style = """
            QPushButton { border: none; background-color: transparent; padding: 4px; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(128, 128, 128, 0.2); }
        """
        
        self.new_btn = QPushButton("新規")
        self.new_btn.setToolTip("新規ファイル作成")
        self.new_btn.setFixedWidth(50)
        self.new_btn.setStyleSheet(btn_style)
        self.new_btn.clicked.connect(self.create_file_dialog)
        
        self.open_btn = QPushButton("開く")
        self.open_btn.setToolTip("既存ファイルを開く")
        self.open_btn.setFixedWidth(50)
        self.open_btn.setStyleSheet(btn_style)
        self.open_btn.clicked.connect(self.open_file_dialog)
        
        header_layout.addWidget(self.new_btn)
        header_layout.addWidget(self.open_btn)
        self.main_layout.addWidget(header_widget)
        
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setObjectName("sidebarSeparator")
        self.main_layout.addWidget(self.line)
        
        # File List
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.main_layout.addWidget(self.list_widget)
        self.files = []

    # Drag and Drop Events
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        valid_exts = ['.json', '.toml', '.yaml', '.yml', '.ini', '.cfg', '.conf']
        first_valid = None
        for f in files:
            if any(f.lower().endswith(ext) for ext in valid_exts):
                self._add_file_item(f)
                if not first_valid: first_valid = f
        if first_valid:
            self._select_and_open_file(first_valid)

    def open_file_dialog(self):
        filters = (
            "All Configs (*.json *.toml *.yaml *.yml *.ini *.cfg *.conf);;"
            "JSON Format (*.json);;TOML Format (*.toml);;YAML Format (*.yaml *.yml);;INI Format (*.ini *.cfg *.conf);;All Files (*)"
        )
        paths, _ = QFileDialog.getOpenFileNames(self, "設定ファイルを開く", "", filters)
        if not paths: return
        for path in paths: self._add_file_item(path)
        if paths: self._select_and_open_file(paths[0])
        
    def create_file_dialog(self):
        filters = "JSON (*.json);;TOML (*.toml);;YAML (*.yaml);;All Files (*)"
        path, _ = QFileDialog.getSaveFileName(self, "新しくファイルを作成", "", filters)
        if not path: return
        try:
            save_config(path, {})
            self._add_file_item(path)
            self._select_and_open_file(path)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイル作成エラー:\n{e}")

    def _add_file_item(self, path):
        if path in self.files: return
        self.files.append(path)
        item = QListWidgetItem(os.path.basename(path))
        item.setData(Qt.UserRole, path)
        item.setToolTip(path)
        self.list_widget.addItem(item)
        
    def remove_file(self, path):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == path:
                is_selected = self.list_widget.currentItem() == item
                self.list_widget.takeItem(i)
                self.files.remove(path)
                if is_selected: self.file_cleared.emit()
                break
                
    def _select_and_open_file(self, path):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == path:
                self.list_widget.setCurrentItem(item)
                self.file_selected.emit(path)
                break

    def _on_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        if path: self.file_selected.emit(path)

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item:
            path = item.data(Qt.UserRole)
            menu = QMenu(self)
            open_folder_action = menu.addAction("フォルダで開く")
            copy_path_action = menu.addAction("パスをコピー")
            menu.addSeparator()
            delete_action = menu.addAction("リストから削除")
            
            action = menu.exec(self.list_widget.mapToGlobal(pos))
            if action == open_folder_action:
                if os.name == 'nt':
                    subprocess.run(['explorer', '/select,', os.path.normpath(path)], check=False)
                else:
                    subprocess.run(['open', os.path.dirname(path)], check=False)
            elif action == copy_path_action:
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(path)
            elif action == delete_action:
                self.remove_file(path)
