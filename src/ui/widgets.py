from PyQt6.QtWidgets import QPushButton, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen


class NeonButton(QPushButton):
    def __init__(self, text, color1="#00f3ff", color2="#bc13fe", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(55)
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0, stop:0 {color1}, stop:1 {color2}
                );
                color: white;
                border-radius: 15px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0, stop:0 {color2}, stop:1 {color1}
                );
            }}
            QPushButton:pressed {{
                background-color: {color2};
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(color1))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)


class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(16)

    def _rotate(self):
        if self.isVisible():
            self._angle = (self._angle + 5) % 360
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#00f3ff"))
        pen.setWidth(6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(QRectF(10, 10, 80, 80), -self._angle * 16, 260 * 16)

        pen.setColor(QColor("#bc13fe"))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawArc(QRectF(25, 25, 50, 50), self._angle * 16, 200 * 16)
