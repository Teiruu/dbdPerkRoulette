import os
import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QPixmap

from widgets import AnimatedButton, ClickableLabel
from utils    import format_perk_name

SPIN_INTERVAL = 100
SPIN_STEPS    = 20

def image_path(*parts):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "images", *parts)

class KillerDisplay(QWidget):
    def __init__(self, back_callback, hover_sound=None, click_sound=None):
        super().__init__()
        self.back_cb     = back_callback
        self.hover_sound = hover_sound
        self.click_sound = click_sound
        self._addon_files = [None, None]

        # ─── Data ────────────────────────────────────────────────────────
        self.killer_dir   = image_path("killers")
        self.addons_root  = image_path("killer_addons")
        self.killer_files = [
            f for f in os.listdir(self.killer_dir)
            if f.lower().endswith(".png")
        ]

        # placeholder graphic
        self.placeholder = QPixmap(image_path("killer_perks", "helpLoadingKiller.png")) \
            .scaled(220, 220,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)

        # ─── UI ───────────────────────────────────────────────────────────
        self.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Content: portrait & name | addons
        content = QHBoxLayout()
        content.setSpacing(60)
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Portrait + Name
        self.portrait_container = QWidget()
        pc = QVBoxLayout(self.portrait_container)
        pc.setContentsMargins(0,0,0,0)
        pc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        frame = QFrame()
        frame.setFixedSize(260,260)
        frame.setStyleSheet("""
            QFrame { background-color: rgba(0,0,0,150);
                     border: 2px solid #222;
                     border-radius: 10px; }
        """)
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0,0,0,0)
        fl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.portrait_label = ClickableLabel()
        self.portrait_label.setFixedSize(220,220)
        self.portrait_label.setPixmap(self.placeholder)
        self.portrait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.portrait_label.setToolTip("Click to reroll killer (spins then addons)")
        self.portrait_label.clicked.connect(self._start_single_portrait)
        fl.addWidget(self.portrait_label)

        pc.addWidget(frame)
        pc.addSpacing(5)

        self.name_label = QLabel("", self)
        self.name_label.setFixedSize(260,40)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12pt;
                font-weight: bold;
                background: transparent;
            }
        """)
        pc.addWidget(self.name_label)

        content.addWidget(self.portrait_container)

        # Addons
        addons_v = QVBoxLayout()
        addons_v.setSpacing(40)
        addons_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # ← restore this list for FullDisplay
        self.addon_containers   = []
        self.addon_labels       = []
        self.addon_name_labels  = []

        for idx in range(2):
            ctn = QWidget()
            cl  = QVBoxLayout(ctn)
            cl.setContentsMargins(0,0,0,0)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            af = QFrame()
            af.setFixedSize(140,140)
            af.setStyleSheet("""
                QFrame { background-color: rgba(0,0,0,150);
                         border: 2px solid #222;
                         border-radius: 10px; }
            """)
            afl = QVBoxLayout(af)
            afl.setContentsMargins(0,0,0,0)
            afl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            ico = ClickableLabel()
            ico.setFixedSize(110,110)
            ico.setPixmap(self.placeholder.scaled(
                110,110,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation
            ))
            ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ico.setToolTip("Click to reroll this addon (spins first)")
            ico.clicked.connect(lambda *args, i=idx: self._start_single_addon(i))
            afl.addWidget(ico)

            name = QLabel("", self)
            name.setFixedSize(140,40)
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name.setWordWrap(True)
            name.setStyleSheet("""
                QLabel { color: white; font-size:10pt; font-weight:bold; background: transparent; }
            """)

            cl.addWidget(af)
            cl.addSpacing(5)
            cl.addWidget(name)

            addons_v.addWidget(ctn)
            # ← append to containers too
            self.addon_containers.append(ctn)
            self.addon_labels.append(ico)
            self.addon_name_labels.append(name)

        content.addLayout(addons_v)
        root.addLayout(content)
        root.addSpacing(30)

        # Spin / Back
        spin_btn = AnimatedButton("Spin", hover_color="#982c1c", base_color="#222", text_color="white",
                                  hover_sound=self.hover_sound, click_sound=self.click_sound)
        spin_btn.setFixedSize(220,50)
        spin_btn.clicked.connect(self._start_portrait)
        root.addWidget(spin_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addSpacing(8)

        back_btn = AnimatedButton("Back", hover_color="#555", base_color="#111", text_color="white",
                                  hover_sound=self.hover_sound, click_sound=self.click_sound)
        back_btn.setFixedSize(150,50)
        back_btn.clicked.connect(self.back_cb)
        root.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        tip = QLabel("Tip: click any icon above to reroll it individually.", self)
        tip.setStyleSheet("color: #ccc; font-size: 8pt;")
        root.addWidget(tip, alignment=Qt.AlignmentFlag.AlignCenter)

        # ─── Timers & Counters ─────────────────────────────────────────
        # Full‑sequence
        self._portrait_counter = 0
        self._addon_counter    = 0
        self.portrait_timer    = QTimer(self)
        self.portrait_timer.timeout.connect(self._animate_portrait)
        self.addon_timer       = QTimer(self)
        self.addon_timer.timeout.connect(self._animate_addons)

        # Single‑addon
        self._single_addon_counter = 0
        self._single_addon_idx     = None
        self._single_addon_timer   = QTimer(self)
        self._single_addon_timer.timeout.connect(self._animate_single_addon)

        # Single‑portrait
        self._single_portrait_counter = 0
        self._single_portrait_timer   = QTimer(self)
        self._single_portrait_timer.timeout.connect(self._animate_single_portrait)

    # ─── Full‑sequence handlers ───────────────────────────────────────
    def _start_portrait(self):
        self._portrait_counter = 0
        self.name_label.clear()
        for icon, lbl in zip(self.addon_labels, self.addon_name_labels):
            icon.setPixmap(self.placeholder.scaled(110,110,
                Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            lbl.clear()
        self.portrait_timer.start(SPIN_INTERVAL)

    def _animate_portrait(self):
        self._portrait_counter += 1
        pick = random.choice(self.killer_files)
        self.portrait_label.setPixmap(
            QPixmap(os.path.join(self.killer_dir, pick))
            .scaled(220,220,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        )
        if self._portrait_counter > SPIN_STEPS:
            self.portrait_timer.stop()
            self.name_label.setText(format_perk_name(pick))
            self._start_addons()

    def _start_addons(self):
        self._addon_counter = 0
        self.addon_timer.start(SPIN_INTERVAL)

    def _animate_addons(self):
        self._addon_counter += 1
        all_addons = []
        for sub in os.listdir(self.addons_root):
            fld = os.path.join(self.addons_root, sub)
            if os.path.isdir(fld):
                for fn in os.listdir(fld):
                    if fn.lower().endswith(".png"):
                        all_addons.append(os.path.join(fld, fn))

        for icon in self.addon_labels:
            icon.setPixmap(
                QPixmap(random.choice(all_addons)).scaled(110,110,
                    Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            )

        if self._addon_counter > SPIN_STEPS:
            self.addon_timer.stop()
            self._reveal_addons()

    def _reveal_addons(self):
        key = self.name_label.text().replace(" ", "")
        folder = os.path.join(self.addons_root, key)
        if not os.path.isdir(folder):
            return
        files = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
        picks = random.sample(files, min(2, len(files)))
        self._addon_files = picks
        for icon, name_lbl, fn in zip(self.addon_labels, self.addon_name_labels, picks):
            path = os.path.join(folder, fn)
            icon.setPixmap(
                QPixmap(path).scaled(110,110,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            )
            name_lbl.setText(format_perk_name(fn))

    # ─── Single‑slot addon spin ──────────────────────────────────────
    def _start_single_addon(self, idx):
        if not self.name_label.text():
            return
        self._single_addon_idx     = idx
        self._single_addon_counter = 0
        self._single_addon_timer.start(SPIN_INTERVAL)

    def _animate_single_addon(self):
        self._single_addon_counter += 1
        key = self.name_label.text().replace(" ", "")
        folder = os.path.join(self.addons_root, key)
        if not os.path.isdir(folder):
            self._single_addon_timer.stop()
            return
        files = [f for f in os.listdir(folder) if f.lower().endswith(".png")]

        icon = self.addon_labels[self._single_addon_idx]
        icon.setPixmap(
            QPixmap(os.path.join(folder, random.choice(files))).scaled(
                110,110,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation
            )
        )

        if self._single_addon_counter > SPIN_STEPS:
            self._single_addon_timer.stop()
            self._reroll_addon(self._single_addon_idx)

    # ─── Single‑slot portrait spin + cascade ─────────────────────────
    def _start_single_portrait(self):
        self._single_portrait_counter = 0
        self._single_portrait_timer.start(SPIN_INTERVAL)

    def _animate_single_portrait(self):
        self._single_portrait_counter += 1
        pick = random.choice(self.killer_files)
        self.portrait_label.setPixmap(
            QPixmap(os.path.join(self.killer_dir, pick))
            .scaled(220,220,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        )
        if self._single_portrait_counter > SPIN_STEPS:
            self._single_portrait_timer.stop()
            self.name_label.setText(format_perk_name(pick))
            self._start_addons()

    # ─── Helper (used by full‑sequence and single‑slot) ─────────────
    def _reroll_addon(self, idx):
        key = self.name_label.text().replace(" ", "")
        folder = os.path.join(self.addons_root, key)
        if not os.path.isdir(folder):
            return
        files = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
        other = self._addon_files[1-idx]
        pool = [f for f in files if f != other] or files
        fn = random.choice(pool)
        self._addon_files[idx] = fn

        path = os.path.join(folder, fn)
        self.addon_labels[idx].setPixmap(
            QPixmap(path).scaled(110,110,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        )
        self.addon_name_labels[idx].setText(format_perk_name(fn))
