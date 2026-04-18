from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QSlider, QGroupBox, QPushButton, QFormLayout)
from PySide6.QtCore import Qt, Signal

class SettingsPage(QWidget):
    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        title = QLabel("アプリケーション設定")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff;")
        self.layout.addWidget(title)

        # --- 外観設定 ---
        appearance_group = QGroupBox("外観")
        appearance_layout = QFormLayout(appearance_group)
        
        # テーマ選択は削除し、フォントサイズのみ残す
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(10, 24)
        self.font_slider.setValue(12)
        appearance_layout.addRow("エディタ文字サイズ:", self.font_slider)
        
        self.layout.addWidget(appearance_group)

        # --- 動作設定 ---
        behavior_group = QGroupBox("動作")
        behavior_layout = QFormLayout(behavior_group)
        
        self.autosave_combo = QComboBox()
        self.autosave_combo.addItems(["無効", "有効 (30秒ごと)"])
        behavior_layout.addRow("自動保存:", self.autosave_combo)
        
        self.layout.addWidget(behavior_group)

        self.layout.addStretch()

        self.save_btn = QPushButton("設定を保存して適用")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #008be5; }
        """)
        self.save_btn.clicked.connect(self._on_save)
        self.layout.addWidget(self.save_btn)

    def _on_save(self):
        settings = {
            "font_size": self.font_slider.value(),
            "autosave": self.autosave_combo.currentIndex() > 0
        }
        self.settings_changed.emit(settings)
