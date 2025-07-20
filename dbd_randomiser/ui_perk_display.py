# ui_perk_display.py
import os
import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QPixmap

from widgets import AnimatedButton, ClickableLabel
from utils    import format_perk_name

FRAME_SIZE    = 160
IMAGE_SIZE    = 128
SPIN_INTERVAL = 100
SPIN_STEPS    = 20

class PerkDisplay(QWidget):
    """Displays and spins four random perks from a folder, with per‑icon reroll."""

    def __init__(self, perk_folder, back_callback, hover_sound=None, click_sound=None):
        super().__init__()
        self.perk_folder   = perk_folder
        self.back_callback = back_callback
        self.hover_sound   = hover_sound
        self.click_sound   = click_sound

        # Gather all perk images
        self.perk_files = [
            f for f in os.listdir(perk_folder)
            if not f.startswith("helpLoading")
        ]
        placeholder_name = (
            "helpLoadingKiller.png"
            if "killer" in perk_folder.lower()
            else "helpLoadingSurvivor.png"
        )
        self.placeholder_path = os.path.join(perk_folder, placeholder_name)

        # UI state
        self.image_labels    = []
        self.text_labels     = []
        self.perk_containers = []

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Perk slots
        row = QHBoxLayout()
        row.setSpacing(30)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for idx in range(4):
            # Frame + icon
            frame = QFrame()
            frame.setFixedSize(FRAME_SIZE, FRAME_SIZE)
            frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0,0,0,150);
                    border: 2px solid #222;
                    border-radius: 10px;
                }
            """)
            lay = QVBoxLayout(frame)
            lay.setContentsMargins(0,0,0,0)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            img = ClickableLabel()
            img.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
            pix = QPixmap(self.placeholder_path).scaled(
                IMAGE_SIZE, IMAGE_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            img.setPixmap(pix)
            img.setToolTip("Click to reroll this perk")
            img.clicked.connect(lambda *args, i=idx: self._start_perk_spin(i))
            lay.addWidget(img)

            # Label
            txt = QLabel("", self)
            txt.setFixedSize(FRAME_SIZE, 60)
            txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            txt.setWordWrap(True)
            txt.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 10pt;
                    font-weight: bold;
                    background: transparent;
                }
            """)

            # Container
            cont = QWidget()
            c_lay = QVBoxLayout(cont)
            c_lay.setContentsMargins(0,0,0,0)
            c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_lay.addWidget(frame)
            c_lay.addSpacing(10)
            c_lay.addWidget(txt)

            row.addWidget(cont)
            self.perk_containers.append(cont)
            self.image_labels.append(img)
            self.text_labels.append(txt)

        main_layout.addLayout(row)
        main_layout.addSpacing(30)

        # Spin + Back
        spin_color = "#405c94" if "survivor_perks" in perk_folder else "#982c1c"
        self.spin_button = AnimatedButton(
            "Spin",
            hover_color=spin_color,
            base_color="#222",
            text_color="white",
            hover_sound=self.hover_sound,
            click_sound=self.click_sound
        )
        self.spin_button.setFixedSize(200, 50)
        self.spin_button.clicked.connect(self._start_spin)

        back_button = AnimatedButton(
            "Back",
            hover_color="#555",
            base_color="#111",
            text_color="white",
            hover_sound=self.hover_sound,
            click_sound=self.click_sound
        )
        back_button.setFixedSize(150, 50)
        back_button.clicked.connect(self.back_callback)

        btns = QVBoxLayout()
        btns.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btns.addWidget(self.spin_button, alignment=Qt.AlignmentFlag.AlignCenter)
        btns.addSpacing(8)
        btns.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(btns)

        # TIP
        tip = QLabel("Tip: click any icon above to reroll it individually.", self)
        tip.setStyleSheet("color: #ccc; font-size: 8pt;")
        main_layout.addWidget(tip, alignment=Qt.AlignmentFlag.AlignCenter)

        # Full‑group spin timer
        self._spin_counter = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_spin)

        # Single‑slot spin timer
        self._single_idx     = None
        self._single_counter = 0
        self._single_timer   = QTimer(self)
        self._single_timer.timeout.connect(self._animate_single)

    def _start_spin(self):
        self._spin_counter = 0
        self._timer.start(SPIN_INTERVAL)

    def _animate_spin(self):
        self._spin_counter += 1
        for lbl in self.image_labels:
            choice = random.choice(self.perk_files)
            pix = QPixmap(os.path.join(self.perk_folder, choice)).scaled(
                IMAGE_SIZE, IMAGE_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            lbl.setPixmap(pix)
        if self._spin_counter > SPIN_STEPS:
            self._timer.stop()
            self._reveal_perks()

    def _reveal_perks(self):
        picks = random.sample(self.perk_files, len(self.image_labels))
        for i, fname in enumerate(picks):
            path = os.path.join(self.perk_folder, fname)
            pix  = QPixmap(path).scaled(
                IMAGE_SIZE, IMAGE_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_labels[i].setPixmap(pix)
            self.text_labels[i].setText(format_perk_name(fname))

    def _start_perk_spin(self, idx):
        self._single_idx     = idx
        self._single_counter = 0
        self._single_timer.start(SPIN_INTERVAL)

    def _animate_single(self):
        i = self._single_idx
        self._single_counter += 1
        choice = random.choice(self.perk_files)
        pix = QPixmap(os.path.join(self.perk_folder, choice)).scaled(
            IMAGE_SIZE, IMAGE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_labels[i].setPixmap(pix)
        if self._single_counter > SPIN_STEPS:
            self._single_timer.stop()
            self._reroll_perk(i)

    def _reroll_perk(self, idx):
        fname = random.choice(self.perk_files)
        path  = os.path.join(self.perk_folder, fname)
        pix   = QPixmap(path).scaled(
            IMAGE_SIZE, IMAGE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_labels[idx].setPixmap(pix)
        self.text_labels[idx].setText(format_perk_name(fname))
