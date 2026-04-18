import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFileDialog, QGroupBox, QGridLayout, QMessageBox)
from PySide6.QtCore import Qt
from core.config_parser import read_config, save_config

class EditPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        title = QLabel("編集ツール")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff;")
        self.layout.addWidget(title)

        # --- 統計情報 ---
        stats_group = QGroupBox("現在の情報")
        stats_layout = QGridLayout(stats_group)
        
        self.file_label = QLabel("ファイル: 未選択")
        self.keys_label = QLabel("キー数: 0")
        self.size_label = QLabel("サイズ: 0 bytes")
        
        stats_layout.addWidget(self.file_label, 0, 0)
        stats_layout.addWidget(self.keys_label, 1, 0)
        stats_layout.addWidget(self.size_label, 1, 1)
        
        self.layout.addWidget(stats_group)

        # --- 変換ツール ---
        convert_group = QGroupBox("形式変換ツール")
        convert_layout = QVBoxLayout(convert_group)
        
        convert_desc = QLabel("開いているファイルを別の形式に変換して保存します。")
        convert_desc.setStyleSheet("color: #888;")
        convert_layout.addWidget(convert_desc)
        
        btn_layout = QHBoxLayout()
        self.to_json_btn = QPushButton("JSONとして保存")
        self.to_toml_btn = QPushButton("TOMLとして保存")
        self.to_yaml_btn = QPushButton("YAMLとして保存")
        
        self.to_json_btn.clicked.connect(lambda: self._convert_to(".json"))
        self.to_toml_btn.clicked.connect(lambda: self._convert_to(".toml"))
        self.to_yaml_btn.clicked.connect(lambda: self._convert_to(".yaml"))
        
        btn_layout.addWidget(self.to_json_btn)
        btn_layout.addWidget(self.to_toml_btn)
        btn_layout.addWidget(self.to_yaml_btn)
        convert_layout.addLayout(btn_layout)
        
        self.layout.addWidget(convert_group)
        self.layout.addStretch()

        self.current_data = None
        self.current_path = None

    def update_info(self, path, data):
        self.current_path = path
        self.current_data = data
        self.file_label.setText(f"ファイル: {os.path.basename(path)}")
        
        # 簡易的なキー数計算
        def count_keys(d):
            count = 0
            if isinstance(d, dict):
                count += len(d)
                for v in d.values():
                    count += count_keys(v)
            elif isinstance(d, list):
                for v in d:
                    count += count_keys(v)
            return count
            
        self.keys_label.setText(f"総項目数: {count_keys(data)}")
        self.size_label.setText(f"サイズ: {os.path.getsize(path)} bytes")

    def _convert_to(self, ext):
        if not self.current_data:
            QMessageBox.warning(self, "警告", "変換するファイルが読み込まれていません。")
            return
            
        default_name = os.path.splitext(self.current_path)[0] + ext
        path, _ = QFileDialog.getSaveFileName(self, "別形式で保存", default_name, f"Files (*{ext})")
        
        if path:
            try:
                save_config(path, self.current_data)
                QMessageBox.information(self, "成功", f"形式を変換して保存しました:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"変換に失敗しました:\n{e}")
