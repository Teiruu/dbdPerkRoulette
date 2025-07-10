"""
Main application window for DBD Perk Roulette.
Handles background animation, audio, and navigation.
"""

import os
import pygame
from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtGui    import QMovie, QPixmap, QIcon
from PyQt6.QtCore   import Qt, QTimer, QSize

from ui_perk_display             import PerkDisplay
from widgets                     import AnimatedButton
from ui_killer_randomiser        import KillerDisplay
from ui_full_killer_randomiser   import FullDisplay  # renamed

# ─── Constants ─────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 1000
WINDOW_HEIGHT = 600

GIF_PATHS      = ["images/menu/fog.gif", "images/menu/fogreverse.gif"]
GIF_INTERVAL   = 10_000
GIF_PAUSE      = 500

THEME_MUSIC    = "media/dbdtheme.mp3"
SFX_HOVER      = "media/buttonhover.mp3"
SFX_CLICK      = "media/buttonselect.mp3"
DEFAULT_VOL    = 0.1

class MainWindow(QMainWindow):
    """Primary window: background, audio, and menu navigation."""

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

    def _setup_background(self):
        self.gif_index = 0
        self.movie_label = QLabel(self)
        self.movie_label.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.movie_label.setScaledContents(True)
        self.movie = QMovie(GIF_PATHS[0])
        self.movie_label.setMovie(self.movie)
        self.movie.start()
        self.gif_timer = QTimer(self)
        self.gif_timer.timeout.connect(self._pause_and_switch_gif)
        self.gif_timer.start(GIF_INTERVAL)

    def _pause_and_switch_gif(self):
        QTimer.singleShot(GIF_PAUSE, self._switch_background_gif)

    def _switch_background_gif(self):
        self.gif_index = (self.gif_index + 1) % len(GIF_PATHS)
        self.movie.stop()
        self.movie = QMovie(GIF_PATHS[self.gif_index])
        self.movie_label.setMovie(self.movie)
        self.movie.start()
        self.gif_timer.start(GIF_INTERVAL)

    def _setup_audio(self):
        pygame.mixer.init()
        try:
            pygame.mixer.music.load(THEME_MUSIC)
            pygame.mixer.music.set_volume(DEFAULT_VOL)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"[ERROR] Loading theme music: {e}")

        try:
            self.sfx_hover = pygame.mixer.Sound(SFX_HOVER)
            self.sfx_click = pygame.mixer.Sound(SFX_CLICK)
            self.sfx_hover.set_volume(0.2)
            self.sfx_click.set_volume(0.2)
        except pygame.error:
            print("[WARNING] Could not load SFX.")
            self.sfx_hover = self.sfx_click = None

    def _setup_ui_layer(self):
        self.ui_layer = QWidget(self)
        self.ui_layer.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.ui_layer.setStyleSheet("background: transparent;")
        self.ui_layout = QVBoxLayout(self.ui_layer)
        self.ui_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _add_footer(self):
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
        if not pygame.mixer.get_init():
            return
        if self.is_muted:
            pygame.mixer.music.set_volume(DEFAULT_VOL)
            self.mute_btn.setIcon(QIcon("images/menu/unmute.png"))
        else:
            pygame.mixer.music.set_volume(0.0)
            self.mute_btn.setIcon(QIcon("images/menu/mute.png"))
        self.is_muted = not self.is_muted

    def resizeEvent(self, event):
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

    def clear_overlay_layout(self):
        while self.ui_layout.count():
            item = self.ui_layout.takeAt(0)
            if widget := item.widget():
                widget.setParent(None)

    def show_main_menu(self):
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
        killer_btn.clicked.connect(self.show_killer_menu)
        survivor_btn.clicked.connect(
            lambda: self._load_perk_roulette("images/survivor_perks")
        )
        self.ui_layout.addWidget(killer_btn)
        self.ui_layout.addWidget(survivor_btn)

    def _load_perk_roulette(self, folder):
        self.clear_overlay_layout()
        display = PerkDisplay(
            folder, self.show_main_menu,
            hover_sound=self.sfx_hover,
            click_sound=self.sfx_click
        )
        self.ui_layout.addWidget(display)

    def show_killer_menu(self):
        self.clear_overlay_layout()

        kb = AnimatedButton("Killer Randomiser", hover_color="#982c1c",
                            hover_sound=self.sfx_hover, click_sound=self.sfx_click)
        kb.clicked.connect(self.show_killer_randomiser)

        pk = AnimatedButton("Perk Randomiser", hover_color="#982c1c",
                            hover_sound=self.sfx_hover, click_sound=self.sfx_click)
        pk.clicked.connect(
            lambda: self._load_perk_roulette("images/killer_perks")
        )

        fb = AnimatedButton("Full Randomiser", hover_color="#982c1c",
                            hover_sound=self.sfx_hover, click_sound=self.sfx_click)
        fb.clicked.connect(self.show_full_randomiser)

        back = AnimatedButton("Back to Main Menu", hover_color="#555",
                              base_color="#111", text_color="white",
                              hover_sound=self.sfx_hover,
                              click_sound=self.sfx_click)
        back.clicked.connect(self.show_main_menu)

        for w in (kb, pk, fb, back):
            w.setFixedSize(250, 50)
            self.ui_layout.addWidget(w, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_killer_randomiser(self):
        self.clear_overlay_layout()
        kd = KillerDisplay(
            back_callback=self.show_killer_menu,
            hover_sound=self.sfx_hover,
            click_sound=self.sfx_click
        )
        self.ui_layout.addWidget(kd)

    def show_full_randomiser(self):
        self.clear_overlay_layout()
        fd = FullDisplay(
            back_callback=self.show_killer_menu,
            hover_sound=self.sfx_hover,
            click_sound=self.sfx_click
        )
        self.ui_layout.addWidget(fd)
