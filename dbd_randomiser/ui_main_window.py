"""
Main application window for DBD Perk Roulette.
Handles background animation, audio, and navigation to the perk spinner.
"""

import os
import pygame
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtGui import QMovie, QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer, QSize

from ui_perk_display import PerkDisplay
from widgets import AnimatedButton

# ─── Constants ─────────────────────────────────────────────────────────────
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600

GIF_PATHS = [
    "images/menu/fog.gif",
    "images/menu/fogreverse.gif",
]
GIF_INTERVAL_MS = 10_000  # switch every 10 seconds
GIF_PAUSE_MS = 500        # pause between switches

THEME_MUSIC = "media/dbdtheme.mp3"
SFX_HOVER   = "media/buttonhover.mp3"
SFX_CLICK   = "media/buttonselect.mp3"
DEFAULT_VOL = 0.1

# ─── Main Window ──────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    """The primary window: animated background, audio, and menu navigation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DBD Perk Roulette")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        self._setup_background()
        self._setup_audio()
        self._setup_ui_layer()
        self._add_footer()

        self.is_muted = False
        self.show_main_menu()

    # ─── Background GIF ────────────────────────────────────────────────────
    def _setup_background(self):
        """Load and start the looping background GIFs with a switch timer."""
        self.gif_index = 0
        self.movie_label = QLabel(self)
        self.movie_label.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.movie_label.setScaledContents(True)

        self.movie = QMovie(GIF_PATHS[0])
        self.movie_label.setMovie(self.movie)
        self.movie.start()

        self.gif_timer = QTimer(self)
        self.gif_timer.timeout.connect(self._pause_and_switch_gif)
        self.gif_timer.start(GIF_INTERVAL_MS)

    def _pause_and_switch_gif(self):
        """Pause briefly before swapping to the next GIF."""
        QTimer.singleShot(GIF_PAUSE_MS, self._switch_background_gif)

    def _switch_background_gif(self):
        """Switch to the next GIF and restart the cycle."""
        self.gif_index = (self.gif_index + 1) % len(GIF_PATHS)
        self.movie.stop()
        self.movie = QMovie(GIF_PATHS[self.gif_index])
        self.movie_label.setMovie(self.movie)
        self.movie.start()
        self.gif_timer.start(GIF_INTERVAL_MS)

    # ─── Audio Setup ───────────────────────────────────────────────────────
    def _setup_audio(self):
        """Initialize pygame mixer, play theme music, and load SFX."""
        pygame.mixer.init()
        try:
            pygame.mixer.music.load(THEME_MUSIC)
            pygame.mixer.music.set_volume(DEFAULT_VOL)
            pygame.mixer.music.play(-1)  # endless loop
        except pygame.error as e:
            print(f"[ERROR] Loading theme music: {e}")

        # Load hover/click sounds (if available)
        try:
            self.sfx_hover = pygame.mixer.Sound(SFX_HOVER)
            self.sfx_click = pygame.mixer.Sound(SFX_CLICK)
            self.sfx_hover.set_volume(0.2)
            self.sfx_click.set_volume(0.2)
        except pygame.error:
            print("[WARNING] Could not load one or more SFX.")
            self.sfx_hover = self.sfx_click = None

    # ─── UI Layer ─────────────────────────────────────────────────────────
    def _setup_ui_layer(self):
        """Create a transparent overlay for all widgets."""
        self.ui_layer = QWidget(self)
        self.ui_layer.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.ui_layer.setStyleSheet("background: transparent;")
        self.ui_layout = QVBoxLayout(self.ui_layer)
        self.ui_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # ─── Footer (Credits & Mute) ──────────────────────────────────────────
    def _add_footer(self):
        """Add a credit link and mute button to the bottom corners."""
        # Credits
        credit = QLabel(self.ui_layer)
        credit.setText(
            '<span style="color:white;">Made by </span>'
            '<a href="https://github.com/Teiruu/" '
            'style="color:#58a6ff;text-decoration:none;">Tei</a>'
        )
        credit.setOpenExternalLinks(True)
        credit.setStyleSheet("background:transparent; font-size:9pt;")
        credit.adjustSize()
        credit.move(self.width() - credit.width() - 10,
                    self.height() - credit.height() - 10)
        self.credit_label = credit

        # Mute button
        mute = QPushButton(parent=self.ui_layer)
        mute.setIcon(QIcon("images/menu/unmute.png"))
        mute.setFixedSize(44, 44)
        mute.setIconSize(QSize(32, 32))
        mute.setStyleSheet("background:transparent; border:none;")
        mute.clicked.connect(self._toggle_mute)
        mute.move(10, self.height() - mute.height() - 10)
        mute.show()
        self.mute_btn = mute

    def _toggle_mute(self):
        """Mute or unmute the theme music."""
        if not pygame.mixer.get_init():
            return
        if self.is_muted:
            pygame.mixer.music.set_volume(DEFAULT_VOL)
            self.mute_btn.setIcon(QIcon("images/menu/unmute.png"))
        else:
            pygame.mixer.music.set_volume(0.0)
            self.mute_btn.setIcon(QIcon("images/menu/mute.png"))
        self.is_muted = not self.is_muted

    # ─── Window Resizing ─────────────────────────────────────────────────
    def resizeEvent(self, event):
        """Ensure background and footer reposition when the window is resized."""
        super().resizeEvent(event)
        self.movie_label.resize(self.size())
        self.ui_layer.resize(self.size())

        self.credit_label.move(
            self.width() - self.credit_label.width() - 10,
            self.height() - self.credit_label.height() - 10
        )
        self.mute_btn.move(
            10,
            self.height() - self.mute_btn.height() - 10
        )

    # ─── Menu / Navigation ───────────────────────────────────────────────
    def clear_overlay_layout(self):
        """Remove all widgets from the overlay layout."""
        while self.ui_layout.count():
            item = self.ui_layout.takeAt(0)
            if widget := item.widget():
                widget.setParent(None)

    def show_main_menu(self):
        """Show logo and buttons to choose Killer or Survivor roulette."""
        self.clear_overlay_layout()

        # Logo
        logo = QLabel()
        pix = QPixmap("images/menu/dbdroulettelogo.png")
        logo.setPixmap(pix.scaledToWidth(
            300, Qt.TransformationMode.SmoothTransformation
        ))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        self.ui_layout.addWidget(logo)
        self.ui_layout.addSpacing(20)

        # Killer / Survivor buttons
        killer_btn = AnimatedButton(
            "Killer Roulette", hover_color="#982c1c",
            hover_sound=self.sfx_hover, click_sound=self.sfx_click
        )
        survivor_btn = AnimatedButton(
            "Survivor Roulette", hover_color="#405c94",
            hover_sound=self.sfx_hover, click_sound=self.sfx_click
        )
        killer_btn.clicked.connect(
            lambda: self._load_perk_roulette("images/killer_perks")
        )
        survivor_btn.clicked.connect(
            lambda: self._load_perk_roulette("images/survivor_perks")
        )
        self.ui_layout.addWidget(killer_btn)
        self.ui_layout.addWidget(survivor_btn)

    def _load_perk_roulette(self, folder):
        """Replace menu with the perk spinner for the selected folder."""
        self.clear_overlay_layout()
        display = PerkDisplay(
            folder, self.show_main_menu,
            hover_sound=self.sfx_hover,
            click_sound=self.sfx_click
        )
        self.ui_layout.addWidget(display)
