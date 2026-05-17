from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from datetime import datetime

from ..data import load_json, save_json, CLIPBOARD_FILE


class ClipboardManager:
    def __init__(self, interval=1000):
        self.clipboard = QApplication.clipboard()
        self.history = load_json(CLIPBOARD_FILE)
        self.last_clip = ""

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(interval)

    def poll(self):
        text = self.clipboard.text().strip()

        if not text:
            return

        if text == self.last_clip:
            return

        self.last_clip = text

        self.history.insert(0, {
            "text": text,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        self.history = self.history[:50]

        save_json(CLIPBOARD_FILE, self.history)

    def set_interval(self, interval):
        self.timer.start(interval)