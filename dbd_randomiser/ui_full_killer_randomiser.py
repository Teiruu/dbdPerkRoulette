import os, random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QPixmap

from widgets import AnimatedButton, ClickableLabel
from ui_killer_randomiser import KillerDisplay
from ui_perk_display       import PerkDisplay, IMAGE_SIZE

SPIN_INTERVAL = 100
SPIN_STEPS    = 20
PERK_CONTAINER_WIDTH  = 160
PERK_CONTAINER_HEIGHT = 160 + 60

class FullDisplay(QWidget):
    """Spin killer-perks grid → portrait+name → addons, all in one view, with per-icon reroll animations."""

    def __init__(self, back_callback, hover_sound=None, click_sound=None):
        super().__init__()
        self.back_cb = back_callback

        # Sub-widgets
        self.kd = KillerDisplay(
            back_callback=back_callback,
            hover_sound=hover_sound,
            click_sound=click_sound
        )
        self.pd = PerkDisplay(
            "images/killer_perks",
            back_callback=back_callback,
            hover_sound=hover_sound,
            click_sound=click_sound
        )

        # Hide built-in Spin/Back buttons
        for btn in (*self.kd.findChildren(AnimatedButton), *self.pd.findChildren(AnimatedButton)):
            btn.hide()

        # --- State for per-icon animations ---
        self._single_perk_idx = None
        self._single_perk_counter = 0
        self._perk_timer = QTimer(self)
        self._perk_timer.timeout.connect(self._animate_single_perk)

        self._single_addon_idx = None
        self._single_addon_counter = 0
        self._addon_timer_single = QTimer(self)
        self._addon_timer_single.timeout.connect(self._animate_single_addon)

        # --- Override click handlers and set tooltips ---
        # Portrait reroll: only portrait
        try:
            self.kd.portrait_label.clicked.disconnect()
        except TypeError:
            pass
        self.kd.portrait_label.setToolTip("Click to reroll killer portrait")
        self.kd.portrait_label.clicked.connect(lambda: self.kd._start_portrait())

        # Addons: individual reroll
        for idx, ico in enumerate(self.kd.addon_labels):
            try:
                ico.clicked.disconnect()
            except TypeError:
                pass
            ico.setToolTip("Click to reroll this addon")
            ico.clicked.connect(lambda *args, i=idx: self._reroll_addon_full(i))

        # Perks: individual reroll
        for idx, img in enumerate(self.pd.image_labels):
            try:
                img.clicked.disconnect()
            except TypeError:
                pass
            img.setToolTip("Click to reroll this perk")
            img.clicked.connect(lambda *args, i=idx: self._reroll_perk_full(i))

        # --- Layout ---
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        row = QHBoxLayout()
        row.setSpacing(60)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2×2 grid of perks
        grid = QGridLayout()
        grid.setSpacing(30)
        for idx, container in enumerate(self.pd.perk_containers):
            container.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
            container.setFixedSize(PERK_CONTAINER_WIDTH, PERK_CONTAINER_HEIGHT)
            r, c = divmod(idx, 2)
            grid.addWidget(container, r, c)
        row.addLayout(grid)

        # Big portrait in middle
        row.addWidget(self.kd.portrait_container)

        # Vertical stack of addons
        addons_v = QVBoxLayout()
        addons_v.setSpacing(40)
        addons_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for container in self.kd.addon_containers:
            addons_v.addWidget(container)
        row.addLayout(addons_v)

        main.addLayout(row)
        main.addSpacing(30)

        # Spin Everything / Back
        spin_all = AnimatedButton(
            "Spin Everything",
            hover_color="#982c1c", base_color="#222", text_color="white",
            hover_sound=hover_sound, click_sound=click_sound
        )
        spin_all.setFixedSize(220, 50)
        spin_all.clicked.connect(self._start)

        back = AnimatedButton(
            "Back",
            hover_color="#555", base_color="#111", text_color="white",
            hover_sound=hover_sound, click_sound=click_sound
        )
        back.setFixedSize(150, 50)
        back.clicked.connect(back_callback)

        main.addWidget(spin_all,    alignment=Qt.AlignmentFlag.AlignCenter)
        main.addSpacing(8)
        main.addWidget(back,        alignment=Qt.AlignmentFlag.AlignCenter)

        # Tooltip
        tip = QLabel("Tip: click any icon above to reroll it individually.", self)
        tip.setStyleSheet("color: #ccc; font-size: 8pt;")
        main.addWidget(tip, alignment=Qt.AlignmentFlag.AlignCenter)

        # Sequencer timer for full spin
        self._phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)

    def _start(self):
        """Begin full portrait → addons → perks sequence."""
        self._phase = 1
        self.kd._start_portrait()
        self._timer.start(SPIN_INTERVAL)

    def _step(self):
        if self._phase == 1 and self.kd._portrait_counter > SPIN_STEPS:
            self.kd._start_addons()
            self._phase = 2
        elif self._phase == 2 and self.kd._addon_counter > SPIN_STEPS:
            self.pd._start_spin()
            self._phase = 3
        elif self._phase == 3 and self.pd._spin_counter > SPIN_STEPS:
            self._timer.stop()

    # --- Individual reroll with animation ---
    def _reroll_perk_full(self, idx):
        self._single_perk_idx = idx
        self._single_perk_counter = 0
        self._perk_timer.start(SPIN_INTERVAL)

    def _animate_single_perk(self):
        idx = self._single_perk_idx
        self._single_perk_counter += 1
        choice = random.choice(self.pd.perk_files)
        pix = QPixmap(os.path.join(self.pd.perk_folder, choice))
        pix = pix.scaled(IMAGE_SIZE, IMAGE_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.pd.image_labels[idx].setPixmap(pix)
        if self._single_perk_counter > SPIN_STEPS:
            self._perk_timer.stop()
            self.pd._reroll_perk(idx)

    def _reroll_addon_full(self, idx):
        self._single_addon_idx = idx
        self._single_addon_counter = 0
        self._addon_timer_single.start(SPIN_INTERVAL)

    def _animate_single_addon(self):
        idx = self._single_addon_idx
        self._single_addon_counter += 1
        key = self.kd.name_label.text().replace(" ", "")
        folder = os.path.join(self.kd.addons_root, key)
        if not os.path.isdir(folder):
            self._addon_timer_single.stop()
            return
        files = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
        path = os.path.join(folder, random.choice(files))
        pix = QPixmap(path).scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.kd.addon_labels[idx].setPixmap(pix)
        if self._single_addon_counter > SPIN_STEPS:
            self._addon_timer_single.stop()
            self.kd._reroll_addon(idx)