from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextBrowser, QFrame)
from PySide6.QtCore import Qt
from utils.version_utils import get_app_version

class HelpPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(10)

        title = QLabel("DotVis ヘルプ & ガイド")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff;")
        self.layout.addWidget(title)
        
        # --- 分割線 ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333; height: 1px;")
        self.layout.addWidget(line)

        # --- コンテンツエリア ---
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e1e;
                border: none;
                color: #ccc;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        
        version = get_app_version()
        help_html = f"""
        <h3 style='color: #4facfe;'>1. DotVisについて</h3>
        <p>DotVisは、JSON、TOML、YAMLなどの設定ファイルをGUI上で編集するツールです。
        ツリー形式で階層構造を把握しながら、直感的に値を変更したり、新しい項目を追加したりできます。</p>
        
        <h3 style='color: #4facfe;'>2. 基本的な使い方</h3>
        <ul>
            <li><b>ファイルの追加:</b> 左側の「新規」または「開く」ボタンでファイルを選択します。</li>
            <li><b>値の編集:</b> ツリーの「値」列をダブルクリック（またはブール値はクリック）して編集します。</li>
            <li><b>項目の追加/削除:</b> ツリー上で右クリックするとメニューが表示されます。</li>
            <li><b>保存:</b> 編集後、右上の「保存」ボタンを押してください。</li>
        </ul>
        
        <h3 style='color: #4facfe;'>3. キーボードショートカット</h3>
        <table border='0' cellspacing='10' style='color: #ccc;'>
            <tr><td><b>Ctrl + S</b></td><td>ファイルを保存（現在のタブ）</td></tr>
            <tr><td><b>Ctrl + O</b></td><td>ファイルを開く</td></tr>
            <tr><td><b>Ctrl + N</b></td><td>新しいファイルを作成</td></tr>
            <tr><td><b>F12</b></td><td>デバッグモード表示（開発者向け）</td></tr>
        </table>
        
        <h3 style='color: #4facfe;'>4. 開発・サポート</h3>
        <p>不具合の報告や機能要望は、GitHubのissueまでお寄せください。</p>
        <p>バージョン: <b>{version}</b><br>
        ライセンス: <b>MIT License</b></p>
        """
        self.browser.setHtml(help_html)
        self.layout.addWidget(self.browser)
