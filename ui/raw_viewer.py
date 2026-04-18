import os
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt, QRegularExpression

class RawHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        # Key format (Blue-ish)
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#4facfe"))
        key_format.setFontWeight(QFont.Bold)
        self._rules.append((QRegularExpression(r'"[^"]*"(?=\s*:)'), key_format)) # JSON keys
        self._rules.append((QRegularExpression(r'^[\w\d_-]+(?=\s*=)'), key_format)) # TOML/INI keys

        # Section format (INI headers, etc.)
        section_format = QTextCharFormat()
        section_format.setForeground(QColor("#d19a66"))
        section_format.setFontWeight(QFont.Bold)
        self._rules.append((QRegularExpression(r'^\[.*\]'), section_format))

        # String format (Yellow-ish)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self._rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        # Number format (Green-ish)
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self._rules.append((QRegularExpression(r'\b\d+(\.\d+)?\b'), number_format))

        # Boolean/Null format (Purple-ish)
        const_format = QTextCharFormat()
        const_format.setForeground(QColor("#c586c0"))
        self._rules.append((QRegularExpression(r'\b(true|false|null|None|True|False)\b'), const_format))

        # Comment format (Grey)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self._rules.append((QRegularExpression(r'#.*'), comment_format))
        self._rules.append((QRegularExpression(r'//.*'), comment_format))

    def highlightBlock(self, text):
        for expression, format in self._rules:
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class RawViewer(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(False)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Set Mono Font
        font = QFont("Consolas" if os.name == 'nt' else "Courier New")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(11)
        self.setFont(font)
        
        # Dark Background
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
            }
        """)
        
        self.highlighter = RawHighlighter(self.document())
