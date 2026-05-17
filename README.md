# Quickray

> Raycast / Spotlight inspired launcher for Windows built with PyQt6.

PyQt6で開発された、Raycast / Spotlight風の高速ランチャーです。

---

## ✨ Features / 主な機能

- ⚡ Instant command launcher
- 🔍 Fuzzy search (rapidfuzz)
- 👻 Ghost text completion (cursor-aligned)
- 📋 Clipboard history
- 🕘 Command history
- 👁️ Preview panel (scrollable)
- ⌨️ Full keyboard control (Tab / Shift+Tab / Enter / Alt)

---

## 🧠 Concept / コンセプト

Quickrayは単なるランチャーではなく、

> **“拡張可能なランチャープラットフォーム”**

を目指しています。

今後はPlugin機構を中心に、
Raycastのような拡張エコシステムを構築予定です。

---

## 🚧 Current Status / 現在の状態

✅ Core features implemented  
✅ UI / UX almost complete  
⚠️ Plugin system (in progress)

---

## 📦 Tech Stack / 技術スタック

- Python 3.13
- PyQt6
- rapidfuzz
- pynput

---

## Getting Started / 起動方法

```bash
uv sync
uv run quickray
````
***

## Project Structure / ディレクトリ構成

```
quickray/
  main.py
  launcher.py
  settings.py
  services/
  widgets/
  data.py
```

***

## 🔌 Plugin System (Planned) / Plugin機構（開発中）

```text
plugins/
  example/
    plugin.py
    plugin.json
```

* Dynamic loading
* Prefix-based routing
* Settings UI per plugin

***

## 🧭 Roadmap / 今後の予定

* [ ] Plugin API設計
* [ ] Plugin Loader完成
* [ ] Settingsとの統合
* [ ] Marketplace対応

***

## 🤝 Contributing

Pull Requests歓迎です！

Plugin system設計に興味ある方はぜひ議論しましょう。

***

## 📜 License

MIT License

***

## 👤 Author

pekokana
