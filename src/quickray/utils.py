import os, shlex, hashlib, random
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

import subprocess

icon_cache = {}

# ----------------------
# コマンドからパス抽出
# ----------------------
def extract_exe(cmd):
    try:
        return shlex.split(cmd)[0]
    except:
        return cmd

# ----------------------
# URL判定
# ----------------------
def is_url(cmd):
    return cmd.startswith("http://") or cmd.startswith("https://")

# ----------------------
# Icon seed生成
# ----------------------
def make_icon_seed(device_seed, path):
    ext = path.split(".")[-1].lower()

    size = 0
    try:
        if os.path.exists(path):
            size = os.path.getsize(path)
    except:
        pass

    size_bucket = size // 100000

    raw = f"{device_seed}:{ext}:{size_bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()

# ----------------------
# Identicon生成（9x9）
# ----------------------
def generate_identicon(seed, label):
    size = 64
    grid = 9

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 背景色
    h = int(seed[:6], 16)
    color = QColor((h>>0)&255, (h>>8)&255, (h>>16)&255)

    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)

    # パターン生成
    rand = random.Random(seed)

    cell_size = size // grid

    for y in range(grid):
        row = [rand.choice([True, False]) for _ in range(5)]
        full = row + row[-2::-1]

        for x in range(grid):
            if full[x]:
                painter.setBrush(QColor(255,255,255,180))
                painter.drawRect(x*cell_size, y*cell_size, cell_size, cell_size)

    # 中央テキスト
    painter.setPen(Qt.GlobalColor.white)
    painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

    painter.drawText(
        pix.rect(),
        Qt.AlignmentFlag.AlignCenter,
        label[:3].upper()
    )

    painter.end()

    return QIcon(pix)

# ----------------------
# 最終取得
# ----------------------
def get_generated_icon(command, name, device_seed):
    key = command

    if key in icon_cache:
        return icon_cache[key]

    exe = extract_exe(command)

    if "." in exe:
        label = exe.split(".")[-1]
        seed = make_icon_seed(device_seed, exe)
    else:
        label = name
        seed = make_icon_seed(device_seed, name)

    icon = generate_identicon(seed, label)

    icon_cache[key] = icon
    return icon

