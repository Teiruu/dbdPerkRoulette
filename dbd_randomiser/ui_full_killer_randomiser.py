import random
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtCore    import Qt, QTimer
from widgets         import AnimatedButton
from ui_killer_randomiser import KillerDisplay
from ui_perk_display       import PerkDisplay

SPIN_INTERVAL = 100
SPIN_STEPS    = 20

# match PerkDisplay.FRAME_SIZE + text area
PERK_CONTAINER_WIDTH  = 160
PERK_CONTAINER_HEIGHT = 160 + 60  # 160 for frame, ~60 for label+spacing

class FullDisplay(QWidget):
    """Spin killer-perks grid → portrait+name → addons, all in one view."""

    def __init__(self, back_callback, hover_sound=None, click_sound=None):
        super().__init__()
        self.back_cb = back_callback

        # 1) create sub-widgets
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

        # hide their built-in Spin/Back buttons
        for btn in (*self.kd.findChildren(AnimatedButton),
                    *self.pd.findChildren(AnimatedButton)):
            btn.hide()

        # ── overall vertical layout ───────────────────────────────────
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── one horizontal row: perks grid | portrait | addons stack ──
        row = QHBoxLayout()
        row.setSpacing(60)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # a) 2×2 grid of perks
        grid = QGridLayout()
        grid.setSpacing(30)
        for idx, container in enumerate(self.pd.perk_containers):
            # force a consistent container size & top alignment
            container.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
            container.setFixedSize(
                PERK_CONTAINER_WIDTH,
                PERK_CONTAINER_HEIGHT
            )

            r, c = divmod(idx, 2)
            grid.addWidget(container, r, c)

        row.addLayout(grid)

        # b) big portrait+name in middle
        row.addWidget(self.kd.portrait_container)

        # c) vertical stack of addons on right
        addons_v = QVBoxLayout()
        addons_v.setSpacing(40)
        addons_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for container in self.kd.addon_containers:
            addons_v.addWidget(container)
        row.addLayout(addons_v)

        main.addLayout(row)
        main.addSpacing(30)

        # ── single “Spin Everything” + “Back to Menu” ───────────────
        spin_all = AnimatedButton(
            "Spin Everything",
            hover_color="#982c1c", base_color="#222", text_color="white",
            hover_sound=hover_sound, click_sound=click_sound
        )
        spin_all.setFixedSize(220, 50)
        spin_all.clicked.connect(self._start)

        back = AnimatedButton(
            "Back to Menu",
            hover_color="#555", base_color="#111", text_color="white",
            hover_sound=hover_sound, click_sound=click_sound
        )
        back.setFixedSize(150, 50)
        back.clicked.connect(back_callback)

        main.addWidget(spin_all, alignment=Qt.AlignmentFlag.AlignCenter)
        main.addSpacing(8)
        main.addWidget(back,    alignment=Qt.AlignmentFlag.AlignCenter)

        # ── one timer to sequence through the three phases ────────────
        self._phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)

    def _start(self):
        """Begin phase 1: portrait shuffle."""
        self._phase = 1
        self.kd._start_portrait()
        self._timer.start(SPIN_INTERVAL)

    def _step(self):
        # once portrait is done, launch addons
        if   self._phase == 1 and self.kd._portrait_counter > SPIN_STEPS:
            self.kd._start_addons()
            self._phase = 2

        # once addons are done, launch perks
        elif self._phase == 2 and self.kd._addon_counter > SPIN_STEPS:
            self.pd._start_spin()
            self._phase = 3

        # once perks are done, stop everything
        elif self._phase == 3 and self.pd._spin_counter > SPIN_STEPS:
            self._timer.stop()
