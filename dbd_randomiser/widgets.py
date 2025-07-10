from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore    import Qt, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui     import QColor

class AnimatedButton(QPushButton):
    """Button with smooth hover colors and sound effects."""

    def __init__(self, text,
                 hover_color,
                 base_color="#222222",
                 text_color="white",
                 hover_sound=None,
                 click_sound=None):
        super().__init__(text)
        self._hover_progress = 0.0
        self.hover_color     = QColor(hover_color)
        self.base_color      = QColor(base_color)
        self.text_color      = text_color
        self.hover_sound     = hover_sound
        self.click_sound     = click_sound

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.anim = QPropertyAnimation(self, b"hoverProgress", self)
        self.anim.setDuration(200)

        self.clicked.connect(self._play_click_sound)
        self._update_style()

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self._hover_progress)
        self.anim.setEndValue(1.0)
        self.anim.start()
        if self.hover_sound:
            self.hover_sound.play()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self._hover_progress)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)

    def _play_click_sound(self):
        if self.click_sound:
            self.click_sound.play()

    def get_hover_progress(self):
        return self._hover_progress

    def set_hover_progress(self, val):
        self._hover_progress = val
        self._update_style()

    hoverProgress = pyqtProperty(float, fget=get_hover_progress, fset=set_hover_progress)

    def _update_style(self):
        r = int(self.base_color.red()   + (self.hover_color.red()   - self.base_color.red())   * self._hover_progress)
        g = int(self.base_color.green() + (self.hover_color.green() - self.base_color.green()) * self._hover_progress)
        b = int(self.base_color.blue()  + (self.hover_color.blue()  - self.base_color.blue())  * self._hover_progress)
        bg = f"rgb({r},{g},{b})"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {self.text_color};
                font-size: 16pt;
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
        """)
