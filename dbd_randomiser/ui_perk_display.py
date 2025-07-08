"""
PerkDisplay widget: shows four perk slots and a 'Spin' button
to randomly reveal perks from a given folder.
"""

import os
import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer

from widgets import AnimatedButton
from utils import format_perk_name

# ─── Configuration ───────────────────────────────────────────────────────
FRAME_SIZE     = 160
IMAGE_SIZE     = 128
SPIN_INTERVAL  = 100   # ms between frames
SPIN_STEPS     = 20    # number of frames to show

# ─── PerkDisplay ─────────────────────────────────────────────────────────
class PerkDisplay(QWidget):
    """Displays and spins four random perks from a folder."""

    def __init__(self, perk_folder, back_callback, hover_sound=None, click_sound=None):
        super().__init__()
        self.perk_folder     = perk_folder
        self.back_callback   = back_callback
        self.hover_sound     = hover_sound
        self.click_sound     = click_sound

        # Gather all perk images, excluding the 'helpLoading' placeholder
        self.perk_files = [
            f for f in os.listdir(perk_folder)
            if not f.startswith("helpLoading")
        ]

        # Choose the correct placeholder image
        placeholder_name = (
            "helpLoadingKiller.png"
            if "killer" in perk_folder.lower()
            else "helpLoadingSurvivor.png"
        )
        self.placeholder_path = os.path.join(perk_folder, placeholder_name)

        self._init_ui()

    def _init_ui(self):
        """Construct UI: four image slots + Spin/Back buttons."""
        self.setStyleSheet("background: transparent;")

        self.image_labels = []
        self.text_labels  = []

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ─ Perk slots ─────────────────────────────────────────────────────
        self.perk_layout = QHBoxLayout()
        self.perk_layout.setSpacing(30)
        self.perk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for _ in range(4):
            # Frame to hold the image
            frame = QFrame()
            frame.setFixedSize(FRAME_SIZE, FRAME_SIZE)
            frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0,0,0,150);
                    border: 2px solid #222;
                    border-radius: 10px;
                }
            """)

            # Layout inside the frame, centered
            image_layout = QVBoxLayout(frame)
            image_layout.setContentsMargins(0, 0, 0, 0)
            image_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            image_label = QLabel()
            image_label.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Load placeholder
            pix = QPixmap(self.placeholder_path)
            if pix.isNull():
                print(f"[ERROR] Missing placeholder: {self.placeholder_path}")
            else:
                pix = pix.scaled(
                    IMAGE_SIZE, IMAGE_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            image_label.setPixmap(pix)
            image_layout.addWidget(image_label)

            # Label for the perk name
            text_label = QLabel("")
            text_label.setFixedSize(FRAME_SIZE, 40)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 10pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)

            # Container for frame + text
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(frame)
            container_layout.addSpacing(5)
            container_layout.addWidget(text_label)

            self.perk_layout.addWidget(container)
            self.image_labels.append(image_label)
            self.text_labels.append(text_label)

        main_layout.addLayout(self.perk_layout)
        main_layout.addSpacing(30)

        # ── Buttons ─────────────────────────────────────────────────────────
        self.spin_button = AnimatedButton(
            "Spin", hover_color="#982c1c", base_color="#222", text_color="white",
            hover_sound=self.hover_sound, click_sound=self.click_sound
        )
        self.spin_button.setFixedSize(200, 50)
        self.spin_button.clicked.connect(self._start_spin)

        back_button = AnimatedButton(
            "Back to Menu", hover_color="#555", base_color="#111", text_color="white",
            hover_sound=self.hover_sound, click_sound=self.click_sound
        )
        back_button.setFixedSize(150, 50)
        back_button.clicked.connect(self.back_callback)

        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # pass alignment to addWidget so each button is centered in the column
        button_layout.addWidget(self.spin_button, alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addSpacing(8)
        button_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(button_layout)


        # ─ Timer for spin animation ────────────────────────────────────────
        self._spin_counter = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_spin)

    def _start_spin(self):
        """Begin cycling through random perks."""
        self._spin_counter = 0
        self._timer.start(SPIN_INTERVAL)

    def _animate_spin(self):
        """Show random frames during spin."""
        self._spin_counter += 1
        for label in self.image_labels:
            fname = random.choice(self.perk_files)
            pix = QPixmap(os.path.join(self.perk_folder, fname))
            pix = pix.scaled(
                IMAGE_SIZE, IMAGE_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(pix)

        if self._spin_counter > SPIN_STEPS:
            self._timer.stop()
            self._reveal_perks()

    def _reveal_perks(self):
        """Pick and display four unique perks with names."""
        try:
            picks = random.sample(self.perk_files, len(self.image_labels))
            for i, fname in enumerate(picks):
                path = os.path.join(self.perk_folder, fname)
                pix = QPixmap(path)
                if pix.isNull():
                    print(f"[ERROR] Could not load: {path}")
                    continue
                pix = pix.scaled(
                    IMAGE_SIZE, IMAGE_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_labels[i].setPixmap(pix)
                self.text_labels[i].setText(format_perk_name(fname))
        except Exception as e:
            print(f"[EXCEPTION] reveal_perks: {e}")

