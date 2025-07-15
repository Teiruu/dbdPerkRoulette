# ui_full_survivor_randomiser.py
import os
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui  import QPixmap

from widgets         import AnimatedButton
from ui_perk_display import PerkDisplay
from utils           import format_perk_name

# ─── Configuration ───────────────────────────────────────────────────────
PERK_FRAME    = 160   # width/height of each “cell” frame
LABEL_HEIGHT  = 60    # height of the label under each frame
IMAGE_SIZE    = 128   # size of the icon inside each frame
SPIN_INTERVAL = 100   # ms per animation step
SPIN_STEPS    = 20    # frames per phase

def image_path(*parts):
    """Build absolute path into your images/ folder."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "images", *parts)


class FullSurvivorDisplay(QWidget):
    """Full‐screen Survivor randomiser: portrait → item → 2 addons → 4 perks"""

    def __init__(self, back_callback, hover_sound=None, click_sound=None):
        super().__init__()
        self.back_cb     = back_callback
        self.hover_sound = hover_sound
        self.click_sound = click_sound

        # ─── Data folders & file lists ─────────────────────────────────
        self.survivor_folder = image_path("survivors")
        self.item_folder     = image_path("survivor_items")
        self.addons_root     = image_path("survivor_items", "addons")
        self.perk_folder     = image_path("survivor_perks")

        self.survivors = [
            f for f in os.listdir(self.survivor_folder)
            if f.lower().endswith(".png")
        ]
        self.items     = [
            f for f in os.listdir(self.item_folder)
            if f.lower().endswith(".png")
        ]

        # keep track of exactly what was picked
        self._picked_survivor = None
        self._picked_item     = None

        # ─── Build a PerkDisplay for the bottom row & hide its buttons ─
        self.pd = PerkDisplay(
            self.perk_folder,
            back_callback=back_callback,
            hover_sound=hover_sound,
            click_sound=click_sound
        )
        for btn in self.pd.findChildren(AnimatedButton):
            btn.hide()

        # ─── A little helper to build each cell (frame + label) ───────
        def make_cell(initial_pix: QPixmap = None):
            cell = QWidget()
            lay  = QVBoxLayout(cell)
            lay.setContentsMargins(0,0,0,0)
            lay.setSpacing(5)
            lay.setAlignment(Qt.AlignmentFlag.AlignTop)

            frame = QFrame()
            frame.setFixedSize(PERK_FRAME, PERK_FRAME)
            frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(0,0,0,150);
                    border: 2px solid #222;
                    border-radius: 10px;
                }
            """)
            pfl = QVBoxLayout(frame)
            pfl.setContentsMargins(0,0,0,0)
            pfl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon = QLabel()
            icon.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
            if initial_pix:
                icon.setPixmap(initial_pix)
            pfl.addWidget(icon)
            lay.addWidget(frame)

            txt = QLabel("")
            txt.setFixedSize(PERK_FRAME, LABEL_HEIGHT)
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
            lay.addWidget(txt)

            cell.setFixedSize(PERK_FRAME, PERK_FRAME + LABEL_HEIGHT)
            return cell, icon, txt

        # ─── Create a placeholder pixmap for initial state ─────────────
        placeholder = QPixmap(
            image_path("survivor_perks", "helpLoadingSurvivor.png")
        ).scaled(
            IMAGE_SIZE, IMAGE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # ─── Build the eight cells ─────────────────────────────────────
        #  0) Portrait
        self.portrait_cell, self.portrait_icon, self.portrait_txt = \
            make_cell(placeholder)

        #  1) Item
        self.item_cell, self.item_icon, self.item_txt = \
            make_cell(placeholder)

        #  2–3) Two item‐specific addons
        self.addon_cells = []
        self.addon_icons = []
        self.addon_txts  = []
        for _ in range(2):
            c, ico, t = make_cell(placeholder)
            self.addon_cells.append(c)
            self.addon_icons.append(ico)
            self.addon_txts.append(t)

        # ─── Lay everything out in a 2×4 grid ──────────────────────────
        main_l = QVBoxLayout(self)
        main_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid = QGridLayout()
        grid.setSpacing(30)

        # Row 0: portrait | item | addon0 | addon1
        grid.addWidget(self.portrait_cell, 0, 0)
        grid.addWidget(self.item_cell,     0, 1)
        grid.addWidget(self.addon_cells[0], 0, 2)
        grid.addWidget(self.addon_cells[1], 0, 3)

        # Row 1: the 4 perks from PerkDisplay
        for i, cont in enumerate(self.pd.perk_containers):
            cont.setFixedSize(PERK_FRAME, PERK_FRAME + LABEL_HEIGHT)
            grid.addWidget(cont, 1, i)

        main_l.addLayout(grid)
        main_l.addSpacing(20)

        # ─── “Spin Everything” / “Back to Menu” ───────────────────────
        btn_spin = AnimatedButton(
            "Spin Everything",
            hover_color="#405c94", base_color="#222", text_color="white",
            hover_sound=hover_sound, click_sound=click_sound
        )
        btn_spin.setFixedSize(220, 50)
        btn_spin.clicked.connect(self._start)

        btn_back = AnimatedButton(
            "Back",
            hover_color="#555", base_color="#111", text_color="white",
            hover_sound=hover_sound, click_sound=click_sound
        )
        btn_back.setFixedSize(150, 50)
        btn_back.clicked.connect(back_callback)

        main_l.addWidget(btn_spin, alignment=Qt.AlignmentFlag.AlignCenter)
        main_l.addSpacing(5)
        main_l.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        # ─── Sequencer timer ───────────────────────────────────────────
        self._phase = 0
        self._cnt   = 0   # ←── initialise the missing counter!
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)


    def _start(self):
        """Reset everything and begin phase 1 (portrait spin)."""
        self._phase = 1
        self._cnt   = 0

        # clear old labels
        self.portrait_txt.clear()
        self.item_txt.clear()
        for t in self.addon_txts:
            t.clear()

        # clear icons back to placeholder if you want
        self._timer.start(SPIN_INTERVAL)


    def _step(self):
        """Drive through portrait → item → addons → perks."""
        # Phase 1: portrait
        if self._phase == 1:
            self._cnt += 1
            pick = random.choice(self.survivors)
            pix = QPixmap(os.path.join(self.survivor_folder, pick))\
                  .scaled(IMAGE_SIZE, IMAGE_SIZE,
                          Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
            self.portrait_icon.setPixmap(pix)

            if self._cnt >= SPIN_STEPS:
                self._picked_survivor = pick
                self.portrait_txt.setText(format_perk_name(pick))
                self._phase = 2
                self._cnt   = 0

        # Phase 2: item
        elif self._phase == 2:
            self._cnt += 1
            choice = random.choice(self.items)
            pix = QPixmap(os.path.join(self.item_folder, choice))\
                  .scaled(IMAGE_SIZE, IMAGE_SIZE,
                          Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
            self.item_icon.setPixmap(pix)

            if self._cnt >= SPIN_STEPS:
                self._picked_item = choice
                self.item_txt.setText(format_perk_name(choice))
                self._phase = 3
                self._cnt   = 0

        # Phase 3: item‐specific addons
        elif self._phase == 3:
            self._cnt += 1
            folder = os.path.join(
                self.addons_root,
                os.path.splitext(self._picked_item)[0]
            )
            all_fns = [f for f in os.listdir(folder) if f.lower().endswith(".png")]

            # preview two random addons
            for ico in self.addon_icons:
                fn = random.choice(all_fns)
                pix = QPixmap(os.path.join(folder, fn))\
                      .scaled(IMAGE_SIZE, IMAGE_SIZE,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
                ico.setPixmap(pix)

            if self._cnt >= SPIN_STEPS:
                picks = random.sample(all_fns, min(2, len(all_fns)))
                for fn, ico, txt in zip(picks, self.addon_icons, self.addon_txts):
                    pix = QPixmap(os.path.join(folder, fn))\
                          .scaled(IMAGE_SIZE, IMAGE_SIZE,
                                  Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
                    ico.setPixmap(pix)
                    txt.setText(format_perk_name(fn))

                self._phase = 4
                self._cnt   = 0

        # Phase 4: trigger the perk‐spin and stop
        elif self._phase == 4:
            self.pd._start_spin()
            self._timer.stop()
