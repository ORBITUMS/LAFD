import os
from pathlib import Path

APP_ID = "com.example.AccountBrowser"
APP_NAME = "Account Browser"

HOME_DIR = Path.home()
XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME_DIR / ".local" / "share"))
BASE_DATA_DIR = XDG_DATA_HOME / "account-browser"
PROFILES_DIR = BASE_DATA_DIR / "profiles"
CONFIG_FILE = BASE_DATA_DIR / "profiles.json"
SETTINGS_FILE = BASE_DATA_DIR / "settings.json"

DEFAULT_URL = "https://www.google.com/"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "language": "ru",            # "en" | "ru" | "xd"
    "orientation": "horizontal", # "horizontal" | "vertical"
    "suggestions": True,         # показывать синий плюсик с быстрыми ссылками
    "drag_and_drop": False,      # включать перетаскивание сессий
    "auto_hide_footer": False,   # автоскрытие футера (по умолчанию выкл)
    "status_dots": True,         # цветные точки статуса на вкладках (по умолчанию вкл)
    "show_ram": True,            # счётчик потребления RAM (по умолчанию вкл)
    "proxy_enabled": True,       # поддержка прокси для сессий (по умолчанию вкл)
    "default_url": DEFAULT_URL,  # ссылка по умолчанию для новых сессий
    "first_run": True,
    "last_active_profile": None,
    "window_width": 1100,
    "window_height": 750,
}


def profile_dir(profile_id: str) -> Path:
    return PROFILES_DIR / profile_id


def profile_data_dir(profile_id: str) -> Path:
    return profile_dir(profile_id) / "data"


def profile_cache_dir(profile_id: str) -> Path:
    return profile_dir(profile_id) / "cache"


def profile_cookie_file(profile_id: str) -> Path:
    return profile_dir(profile_id) / "cookies.sqlite"