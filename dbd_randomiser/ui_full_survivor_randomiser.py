# ui_full_survivor_randomiser.py
import os
import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QPixmap

from widgets         import AnimatedButton, ClickableLabel
from ui_perk_display import PerkDisplay
from utils           import format_perk_name

# Configuration constants
PERK_FRAME    = 160
LABEL_HEIGHT  = 60
IMAGE_SIZE    = 128
SPIN_INTERVAL = 100
SPIN_STEPS    = 20

def image_path(*parts):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "images", *parts)

class FullSurvivorDisplay(QWidget):
    """Full‑screen Survivor randomiser: portrait → item → 2 addons → 4 perks,
       with full-sequence and per-icon reroll animations."""

    def __init__(self, back_callback, hover_sound=None, click_sound=None):
        super().__init__()
        self.back_cb     = back_callback
        self.hover_sound = hover_sound
        self.click_sound = click_sound

        # Data folders
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

        self._picked_survivor = None
        self._picked_item     = None
        self._temp_item       = None  # used during item spin

        # PerkDisplay (bottom row)
        self.pd = PerkDisplay(
            self.perk_folder,
            back_callback=back_callback,
            hover_sound=hover_sound,
            click_sound=click_sound
        )
        for btn in self.pd.findChildren(AnimatedButton):
            btn.hide()

        # Placeholder graphic
        self.placeholder = QPixmap(
            image_path("survivor_perks", "helpLoadingSurvivor.png")
        ).scaled(
            IMAGE_SIZE, IMAGE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Helper to build a cell (frame + icon + label)
        def make_cell(initial_pix=None):
            cell = QWidget()
            lay  = QVBoxLayout(cell)
            lay.setContentsMargins(0,0,0,0)
            lay.setSpacing(5)
            lay.setAlignment(Qt.AlignmentFlag.AlignTop)

            frame = QWidget()
            frame.setFixedSize(PERK_FRAME, PERK_FRAME)
            frame.setStyleSheet("""
                background-color: rgba(0,0,0,150);
                border: 2px solid #222;
                border-radius: 10px;
            """)
            pfl = QVBoxLayout(frame)
            pfl.setContentsMargins(0,0,0,0)
            pfl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon = ClickableLabel()
            icon.setFixedSize(IMAGE_SIZE, IMAGE_SIZE)
            if initial_pix:
                icon.setPixmap(initial_pix)
            pfl.addWidget(icon)

            lay.addWidget(frame)
            txt = QLabel("", self)
            txt.setFixedSize(PERK_FRAME, LABEL_HEIGHT)
            txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            txt.setWordWrap(True)
            txt.setStyleSheet("""
                color: white; font-size: 10pt; font-weight: bold;
                background: transparent;
            """)
            lay.addWidget(txt)

            cell.setFixedSize(PERK_FRAME, PERK_FRAME + LABEL_HEIGHT)
            return cell, icon, txt

        # Build each slot **with** placeholder
        self.portrait_cell, self.portrait_icon, self.portrait_txt = make_cell(self.placeholder)
        self.portrait_icon.setToolTip("Click to reroll survivor portrait")
        self.portrait_icon.clicked.connect(self._start_survivor_spin)

        self.item_cell, self.item_icon, self.item_txt = make_cell(self.placeholder)
        self.item_icon.setToolTip("Click to reroll item (resets addons)")
        self.item_icon.clicked.connect(self._start_item_spin)

        self.addon_cells = []
        self.addon_icons = []
        self.addon_txts  = []
        for idx in range(2):
            c, ico, txt = make_cell(self.placeholder)
            ico.setToolTip("Click to reroll this addon")
            ico.clicked.connect(lambda *args, i=idx: self._start_addon_spin(i))
            self.addon_cells.append(c)
            self.addon_icons.append(ico)
            self.addon_txts.append(txt)

        # Layout grid
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid = QGridLayout()
        grid.setSpacing(30)
        grid.addWidget(self.portrait_cell, 0, 0)
        grid.addWidget(self.item_cell,     0, 1)
        grid.addWidget(self.addon_cells[0], 0, 2)
        grid.addWidget(self.addon_cells[1], 0, 3)
        for i, cont in enumerate(self.pd.perk_containers):
            cont.setFixedSize(PERK_FRAME, PERK_FRAME + LABEL_HEIGHT)
            grid.addWidget(cont, 1, i)
        main.addLayout(grid)
        main.addSpacing(20)

        # Buttons
        btn_spin = AnimatedButton(
            "Spin Everything",
            hover_color="#405c94", base_color="#222", text_color="white",
            hover_sound=hover_sound, click_sound=click_sound
        )
        btn_spin.setFixedSize(220,50)
        btn_spin.clicked.connect(self._start)

        btn_back = AnimatedButton(
            "Back",
            hover_color="#555", base_color="#111", text_color="white",
            hover_sound=hover_sound, click_sound=click_sound
        )
        btn_back.setFixedSize(150,50)
        btn_back.clicked.connect(back_callback)

        main.addWidget(btn_spin, alignment=Qt.AlignmentFlag.AlignCenter)
        main.addSpacing(5)
        main.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        tip = QLabel("Tip: click any icon above to reroll it individually.", self)
        tip.setStyleSheet("color:#ccc;font-size:8pt;")
        main.addWidget(tip, alignment=Qt.AlignmentFlag.AlignCenter)

        # Full‑sequence timer
        self._phase = 0
        self._cnt   = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)

        # Single‑slot timer
        self._spin_type    = None
        self._spin_idx     = None
        self._spin_counter = 0
        self._slot_timer   = QTimer(self)
        self._slot_timer.timeout.connect(self._animate_slot_spin)

    def _start(self):
        # Reset icons to placeholders before animating
        self._phase, self._cnt = 1, 0
        self.portrait_icon.setPixmap(self.placeholder)
        self.item_icon.setPixmap(self.placeholder)
        for ico, txt in zip(self.addon_icons, self.addon_txts):
            ico.setPixmap(self.placeholder)
            txt.clear()
        self.pd._timer.stop()
        self._timer.start(SPIN_INTERVAL)

    def _step(self):
        self._cnt += 1
        # Phase 1: portrait
        if self._phase == 1:
            choice = random.choice(self.survivors)
            pix = QPixmap(os.path.join(self.survivor_folder, choice))\
                  .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.portrait_icon.setPixmap(pix)
            if self._cnt >= SPIN_STEPS:
                self._picked_survivor = choice
                self.portrait_txt.setText(format_perk_name(choice))
                self._phase, self._cnt = 2, 0

        # Phase 2: item (and reset addons)
        elif self._phase == 2:
            choice = random.choice(self.items)
            pix = QPixmap(os.path.join(self.item_folder, choice))\
                  .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.item_icon.setPixmap(pix)
            if self._cnt >= SPIN_STEPS:
                self._temp_item = choice
                self.item_txt.setText(format_perk_name(choice))
                # reset addons to placeholder
                for ico, txt in zip(self.addon_icons, self.addon_txts):
                    ico.setPixmap(self.placeholder)
                    txt.clear()
                self._phase, self._cnt = 3, 0

        # Phase 3: addons
        elif self._phase == 3:
            folder = os.path.join(self.addons_root, os.path.splitext(self._temp_item)[0])
            files  = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
            for ico in self.addon_icons:
                fn = random.choice(files)
                pix = QPixmap(os.path.join(folder, fn))\
                      .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                ico.setPixmap(pix)
            if self._cnt >= SPIN_STEPS:
                picks = random.sample(files, min(2, len(files)))
                for ico, txt, fn in zip(self.addon_icons, self.addon_txts, picks):
                    pix = QPixmap(os.path.join(folder, fn))\
                          .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    ico.setPixmap(pix)
                    txt.setText(format_perk_name(fn))
                self._phase, self._cnt = 4, 0

        # Phase 4: perks
        elif self._phase == 4:
            self.pd._start_spin()
            self._timer.stop()

    # — Single‑slot reroll animations —

    def _start_survivor_spin(self):
        self._spin_type    = "survivor"
        self._spin_counter = 0
        self._slot_timer.start(SPIN_INTERVAL)

    def _start_item_spin(self):
        # reset addons immediately
        for ico, txt in zip(self.addon_icons, self.addon_txts):
            ico.setPixmap(self.placeholder)
            txt.clear()
        self._spin_type    = "item_sequence"
        self._spin_counter = 0
        self._slot_timer.start(SPIN_INTERVAL)

    def _start_addon_spin(self, idx):
        self._spin_type    = "addon"
        self._spin_idx     = idx
        self._spin_counter = 0
        self._slot_timer.start(SPIN_INTERVAL)

    def _animate_slot_spin(self):
        self._spin_counter += 1

        if self._spin_type == "survivor":
            choice = random.choice(self.survivors)
            pix = QPixmap(os.path.join(self.survivor_folder, choice))\
                  .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.portrait_icon.setPixmap(pix)
            if self._spin_counter >= SPIN_STEPS:
                self._slot_timer.stop()
                self._reroll_survivor()

        elif self._spin_type == "item_sequence":
            # first SPIN_STEPS ticks animate the item
            half = SPIN_STEPS
            if self._spin_counter <= half:
                choice = random.choice(self.items)
                pix = QPixmap(os.path.join(self.item_folder, choice))\
                      .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.item_icon.setPixmap(pix)
                if self._spin_counter == half:
                    self._temp_item = choice
                    self.item_txt.setText(format_perk_name(choice))
            # next SPIN_STEPS ticks animate the two addons
            elif self._spin_counter <= 2*half:
                folder = os.path.join(self.addons_root, os.path.splitext(self._temp_item)[0])
                files  = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
                for ico in self.addon_icons:
                    fn = random.choice(files)
                    pix = QPixmap(os.path.join(folder, fn))\
                          .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    ico.setPixmap(pix)
                if self._spin_counter == 2*half:
                    self._slot_timer.stop()
                    # finalize item + addons
                    self._picked_item = os.path.splitext(self._temp_item)[0]
                    self._reroll_item()


        elif self._spin_type == "addon":

            # if no item has ever been picked, abort
            if not self._picked_item:
                self._slot_timer.stop()
                return
            folder = os.path.join(self.addons_root, self._picked_item)
            files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
            fn = random.choice(files)
            pix = QPixmap(os.path.join(folder, fn))\
                    .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)

            self.addon_icons[self._spin_idx].setPixmap(pix)
            if self._spin_counter >= SPIN_STEPS:
                self._slot_timer.stop()
                self._reroll_addon(self._spin_idx)

    # — Reroll helpers —

    def _reroll_survivor(self):
        pick = random.choice(self.survivors)
        pix  = QPixmap(os.path.join(self.survivor_folder, pick))\
               .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.portrait_icon.setPixmap(pix)
        self.portrait_txt.setText(format_perk_name(pick))
        self._picked_survivor = pick

    def _reroll_item(self):
        pick = self._temp_item or random.choice(self.items)
        pix  = QPixmap(os.path.join(self.item_folder, pick))\
               .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.item_icon.setPixmap(pix)
        self.item_txt.setText(format_perk_name(pick))
        self._picked_item = os.path.splitext(pick)[0]
        # cascade to both addons
        for i in range(2):
            self._reroll_addon(i)

    def _reroll_addon(self, idx):
        folder = os.path.join(self.addons_root, self._picked_item)
        files  = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
        fn     = random.choice(files)
        pix    = QPixmap(os.path.join(folder, fn))\
                 .scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.addon_icons[idx].setPixmap(pix)
        self.addon_txts[idx].setText(format_perk_name(fn))
