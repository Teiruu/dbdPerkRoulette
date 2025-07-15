import os, random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QPixmap

from widgets import AnimatedButton
from utils    import format_perk_name

SPIN_INTERVAL = 100
SPIN_STEPS    = 20

def image_path(*parts):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "images", *parts)

class SurvivorDisplay(QWidget):
    """Spin survivor portrait → item → item‐addons (2) → show names."""

    def __init__(self, back_callback, hover_sound=None, click_sound=None):
        super().__init__()
        self.back_cb     = back_callback
        self.hover_sound = hover_sound
        self.click_sound = click_sound

        # ── data dirs ───────────────────────────────────────────────
        self.portrait_dir = image_path("survivors")
        self.item_dir     = image_path("survivor_items")
        self.addons_root  = image_path("survivor_items", "addons")

        # list portraits
        self.portraits = [f for f in os.listdir(self.portrait_dir) if f.lower().endswith(".png")]
        # list items (flashlight.png, key.png, map.png, medkit.png, toolbox.png)
        self.items     = [f for f in os.listdir(self.item_dir) if f.lower().endswith(".png")]

        # placeholder
        self.placeholder = QPixmap(image_path("survivor_perks","helpLoadingSurvivor.png"))\
            .scaled(200,200,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)

        # ── build UI ──────────────────────────────────────────────────
        self.setStyleSheet("background:transparent;")
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # portrait slot
        self.portrait_lbl = QLabel()
        self.portrait_lbl.setFixedSize(200,200)
        self.portrait_lbl.setPixmap(self.placeholder)
        self.portrait_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.portrait_lbl)
        root.addSpacing(10)

        # item slot
        self.item_lbl = QLabel()
        self.item_lbl.setFixedSize(160,160)
        self.item_lbl.setPixmap(self.placeholder)
        self.item_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.item_lbl)
        root.addSpacing(10)

        # item‐name & addon names placeholders
        self.item_name = QLabel("", self)
        self.item_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.item_name.setWordWrap(True)
        self.item_name.setStyleSheet("color:white; font-size:10pt; font-weight:bold;")
        root.addWidget(self.item_name)
        root.addSpacing(20)

        # two addon slots side by side
        addons_row = QHBoxLayout(); addons_row.setSpacing(40)
        self.addon_lbls  = []
        self.addon_names = []
        for _ in range(2):
            col = QVBoxLayout(); col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            a_img = QLabel(); a_img.setFixedSize(100,100)
            a_img.setPixmap(self.placeholder.scaled(100,100,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            a_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            a_txt = QLabel("", self)
            a_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            a_txt.setWordWrap(True)
            a_txt.setStyleSheet("color:white; font-size:9pt; font-weight:bold;")
            col.addWidget(a_img)
            col.addSpacing(5)
            col.addWidget(a_txt)
            addons_row.addLayout(col)
            self.addon_lbls.append(a_img)
            self.addon_names.append(a_txt)

        root.addLayout(addons_row)
        root.addSpacing(30)

        # spin / back
        btn_spin = AnimatedButton("Spin", hover_color="#405c94", base_color="#222", text_color="white",
                                  hover_sound=self.hover_sound, click_sound=self.click_sound)
        btn_spin.setFixedSize(200,50)
        btn_spin.clicked.connect(self._phase_portrait)
        root.addWidget(btn_spin,alignment=Qt.AlignmentFlag.AlignCenter)
        btn_back = AnimatedButton("Back", hover_color="#555", base_color="#111", text_color="white",
                                  hover_sound=self.hover_sound, click_sound=self.click_sound)
        btn_back.setFixedSize(150,50)
        btn_back.clicked.connect(self.back_cb)
        root.addSpacing(8)
        root.addWidget(btn_back,alignment=Qt.AlignmentFlag.AlignCenter)

        # timers & counters
        self._phase_cnt = 0
        self._phase     = 0
        self.timer      = QTimer(self)
        self.timer.timeout.connect(self._animate)

    def _phase_portrait(self):
        self._phase = 1
        self._phase_cnt = 0
        # clear old
        self.item_lbl.clear(); self.item_name.clear()
        for img,txt in zip(self.addon_lbls,self.addon_names):
            img.setPixmap(self.placeholder); txt.clear()
        self.timer.start(SPIN_INTERVAL)

    def _animate(self):
        self._phase_cnt += 1
        if self._phase == 1:
            choice = random.choice(self.portraits)
            self.portrait_lbl.setPixmap(
                QPixmap(os.path.join(self.portrait_dir,choice)).scaled(200,200,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            )
            if self._phase_cnt>SPIN_STEPS:
                self._phase=2; self._phase_cnt=0

        elif self._phase == 2:
            choice = random.choice(self.items)
            self.item_lbl.setPixmap(
                QPixmap(os.path.join(self.item_dir,choice)).scaled(160,160,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            )
            if self._phase_cnt>SPIN_STEPS:
                self.item_name.setText(format_perk_name(choice))
                self._picked_item = os.path.splitext(choice)[0]
                self._phase=3; self._phase_cnt=0

        elif self._phase == 3:
            addon_folder = os.path.join(self.addons_root,self._picked_item)
            all_add = [f for f in os.listdir(addon_folder) if f.lower().endswith('.png')]
            for lbl in self.addon_lbls:
                fn = random.choice(all_add)
                lbl.setPixmap(
                    QPixmap(os.path.join(addon_folder,fn)).scaled(100,100,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                )
            if self._phase_cnt>SPIN_STEPS:
                self._addon_files = random.sample(all_add,2)
                self._phase=4; self._phase_cnt=0

        elif self._phase == 4:
            # reveal exactly 2 and names
            addon_folder = os.path.join(self.addons_root,self._picked_item)
            for lbl,txt,fn in zip(self.addon_lbls,self.addon_names,self._addon_files):
                lbl.setPixmap(
                    QPixmap(os.path.join(addon_folder,fn)).scaled(100,100,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                )
                txt.setText(format_perk_name(fn))
            self.timer.stop()
