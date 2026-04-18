import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                               QHBoxLayout, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class DebugViewer(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("デバッグビューア - 現在の生データ (JSON形式)")
        self.resize(600, 500)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        info_label = QLabel("※ メモリ上の現在のデータをJSON形式でダンプしています。")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        self.layout.addWidget(info_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        # フォントを等幅に設定
        mono_font = QFont("Courier New", 10)
        mono_font.setStyleHint(QFont.Monospace)
        self.text_edit.setFont(mono_font)
        
        # データを整形して表示
        try:
            formatted_json = json.dumps(data, indent=4, ensure_ascii=False)
            self.text_edit.setPlainText(formatted_json)
        except Exception as e:
            self.text_edit.setPlainText(f"Error rendering data: {e}")
            
        self.layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()
        self.copy_btn = QPushButton("クリップボードにコピー")
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        
        self.close_btn = QPushButton("閉じる")
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.close_btn)
        self.layout.addLayout(btn_layout)

        # ダークテーマ風のスタイル
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: #ccc; }
            QTextEdit { background-color: #252525; color: #4facfe; border: 1px solid #333; }
            QPushButton { background-color: #333; color: #ccc; border: 1px solid #444; padding: 5px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #444; color: #fff; }
        """)

    def _copy_to_clipboard(self):
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        self.copy_btn.setText("コピー完了!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("クリップボードにコピー"))
