import os, json, sys, hashlib, socket, getpass, time
from datetime import datetime, timedelta

APP_DIR = os.path.join(os.getenv("APPDATA"), "quickray")
os.makedirs(APP_DIR, exist_ok=True)

DATA_FILE = os.path.join(APP_DIR, "commands.json")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

HISTORY_FILE = os.path.join(APP_DIR, "history.json")
CLIPBOARD_FILE = os.path.join(APP_DIR, "clipboard.json")


DEFAULT_SETTINGS = {
    "hotkey": "<ctrl>+<shift>+<space>",
    "sort": "count",
    "theme": "dark",
    "clipboard_interval": 1000
}

# ----------------------
# device seed
# ----------------------
def generate_device_seed():
    raw = f"{getpass.getuser()}@{socket.gethostname()}-{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()

def ensure_device_seed(settings):
    if "device_seed" not in settings:
        settings["device_seed"] = generate_device_seed()
    return settings

# ----------------------
# commands
# ----------------------
def load():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ----------------------
# settings
# ----------------------
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        settings = DEFAULT_SETTINGS.copy()
        settings = ensure_device_seed(settings)
        save_settings(settings)
        return settings

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)

    settings = ensure_device_seed(settings)
    save_settings(settings)
    return settings

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ----------------------
# history manege
# ----------------------
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cleanup(items, days=7):
    now = datetime.now()
    result = []

    for i in items:
        if "time" not in i:
            continue

        t = datetime.strptime(i["time"], "%Y-%m-%d %H:%M:%S")
        if now - t <= timedelta(days=days):
            result.append(i)

    return result
