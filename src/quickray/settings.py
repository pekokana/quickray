from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QTimer, QEvent
from PyQt6.QtGui import QIcon, QKeySequence
from .data import *

from .utils import get_generated_icon
from .constants import ICON_PATH

def to_pynput_format(text: str):
    mapping = {
        "Ctrl": "<ctrl>",
        "Shift": "<shift>",
        "Alt": "<alt>",
        "Space": "<space>",
        "Enter": "<enter>"
    }

    parts = text.split("+")
    out = []

    for p in parts:
        out.append(mapping.get(p, p.lower()))

    return "+".join(out)

class Settings(QWidget):
    hotkey_changed = pyqtSignal()

    def __init__(self, commands, launcher):
        super().__init__()
        self.setWindowIcon(QIcon(ICON_PATH))
        self.commands = commands
        self.launcher = launcher
        self.edit_index = None
        self.settings = load_settings()
        self.temp_settings = self.settings.copy()

        self.setWindowTitle("Quickray Settings")
        self.resize(520, 420)

        self.tabs = QTabWidget()

        self.tabs.addTab(self.build_general_tab(), "General")
        self.tabs.addTab(self.build_commands_tab(), "Commands")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)


        # ★ 初期値反映（Q2対応）
        self.hotkey.setText(self.settings.get("hotkey", ""))
        self.theme.setCurrentText(self.settings.get("theme", "dark"))

        self.apply_theme()

    # ==================================================
    # General
    # ==================================================

    def build_general_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)

        self.hotkey = QLineEdit()
        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])

        self.theme.currentTextChanged.connect(self.change_theme)

        # ★ QLabel追加（Q5思想）
        ## Hotkey
        l.addWidget(QLabel("Hotkey"))
        # l.addWidget(self.hotkey)
        row = QHBoxLayout()
        self.hotkey.setReadOnly(True)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.start_hotkey_capture)
        row.addWidget(self.hotkey)
        row.addWidget(self.edit_btn)
        l.addLayout(row)

        ## Theme
        l.addWidget(QLabel("Theme"))
        l.addWidget(self.theme)

        ## clipboard
        l.addWidget(QLabel("Clipboard Interval (ms)"))
        self.clip_interval = QSpinBox()
        self.clip_interval.setRange(200, 5000)
        self.clip_interval.setValue(self.settings.get("clipboard_interval", 1000))
        l.addWidget(self.clip_interval)

        ## data folder
        l.addWidget(QLabel("Data Folder"))
        path = QLineEdit(APP_DIR)
        path.setReadOnly(True)
        l.addWidget(path)


        ### Apply & Cancel
        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.cancel_btn = QPushButton("Cancel")
        self.apply_btn.clicked.connect(self.apply_general_settings)
        self.cancel_btn.clicked.connect(self.cancel_general_settings)
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.cancel_btn)
        l.addLayout(btn_row)

        return w

    def apply_hotkey(self):
        if not self.captured_hotkey:
            return

        # pynput形式に変換
        formatted = to_pynput_format(self.captured_hotkey)

        # self.settings["hotkey"] = formatted
        # save_settings(self.settings)
        self.temp_settings["hotkey"] = formatted

        # 表示も人間用に戻す
        self.hotkey.setText(self.captured_hotkey)

        self.hotkey_changed.emit()

        # キャプチャ終了
        QApplication.instance().removeEventFilter(self)

    def cancel_hotkey(self):
        QApplication.instance().removeEventFilter(self)

        # 元の値に戻す
        current = self.settings.get("hotkey", "")
        self.hotkey.setText(current)

        # ホットキー再登録
        self.hotkey_changed.emit()

    def start_hotkey_capture(self):
        self.hotkey.setText("Press keys...")
        self.pressed_keys = set()
        self.captured_hotkey = ""

        # グローバルホットキー止める（重要）
        if hasattr(self.launcher, "_state"):
            hk = self.launcher._state.get("hotkey")
            if hk:
                hk.stop()

        QApplication.instance().installEventFilter(self)


    # def eventFilter(self, obj, event):
    #     if event.type() == QEvent.Type.KeyPress:
    #         keys = []

    #         mods = event.modifiers()

    #         if mods & Qt.KeyboardModifier.ControlModifier:
    #             keys.append("Ctrl")
    #         if mods & Qt.KeyboardModifier.ShiftModifier:
    #             keys.append("Shift")
    #         if mods & Qt.KeyboardModifier.AltModifier:
    #             keys.append("Alt")

    #         key = QKeySequence(event.key()).toString()

    #         if key and key not in ["Ctrl", "Shift", "Alt"]:
    #             keys.append(key)

    #         combo = "+".join(keys)

    #         self.captured_hotkey = combo   # ✅保存用（まだ保存しない）
    #         self.hotkey.setText(combo)

    #         return True

    #     return super().eventFilter(obj, event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()

            self.pressed_keys.add(key)
            self.update_hotkey_display()

            return True

        if event.type() == QEvent.Type.KeyRelease:
            key = event.key()

            if key in self.pressed_keys:
                self.pressed_keys.remove(key)

            # 全キー離したらキャプチャ終了
            if not self.pressed_keys:
                QApplication.instance().removeEventFilter(self)

            return True

        return super().eventFilter(obj, event)

    def update_hotkey_display(self):
        keys = []

        for k in self.pressed_keys:
            if k == Qt.Key.Key_Control:
                keys.append("Ctrl")
            elif k == Qt.Key.Key_Shift:
                keys.append("Shift")
            elif k == Qt.Key.Key_Alt:
                keys.append("Alt")
            else:
                keys.append(QKeySequence(k).toString())

        # 順序固定（これ重要）
        order = ["Ctrl", "Shift", "Alt"]

        mods = [k for k in order if k in keys]
        others = [k for k in keys if k not in order]

        combo = "+".join(mods + others)

        self.captured_hotkey = combo
        self.hotkey.setText(combo)

    def apply_general_settings(self):
        self.temp_settings["clipboard_interval"] = self.clip_interval.value()
        self.settings.update(self.temp_settings)
        save_settings(self.settings)

        self.hotkey.setText(self.settings["hotkey"])
        self.hotkey_changed.emit()

        # ボタンアニメーション
        anim = QPropertyAnimation(self.apply_btn, b"windowOpacity")
        anim.setDuration(150)
        anim.setStartValue(0.4)
        anim.setEndValue(1.0)
        anim.start()

        self._anim = anim  # GC防止

        # Clipboard監視間隔更新
        if hasattr(self.launcher, "_state"):
            clipboard = self.launcher._state.get("clipboard")
            if clipboard:
                interval = self.settings.get("clipboard_interval", 1000)
                clipboard.set_interval(interval)

        # 保存通知
        self.show_saved_message()


    def show_saved_message(self):
        if not hasattr(self, "toast"):
            self.toast = QLabel("Saved ✅", self)
            self.toast.setStyleSheet("""
                background: rgba(0, 0, 0, 180);
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
            """)
            self.toast.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.toast.adjustSize()

        # 画面右下に表示
        self.toast.move(
            self.width() - self.toast.width() - 20,
            self.height() - self.toast.height() - 20
        )

        self.toast.setWindowOpacity(0)
        self.toast.show()

        # フェードイン
        self.fade_in = QPropertyAnimation(self.toast, b"windowOpacity")
        self.fade_in.setDuration(150)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.start()

        # 1秒後に消す
        QTimer.singleShot(1000, self.fade_out_message)


    def fade_out_message(self):
        self.fade_out = QPropertyAnimation(self.toast, b"windowOpacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)

        self.fade_out.finished.connect(self.toast.hide)
        self.fade_out.start()

    def cancel_general_settings(self):
        self.temp_settings = self.settings.copy()

        self.hotkey.setText(self.settings.get("hotkey", ""))
        self.theme.setCurrentText(self.settings.get("theme", "dark"))

        self.apply_theme()
        self.launcher.apply_theme(self.settings.get("theme", "dark"))

    # ==================================================
    # Commands
    # ==================================================

    def build_commands_tab(self):
        w = QWidget()
        main = QVBoxLayout(w)

        self.listbox = QListWidget()
        self.listbox.itemClicked.connect(self.load_selected)

        # ★ 削除ボタン付きリスト（Q6）
        self.listbox.setSpacing(4)

        form = QFormLayout()

        self.name = QLineEdit()
        self.cmd = QLineEdit()
        self.alias = QLineEdit()

        # ★ ラベル付き（Q5解決）
        form.addRow("Name", self.name)
        form.addRow("Command", self.cmd)
        form.addRow("Alias", self.alias)

        self.btn = QPushButton("Add")
        self.btn.clicked.connect(self.add_or_update)

        main.addWidget(self.listbox)
        main.addLayout(form)
        main.addWidget(self.btn)

        self.refresh()
        return w

    # ==================================================
    # CRUD
    # ==================================================

    def refresh(self):
        self.listbox.clear()

        settings = load_settings()
        seed = settings.get("device_seed")

        for i, c in enumerate(self.commands):
            icon = get_generated_icon(c["command"], c["name"], seed)
            item = QListWidgetItem(icon, c["name"])

            # ★ 削除ボタン （Q6）
            btn = QPushButton("×")
            btn.setFixedWidth(24)
            btn.clicked.connect(lambda _, idx=i: self.delete_item(idx))

            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(4, 2, 4, 2)
            layout.addWidget(QLabel(c["name"]))
            layout.addStretch()
            layout.addWidget(btn)


            item.setSizeHint(widget.sizeHint())

            self.listbox.addItem(item)
            self.listbox.setItemWidget(item, widget)

    def load_selected(self, item):
        idx = self.listbox.row(item)
        c = self.commands[idx]

        self.name.setText(c["name"])
        self.cmd.setText(c["command"])
        self.alias.setText(c.get("alias", ""))

        self.edit_index = idx
        self.btn.setText("Update")  # ★ Q6

    def add_or_update(self):
        data = {
            "name": self.name.text(),
            "command": self.cmd.text(),
            "alias": self.alias.text(),
            "count": 0
        }

        if self.edit_index is None:
            self.commands.append(data)
        else:
            self.commands[self.edit_index].update(data)

        save(self.commands)

        # ★ 同期
        self.launcher.commands = load()
        self.launcher.update_list()

        self.clear_form()
        self.refresh()


    def animate_delete(self, widget):
        anim = QPropertyAnimation(widget, b"windowOpacity")
        anim.setDuration(150)
        anim.setStartValue(1)
        anim.setEndValue(0)

        anim.finished.connect(widget.deleteLater)
        anim.start()

    def delete_item(self, idx):
        item = self.listbox.item(idx)
        widget = self.listbox.itemWidget(item)

        # ★ 確認ダイアログ（Q6）
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Delete this command?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.animate_delete(widget)

            del self.commands[idx]
            save(self.commands)

            self.launcher.commands = load()
            self.launcher.update_list()

            QTimer.singleShot(160, self.refresh)

    def clear_form(self):
        self.name.clear()
        self.cmd.clear()
        self.alias.clear()
        self.edit_index = None
        self.btn.setText("Add")

    # ==================================================
    # Theme
    # ==================================================

    def apply_theme(self):
        theme = self.settings.get("theme", "dark")

        if theme == "dark":
            self.setStyleSheet("""
                QWidget {
                    background: #2b2b2b;
                    color: #eee;
                }

                QLineEdit, QComboBox {
                    background: #3c3f41;
                    color: white;
                    border: 1px solid #555;
                    padding: 6px;
                }

                QListWidget {
                    background: #2b2b2b;
                    border: 1px solid #444;
                }

                QListWidget::item:selected {
                    background: #555;
                    color: white;
                }

                QTabWidget::pane {
                    border: 1px solid #555;
                }

                QTabBar::tab {
                    background: #3c3f41;
                    padding: 6px;
                    border: 1px solid #555;
                }

                QTabBar::tab:selected {
                    background: #555;
                }

                QPushButton {
                    background: #555;
                    color: white;
                    padding: 6px;
                }

                QPushButton:hover {
                    background: #777;   /* ✅ホバー時 */
                }

                QPushButton:pressed {
                    background: #999;   /* ✅押したとき */
                }

                QListWidget::item:hover {
                    background: #666;  /* dark */
                }

                QListWidget::item {
                    padding: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background: #f5f5f5;
                    color: black;
                }

                QLineEdit, QComboBox {
                    background: white;
                    color: black;
                    border: 1px solid #aaa;
                    padding: 6px;
                }

                QListWidget {
                    background: white;
                    border: 1px solid #aaa;
                }

                QListWidget::item:selected {
                    background: #ddd;
                    color: black;
                }

                QTabWidget::pane {
                    border: 1px solid #aaa;
                }

                QTabBar::tab {
                    background: #ddd;
                    padding: 6px;
                    border: 1px solid #aaa;
                }

                QTabBar::tab:selected {
                    background: white;
                }

                QPushButton {
                    background: #ddd;
                    color: black;
                    padding: 6px;
                }

                QPushButton:hover {
                    background: #bbb;
                }

                QPushButton:pressed {
                    background: #999;
                }


                QListWidget::item:hover {
                    background: #ccc;  /* light */
                }

                QListWidget::item {
                    padding: 4px;
                }
            """)

    def change_theme(self, theme):
        self.temp_settings["theme"] = theme
        self.apply_theme()
        self.launcher.apply_theme(theme)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            if self.edit_index is not None:
                self.clear_form()
            else:
                self.close()

