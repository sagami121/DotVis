from ui.raw_viewer import RawViewer
import json
import yaml
import toml
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QLineEdit, QCheckBox, QPushButton, QLabel, QMessageBox, QMenu, QInputDialog,
    QStackedWidget, QFrame, QToolButton, QTabBar, QHeaderView, QStyle
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from core.config_parser import read_config, save_config, ConfigParseError

class ConfigEditor(QWidget):
    """Main configuration editor widget with Tree and Raw views."""
    request_new_file = Signal()
    request_open_file = Signal()
    data_changed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = None
        self.config_data = None
        self._is_modified = False
        self._is_syncing = False

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.stack = QStackedWidget()
        
        # --- Welcome Page ---
        self.welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_widget)
        welcome_layout.setAlignment(Qt.AlignCenter)
        welcome_layout.setSpacing(20)
        
        logo_label = QLabel("DotVis")
        logo_font = QFont()
        logo_font.setPointSize(32)
        logo_font.setBold(True)
        logo_label.setFont(logo_font)
        logo_label.setStyleSheet("color: #4facfe; margin-bottom: 5px;")
        
        subtitle = QLabel("ようこそ")
        sub_font = QFont()
        sub_font.setPointSize(12)
        subtitle.setFont(sub_font)
        subtitle.setStyleSheet("color: #888; margin-bottom: 30px;")
        
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        actions_layout.setAlignment(Qt.AlignCenter)
        
        quick_btn_style = """
            QPushButton { 
                border: 1px solid #444; 
                border-radius: 8px; 
                font-size: 14px; 
                padding: 12px 40px; 
                min-width: 260px; 
                background-color: #252525;
                color: #ccc;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #666;
                color: #fff;
            }
        """
        
        new_btn = QPushButton("新しいファイルを作成")
        new_btn.setStyleSheet(quick_btn_style)
        new_btn.clicked.connect(self.request_new_file.emit)
        
        open_btn = QPushButton("既存のファイルを開く")
        open_btn.setStyleSheet(quick_btn_style)
        open_btn.clicked.connect(self.request_open_file.emit)
        
        actions_layout.addWidget(new_btn)
        actions_layout.addWidget(open_btn)
        
        welcome_layout.addStretch()
        welcome_layout.addWidget(logo_label, 0, Qt.AlignCenter)
        welcome_layout.addWidget(subtitle, 0, Qt.AlignCenter)
        welcome_layout.addLayout(actions_layout)
        welcome_layout.addStretch()
        
        # --- Editor Page ---
        self.editor_widget = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_widget)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(0)
        
        # 1. View Components (Initialize first so headers/subheaders can reference them)
        self.view_tabs = QStackedWidget()
        
        # -- Tree View
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["項目", "値"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.setColumnWidth(0, 150)
        self.tree.setIndentation(15)
        self.tree.setAlternatingRowColors(True)
        
        style = self.style()
        self.dir_icon = style.standardIcon(QStyle.SP_DirIcon)
        self.file_icon = style.standardIcon(QStyle.SP_FileIcon)
        self.list_icon = style.standardIcon(QStyle.SP_FileDialogDetailedView)

        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_tree_context_menu)

        self.tree_container = QWidget()
        tree_layout = QVBoxLayout(self.tree_container)
        tree_layout.setContentsMargins(10, 10, 10, 10)
        tree_layout.addWidget(self.tree)

        # -- Raw View
        self.raw_viewer = RawViewer()
        self.raw_viewer.textChanged.connect(self._on_raw_content_changed)
        
        self.view_tabs.addWidget(self.tree_container)
        self.view_tabs.addWidget(self.raw_viewer)

        # 2. Header (File Title & Save)
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(50)
        self.header_frame.setObjectName("editorHeader")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.title_label = QLabel("ファイル未選択")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save)
        self.save_btn.setEnabled(False)
        self.save_btn.setFixedWidth(100)
        self.save_btn.setStyleSheet("""
            QPushButton { 
                background-color: #007acc; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                font-weight: bold; 
                padding: 6px; 
            } 
            QPushButton:hover { 
                background-color: #008be5; 
            } 
            QPushButton:disabled { 
                background-color: #444; 
                color: #777; 
            }
            QPushButton#modified {
                background-color: #e81123;
            }
            QPushButton#modified:hover {
                background-color: #f72a3b;
            }
        """)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.save_btn)
        self.editor_layout.addWidget(self.header_frame)

        # 3. View Switcher & Sub-Header
        self.view_selector = QTabBar()
        self.view_selector.addTab("ツリー編集")
        self.view_selector.addTab("Rawテキスト")
        self.view_selector.setStyleSheet("""
            QTabBar::tab { background: #252525; color: #888; padding: 5px 15px; border: 1px solid #333; border-bottom: none; }
            QTabBar::tab:selected { background: #1e1e1e; color: #fff; border-bottom: 2px solid #007acc; }
        """)

        self.sub_header = QFrame()
        self.sub_header.setFixedHeight(40)
        self.sub_header.setStyleSheet("background-color: #1e1e1e; border-bottom: 1px solid #333;")
        sub_layout = QHBoxLayout(self.sub_header)
        sub_layout.setContentsMargins(10, 0, 10, 0)
        
        sub_layout.addWidget(self.view_selector)
        
        self.breadcrumb_label = QLabel("ルート")
        self.breadcrumb_label.setStyleSheet("color: #666; font-size: 11px; margin-left:10px;")
        sub_layout.addWidget(self.breadcrumb_label)
        sub_layout.addStretch()
        
        # 検索バー
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("キーを検索...")
        self.search_box.setFixedWidth(180)
        self.search_box.setStyleSheet("QLineEdit { background-color: #252525; border: 1px solid #444; border-radius: 4px; padding: 2px 10px; font-size: 11px; }")
        sub_layout.addWidget(self.search_box)
        
        # 展開/折りたたみボタン
        btn_qss = "QToolButton { border: none; color: #888; padding: 4px; } QToolButton:hover { color: #fff; background-color: #333; }"
        self.expand_btn = QToolButton()
        self.expand_btn.setText("＋")
        self.expand_btn.setStyleSheet(btn_qss)
        
        self.collapse_btn = QToolButton()
        self.collapse_btn.setText("－")
        self.collapse_btn.setStyleSheet(btn_qss)
        
        sub_layout.addWidget(self.expand_btn)
        sub_layout.addWidget(self.collapse_btn)
        
        # シグナル接続 (全てのウィジェットが初期化された後に行う)
        self.view_selector.currentChanged.connect(self._on_view_changed)
        self.search_box.textChanged.connect(self._on_search)
        self.expand_btn.clicked.connect(self.tree.expandAll)
        self.collapse_btn.clicked.connect(self.tree.collapseAll)
        
        self.editor_layout.addWidget(self.sub_header)

        # 4. View Area
        self.editor_layout.addWidget(self.view_tabs)
        
        self.stack.addWidget(self.welcome_widget)
        self.stack.addWidget(self.editor_widget)
        self.main_layout.addWidget(self.stack)
        
        # Debounce timer for raw sync
        self.raw_sync_timer = QTimer()
        self.raw_sync_timer.setSingleShot(True)
        self.raw_sync_timer.timeout.connect(self._sync_raw_to_tree)
        
    def _on_view_changed(self, index):
        if index == 1: # Switch to Raw
            self._sync_tree_to_raw()
            self.search_box.setEnabled(False)
            self.expand_btn.setEnabled(False)
            self.collapse_btn.setEnabled(False)
        else: # Switch to Tree
            self.search_box.setEnabled(True)
            self.expand_btn.setEnabled(True)
            self.collapse_btn.setEnabled(True)
        self.view_tabs.setCurrentIndex(index)

    def _sync_tree_to_raw(self):
        if self.config_data is None: return
        self._is_syncing = True
        ext = os.path.splitext(self.current_path)[1].lower()
        try:
            if ext == '.json':
                text = json.dumps(self.config_data, indent=2, ensure_ascii=False)
            elif ext in ['.yaml', '.yml']:
                text = yaml.dump(self.config_data, allow_unicode=True, sort_keys=False)
            elif ext == '.toml':
                text = toml.dumps(self.config_data)
            else:
                text = str(self.config_data)
            self.raw_viewer.setPlainText(text)
        except Exception:
            pass
        finally:
            self._is_syncing = False

    def _on_raw_content_changed(self):
        if self._is_syncing: return
        self.raw_sync_timer.start(1000) # 1 second debounce
        self.set_modified(True)

    def _sync_raw_to_tree(self):
        if self.current_path is None: return
        text = self.raw_viewer.toPlainText()
        ext = os.path.splitext(self.current_path)[1].lower()
        try:
            if ext == '.json':
                new_data = json.loads(text)
            elif ext in ['.yaml', '.yml']:
                new_data = yaml.safe_load(text)
            elif ext == '.toml':
                new_data = toml.loads(text)
            else:
                return
            
            self.config_data = new_data
            self.populate_tree()
            self.data_changed.emit(self.current_path, self.config_data)
        except Exception:
            # Silent fail during live typing
            pass

    def set_modified(self, modified=True):
        self._is_modified = modified
        display_name = os.path.basename(self.current_path) if self.current_path else "ファイル未選択"
        if modified:
            self.title_label.setText(f"{display_name} *")
            self.save_btn.setProperty("modified", True)
        else:
            self.title_label.setText(display_name)
            self.save_btn.setProperty("modified", False)
        
        self.save_btn.style().unpolish(self.save_btn)
        self.save_btn.style().polish(self.save_btn)

    def load_file(self, path):
        if not path or not os.path.exists(path): return
        self.current_path = path
        try:
            self.config_data = read_config(path)
            self.save_btn.setEnabled(True)
            self.set_modified(False)
            self.populate_tree()
            self._sync_tree_to_raw()
            self.stack.setCurrentWidget(self.editor_widget)
            self.data_changed.emit(self.current_path, self.config_data)
        except ConfigParseError as e:
            msg = f"書式の読み込みに失敗しました。\n\nエラー: {str(e)}"
            if e.line: msg += f"\n行: {e.line}, 列: {e.col}"
            QMessageBox.critical(self, "パースエラー", msg)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイル読み込みエラー:\n{e}")

    def clear_editor(self):
        self.current_path = None
        self.config_data = None
        self._is_modified = False
        self.title_label.setText("ファイル未選択")
        self.breadcrumb_label.setText("ルート")
        self.tree.clear()
        self.raw_viewer.clear()
        self.save_btn.setEnabled(False)
        self.save_btn.setProperty("modified", False)
        self.stack.setCurrentWidget(self.welcome_widget)
            
    def populate_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()
        if self.config_data is not None:
            self._build_tree(self.config_data, self.tree.invisibleRootItem())
            self.tree.expandToDepth(0)
        self.tree.blockSignals(False)
        self._on_search() 
        
    def _build_tree(self, data, parent_item, path_keys=None):
        if path_keys is None: path_keys = []
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent_item)
                item.setText(0, str(key))
                self._add_value_widget_or_recurse(item, value, path_keys + [key])
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem(parent_item)
                item.setText(0, f"[{index}]")
                self._add_value_widget_or_recurse(item, value, path_keys + [index])
                
    def _add_value_widget_or_recurse(self, item, value, path_keys):
        item.setData(1, Qt.UserRole, path_keys)
        if isinstance(value, (dict, list)):
            if isinstance(value, list):
                item.setIcon(0, self.list_icon)
                item.setText(1, f"[{len(value)} items]")
            else:
                item.setIcon(0, self.dir_icon)
                item.setText(1, f"{{{len(value)} keys}}")
            item.setForeground(1, QColor("#666"))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self._build_tree(value, item, path_keys)
        else:
            item.setIcon(0, self.file_icon)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            if isinstance(value, bool):
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(1, Qt.Checked if value else Qt.Unchecked)
                item.setData(1, Qt.UserRole + 1, 'bool')
            else:
                item.setText(1, str(value) if value is not None else "")
                item.setForeground(1, QColor("#4facfe")) 
                t = 'int' if isinstance(value, int) else 'float' if isinstance(value, float) else 'str'
                item.setData(1, Qt.UserRole + 1, t)

    def _on_selection_changed(self):
        items = self.tree.selectedItems()
        if not items:
            self.breadcrumb_label.setText("ルート")
            return
        
        path_keys = items[0].data(1, Qt.UserRole)
        if path_keys:
            self.breadcrumb_label.setText(" > ".join(map(str, path_keys)))
        else:
            self.breadcrumb_label.setText("ルート")

    def _on_search(self):
        search_text = self.search_box.text().lower()
        
        def filter_item(item):
            match = search_text in item.text(0).lower() or search_text in item.text(1).lower()
            any_child_match = False
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    any_child_match = True
            
            show = match or any_child_match
            item.setHidden(not show)
            if search_text:
                if any_child_match: item.setExpanded(True)
            else:
                if item.parent(): item.setExpanded(False)
                else: item.setExpanded(True)
            return show

        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))
        self.tree.blockSignals(False)

    def _on_item_changed(self, item, column):
        if column != 1: return
        path_keys = item.data(1, Qt.UserRole)
        if not path_keys: return
        type_str = item.data(1, Qt.UserRole + 1)
        
        try:
            if type_str == 'bool': val = (item.checkState(1) == Qt.Checked)
            elif type_str == 'int': 
                text = item.text(1)
                val = int(text) if text else 0
            elif type_str == 'float': 
                text = item.text(1)
                val = float(text) if text else 0.0
            else: val = item.text(1)
            
            self._update_value(path_keys, val)
            self.set_modified(True)
            self.data_changed.emit(self.current_path, self.config_data)
        except ValueError:
            QMessageBox.warning(self, "入力エラー", f"数値として正しくありません: {item.text(1)}")
            self.populate_tree()

    def _show_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        path_keys = item.data(1, Qt.UserRole) if item else []
        
        current = self.config_data
        if current is not None and path_keys:
            try:
                for k in path_keys: 
                    if isinstance(current, (dict, list)): current = current[k]
            except (KeyError, IndexError): current = None
        
        is_container = current is None or isinstance(current, (dict, list))
        add_action = menu.addAction("項目を追加") if is_container else None
        
        if item:
            del_action = menu.addAction("削除")
            menu.addSeparator()
            to_dict_action = menu.addAction("オブジェクトに変換") if not isinstance(current, dict) else None
            to_list_action = menu.addAction("配列に変換") if not isinstance(current, list) else None
        
        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action == add_action: self._add_new_element(item)
        elif item and action == del_action: self._del_element(item)
        elif item and action == to_dict_action: self._convert_container(path_keys, {})
        elif item and action == to_list_action: self._convert_container(path_keys, [])

    def _convert_container(self, keys, new_val):
        self._update_value(keys, new_val)
        self.set_modified(True)
        self.populate_tree()
        self.data_changed.emit(self.current_path, self.config_data)

    def _add_new_element(self, item):
        path_keys = item.data(1, Qt.UserRole) if item else []
        if self.config_data is None: self.config_data = {}
        current = self.config_data
        for key in path_keys: current = current[key]
        
        dialog = QInputDialog(self)
        dialog.setWindowTitle("項目の追加")
        dialog.setLabelText("キー名を入力:")
        dialog.setTextValue("new_key")
        dialog.setOkButtonText("追加")
        dialog.setCancelButtonText("キャンセル")
        dialog.setMinimumWidth(300)
        
        if dialog.exec() == QInputDialog.Accepted:
            text = dialog.textValue()
            if text:
                if isinstance(current, list): current.append("new_value")
                elif text not in current: current[text] = "new_value"
                else: 
                    QMessageBox.warning(self, "エラー", "そのキーは既に存在します。")
                    return
                self.set_modified(True)
                self.populate_tree()
                self.data_changed.emit(self.current_path, self.config_data)

    def _del_element(self, item):
        path_keys = item.data(1, Qt.UserRole)
        if not path_keys: return
        reply = QMessageBox.question(self, "確認", f"'{path_keys[-1]}' を削除しますか？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No: return

        current = self.config_data
        for key in path_keys[:-1]: current = current[key]
        if isinstance(current, dict): del current[path_keys[-1]]
        elif isinstance(current, list): current.pop(path_keys[-1])
        
        self.set_modified(True)
        self.populate_tree()
        self.data_changed.emit(self.current_path, self.config_data)

    def _update_value(self, keys, value):
        if not self.config_data: return
        current = self.config_data
        try:
            for key in keys[:-1]: current = current[key]
            current[keys[-1]] = value
        except Exception: pass
        
    def save(self):
        if not self.current_path or self.config_data is None: return
        try:
            save_config(self.current_path, self.config_data)
            self.set_modified(False)
            self.save_btn.setText("保存完了!")
            QTimer.singleShot(2000, lambda: self.save_btn.setText("保存"))
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存エラー:\n{e}")
