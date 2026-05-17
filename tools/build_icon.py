from PIL import Image
from pathlib import Path

# ===== パス設定 =====

BASE = Path(__file__).resolve().parent.parent

ASSETS_SRC = BASE / "assets_src"              # 元素材
ASSETS_OUT = BASE / "src" / "quickray" / "assets"  # 出力先

SRC_PNG = ASSETS_SRC / "icon.png"             # 元画像

ASSETS_OUT.mkdir(parents=True, exist_ok=True)

# ===== サイズ定義 =====

sizes = [16, 32, 48, 64, 128]

# ===== PNG生成 =====

img = Image.open(SRC_PNG)

for s in sizes:
    out = ASSETS_OUT / f"icon_{s}.png"
    img.resize((s, s), Image.LANCZOS).save(out)
    print(f"[PNG] created: {out}")

# ===== ICO生成 =====

ico_path = ASSETS_OUT / "icon.ico"

img.save(
    ico_path,
    format="ICO",
    sizes=[(s, s) for s in sizes]
)

print(f"[ICO] created: {ico_path}")