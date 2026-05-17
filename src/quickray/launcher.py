from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from rapidfuzz import process
import subprocess, webbrowser
from datetime import datetime

from .widgets.ghost_input import GhostLineEdit

from .utils import get_generated_icon
from .data import load_settings, save

from .data import load_json, save_json, HISTORY_FILE, CLIPBOARD_FILE

class Launcher(QWidget):
    def __init__(self, commands):
        super().__init__()

        self.commands = commands
        self.history = load_json(HISTORY_FILE)
        self.history_index = -1

        self.mode = "input"
        self.tab_index = -1

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)

        self.setFixedSize(520,300)

        # @@@@
        main_layout = QVBoxLayout(self)

        # =========================
        # 検索入力（上）
        # =========================
        self.input = GhostLineEdit()
        self.input.setFont(QFont("Consolas", 12))
        self.input.setTextMargins(8, 0, 0, 0)

        main_layout.addWidget(self.input)

        # =========================
        # 下エリア（2カラム）
        # =========================
        bottom_layout = QHBoxLayout()

        # 左：結果リスト
        self.listbox = QListWidget()
        self.listbox.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        bottom_layout.addWidget(self.listbox, 2)

        # 右：Preview（スクロール可能）
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.preview.setMinimumWidth(260)
        self.preview.setMaximumWidth(420)

        self.preview.setStyleSheet("""
            background:#222;
            padding:10px;
            border-left:1px solid #444;
        """)

        self.preview.setFont(QFont("Consolas", 10))

        bottom_layout.addWidget(self.preview, 3)

        main_layout.addLayout(bottom_layout)

        # @@@@
        self.input.installEventFilter(self)
        self.input.textChanged.connect(self.update_list)
        self.listbox.currentItemChanged.connect(self.update_preview)
        

        self.apply_theme(load_settings().get("theme", "dark"))
        self.update_list()

    def update_preview(self, item):
        if not item:
            self.preview.setText("")
            return

        c = item.data(Qt.ItemDataRole.UserRole)

        # ======================
        # Clipboard
        # ======================
        if "text" in c:
            # text = c["command"]
            text = c["command"].replace("\\r\\n", "\n")

            self.preview.setStyleSheet("""
                background:#1e1e1e;
                color:#9cdcfe;
                padding:10px;
            """)

            self.preview.setPlainText(
                f"[Clipboard]\n\n{text}"
            )
            return

        # ======================
        # History / Command
        # ======================
        name = c.get("name", "")
        cmd = c.get("command", "")
        alias = c.get("alias", "")
        count = c.get("count", 0)

        self.preview.setPlainText(
            f"{name}\n\n"
            f"[Command]\n{cmd}\n\n"
            f"[Alias]\n{alias}\n\n"
            f"[Used]\n{count}"
        )

    def delete_selected(self):
        item = self.listbox.currentItem()
        if not item:
            return

        text = self.input.text().strip().lower()
        c = item.data(Qt.ItemDataRole.UserRole)

        current_row = self.listbox.currentRow()

        # ======================
        # Clipboard削除（1件のみ）
        # ======================
        if text.startswith("c"):
            target = c["command"]

            for i, x in enumerate(self.clip_history):
                if x["text"] == target:
                    del self.clip_history[i]
                    break

            save_json(CLIPBOARD_FILE, self.clip_history)

            # serviceにも反映
            if hasattr(self, "_state"):
                clipboard = self._state.get("clipboard")
                if clipboard:
                    clipboard.history = self.clip_history

        # ======================
        # History削除（1件のみ）
        # ======================
        elif text.startswith("h"):
            target = c["command"]

            for i, x in enumerate(self.history):
                if x["command"] == target:
                    del self.history[i]
                    break

            save_json(HISTORY_FILE, self.history)

        # ======================
        # 再描画
        # ======================
        self.update_list()

        # 選択位置維持
        count = self.listbox.count()
        if count > 0:
            new_row = min(current_row, count - 1)
            self.listbox.setCurrentRow(new_row)
            self.update_preview(self.listbox.currentItem())
        else:
            self.preview.clear()

    def eventFilter(self, obj, event):
        if obj == self.input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Tab:

                count = self.listbox.count()
                if count == 0:
                    return True

                is_shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier

                # ======================
                # Ghost補完（前方向のみ）
                # ======================
                if not is_shift:
                    # ghost_text = self.input.text() + self.input.ghost_text
                    # if ghost_text and ghost_text != self.input.text():
                    #     self.input.setText(ghost_text)
                    #     self.input.setCursorPosition(len(ghost_text))
                    #     return True
                    ghost = self.input.ghost_text
                    if ghost:
                        cur = self.input.cursorPosition()
                        text = self.input.text()

                        new_text = text[:cur] + ghost + text[cur:]
                        self.input.setText(new_text)
                        self.input.setCursorPosition(cur + len(ghost))
                        return True

                # ======================
                # index移動
                # ======================
                if self.tab_index == -1:
                    self.tab_index = 0
                else:
                    if is_shift:
                        self.tab_index = (self.tab_index - 1) % count
                    else:
                        self.tab_index = (self.tab_index + 1) % count

                # ======================
                # UI反映
                # ======================
                self.input.setFocus()
                self.listbox.setCurrentRow(self.tab_index)

                item = self.listbox.item(self.tab_index)
                c = item.data(Qt.ItemDataRole.UserRole)

                self.input.setText(c["name"])
                self.input.selectAll()

                return True
        return super().eventFilter(obj, event)

    # ======================
    # Theme
    # ======================
    def apply_theme(self, theme):
        if theme == "dark":
            self.setStyleSheet("""
                QWidget { background: rgba(30,30,30,230); color: white; }
                QLineEdit { background:#333; padding:10px; }
                QListWidget::item:selected { background:#444; }
            """)
        else:
            self.setStyleSheet("""
                QWidget { background:#f5f5f5; color:black; }
                QLineEdit { background:white; padding:10px; }
                QListWidget::item:selected { background:#ddd; }
            """)

    # ======================
    # UX
    # ======================
    def keyPressEvent(self, e):

        # ======================
        # Esc
        # ======================
        if e.key() == Qt.Key.Key_Escape:
            if self.mode == "list":
                self.mode = "input"
                self.input.setFocus()
                return
            else:
                self.input.clear()
                self.hide()
                return

        # ======================
        # ↓でlistへ
        # ======================
        if e.key() == Qt.Key.Key_Down:
            if self.mode == "input":
                if self.listbox.count():
                    self.mode = "list"
                    self.listbox.setFocus()
                    self.listbox.setCurrentRow(0)
                return

        # ======================
        # listモード操作
        # ======================
        if self.mode == "list":

            if e.key() == Qt.Key.Key_Down:
                row = self.listbox.currentRow()
                self.listbox.setCurrentRow(min(row + 1, self.listbox.count() - 1))
                return

            if e.key() == Qt.Key.Key_Up:
                row = self.listbox.currentRow()
                if row == 0:
                    self.mode = "input"
                    self.input.setFocus()
                else:
                    self.listbox.setCurrentRow(row - 1)
                return

            if e.key() == Qt.Key.Key_Return:
                self.launch()
                return

            if e.key() == Qt.Key.Key_Tab:
                item = self.listbox.currentItem()
                if item:
                    c = item.data(Qt.ItemDataRole.UserRole)
                    self.input.setText(c["name"])
                    self.mode = "input"
                    self.input.setFocus()
                return
            # ======================
            # Alt削除
            # ======================
            if e.modifiers() & Qt.KeyboardModifier.AltModifier:
                if e.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                    self.delete_selected()
                    return

        super().keyPressEvent(e)

    # ======================
    # Search
    # ======================
    def populate_list(self, results):
        self.listbox.clear()

        for c in results:
            item = QListWidgetItem(c["name"])
            item.setData(Qt.ItemDataRole.UserRole, c)
            self.listbox.addItem(item)

        if self.listbox.count():
            self.listbox.setCurrentRow(0)


    def update_list(self):

        self.tab_index = -1  # ✅毎回リセット
        text = self.input.text().strip().lower()
        self.tab_index = -1

        if hasattr(self, "_state"):
            clipboard = self._state.get("clipboard")
            if clipboard:
                self.clip_history = clipboard.history

        self.listbox.clear()

        cmds = self.commands.copy()

        results = []

        # ======================
        # Clipboard検索
        #  c        → 一覧（browse）
        #  c foo    → 検索（search）
        # ======================
        if text.startswith("c"):
            query = text[1:].strip()

            # 最近使用を優先
            sorted(self.clip_history, key=lambda x: x["time"], reverse=True)

            if not query:
                # 閲覧モード
                results = [
                    {
                        "name": item["text"][:80],
                        "command": item["text"]
                    }
                    for item in self.clip_history
                ][:20]

            else:
                # 検索モード
                results = [
                    {
                        "name": item["text"][:80],
                        "command": item["text"]
                    }
                    for item in self.clip_history
                    if query in item["text"].lower()
                ][:10]

            self.populate_list(results)
            return
        # ======================
        # History検索
        #  h        → 一覧
        #  h foo    → 検索
        # ======================
        if text.startswith("h"):
            query = text[1:].strip()

            # 最近使用を優先
            sorted(self.history, key=lambda x: x["time"], reverse=True)


            if not query:
                # 閲覧
                results = [
                    {
                        "name": item["name"],
                        "command": item["command"]
                    }
                    for item in self.history
                ][:20]

            else:
                # 検索
                results = [
                    {
                        "name": item["name"],
                        "command": item["command"]
                    }
                    for item in self.history
                    if query in item["name"].lower()
                ][:10]

            self.populate_list(results)
            return
        # ======================
        # 通常コマンド検索
        # ======================
        if not text:
            results = cmds[:6]
        else:
            # # コマンド
            # cmd_results = sorted(cmds,
            #                      key=lambda c: self.score(text, c),
            #                      reverse=True)[:5]

            # results = cmd_results
            results = sorted(
                cmds,
                key=lambda c: self.score(text, c),
                reverse=True
            )[:5]

        seed = load_settings().get("device_seed")

        for c in results:
            icon = get_generated_icon(c["command"], c["name"], seed)
            item = QListWidgetItem(icon, c["name"])
            item.setData(Qt.ItemDataRole.UserRole, c)
            self.listbox.addItem(item)

        # Ghost更新
        if self.listbox.count() > 0:
            item = self.listbox.item(0)
            c = item.data(Qt.ItemDataRole.UserRole)

            text = self.input.text()
            cursor = self.input.cursorPosition()

            # 「末尾のみ」Ghost出す（Raycast仕様）
            if cursor != len(text):
                self.input.setGhostText("")
                return

            # prefix一致チェック
            if c["name"].lower().startswith(text.lower()) and text:
                rest = c["name"][len(text):]
                self.input.setGhostText(rest)
            else:
                self.input.setGhostText("")
        else:
            self.input.setGhostText("")


        if self.listbox.count():
            self.listbox.setCurrentRow(0)

        # tab_index調整
        if self.tab_index >= 0:
            self.tab_index = min(self.tab_index, self.listbox.count() - 1)
        
        # Preview
        if self.listbox.count():
            self.listbox.setCurrentRow(0)
            self.update_preview(self.listbox.currentItem())


    def score(self, text, c):
        name = c["name"].lower()
        alias = c.get("alias", "").lower()

        score = 0
        if text in name: score += 100
        if text in alias: score += 120

        score += process.extractOne(text, [name])[1]
        score += c.get("count", 0) * 10

        return score

    # ======================
    # Launch
    # ======================
    def is_shell_command(self, cmd):
        return cmd.lower() in ["powershell", "cmd"]

    def launch(self):
        if getattr(self, "_launching", False):
            return
        self._launching = True

        try:
            text = self.input.text()

            # ======================
            # Google
            # ======================
            if text.startswith("g "):
                webbrowser.open(f"https://google.com/search?q={text[2:]}")
                self.hide()
                return

            # ======================
            # Clipboard
            # ======================
            if text.startswith("c"):
                item = self.listbox.currentItem()
                if item:
                    c = item.data(Qt.ItemDataRole.UserRole)
                    QApplication.clipboard().setText(c["command"])
                self.hide()
                return

            # ======================
            # History
            # ======================
            if text.startswith("h"):
                item = self.listbox.currentItem()
                if item:
                    c = item.data(Qt.ItemDataRole.UserRole)
                    text = c["command"]
            else:
                item = self.listbox.currentItem()
                if not item:
                    return
                c = item.data(Qt.ItemDataRole.UserRole)
                text = c["command"]

            cmd = text

            if self.is_shell_command(cmd):
                subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen(cmd, shell=True)

            # ===== 履歴保存 =====
            c["count"] = c.get("count", 0) + 1
            c["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            save(self.commands)

            hist = load_json(HISTORY_FILE)

            hist.insert(0, {
                "name": c["name"],
                "command": c["command"],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            hist = hist[:50]
            save_json(HISTORY_FILE, hist)

            self.history = hist
            self.history_index = -1

            self.input.clear()
            self.hide()

        finally:
            self._launching = False



