from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtGui import QPainter, QColor, QFontMetrics

class GhostLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.ghost_text = ""

    def setGhostText(self, text):
        self.ghost_text = text
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.ghost_text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # フォントと色を設定
        painter.setFont(self.font())
        painter.setPen(QColor(150, 150, 150))

        fm = QFontMetrics(self.font())

        # カーソル位置取得（これが核心）
        cursor_rect = self.cursorRect()

        x = cursor_rect.x() + 4
        y = cursor_rect.y() + fm.ascent()

        painter.drawText(x, y, self.ghost_text)