import sys, os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QObject

from pynput import keyboard as pk

from .data import load, load_json, save_json, cleanup, HISTORY_FILE, CLIPBOARD_FILE
from .launcher import Launcher
from .settings import Settings
from .data import load_settings
from .services.clipboard import ClipboardManager

from .constants import ICON_PATH

class SignalHandler(QObject):
    show_signal = pyqtSignal()


def center(widget):
    screen = QApplication.primaryScreen().geometry()
    widget.move(
        (screen.width() - widget.width()) // 2,
        (screen.height() - widget.height()) // 3
    )

def register_hotkey(state, signal, settings):

    from pynput import keyboard as pk

    # 古いの止める
    if state.get("hotkey"):
        state["hotkey"].stop()

    def on_hotkey():
        signal.show_signal.emit()

    hk = settings.get("hotkey", "<ctrl>+alt+space")

    state["hotkey"] = pk.GlobalHotKeys({
        hk: on_hotkey
    })
    state["hotkey"].start()

def animate_show(widget):
    widget.setWindowOpacity(0)
    widget.show()

    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(120)
    anim.setStartValue(0)
    anim.setEndValue(1)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    anim.start()
    widget.anim = anim  # GC防止


def clean_history():
    settings = load_settings()
    days = settings.get("history_days", 7)

    hist = cleanup(load_json(HISTORY_FILE), days)
    save_json(HISTORY_FILE, hist)

    clip = cleanup(load_json(CLIPBOARD_FILE), days)
    save_json(CLIPBOARD_FILE, clip)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    commands = load()

    launcher = Launcher(commands)
    settings = Settings(commands, launcher)
    settings_data = load_settings()

    signal = SignalHandler()

    def reload_hotkey():
        settings_data = load_settings()
        register_hotkey(_state, signal, settings_data)

    def show_launcher():
        center(launcher)
        clean_history()
        animate_show(launcher)
        launcher.raise_()
        launcher.activateWindow()
        launcher.input.setFocus()
        launcher.input.clear()
        launcher.update_list()

    # ===== Signal =====
    signal.show_signal.connect(show_launcher)
    settings.hotkey_changed.connect(reload_hotkey)

    # ===== State =====
    global _state
    _state = {}

    _state["signal"] = signal
    _state["launcher"] = launcher
    _state["settings"] = settings

    # ===== Clipboadr =====
    settings_data = load_settings()

    clipboard_manager = ClipboardManager(
        interval=settings_data.get("clipboard_interval", 1000)
    )

    _state["clipboard"] = clipboard_manager

    # ===== Tray =====
    icon = QIcon(ICON_PATH) if os.path.exists(ICON_PATH) else QIcon()
    tray = QSystemTrayIcon(icon)
    tray.setToolTip("Quickray")

    menu = QMenu()
    menu.addAction("Settings", settings.show)
    menu.addAction("Quit", app.quit)

    tray.setContextMenu(menu)
    tray.show()

    _state["tray"] = tray

    launcher._state = _state
    # ===== Hotkey =====
    register_hotkey(_state, signal, settings_data)

    sys.exit(app.exec())


