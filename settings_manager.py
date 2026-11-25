import json
import os
from typing import Any

from config import BASE_DATA_DIR, SETTINGS_FILE, DEFAULT_SETTINGS


class SettingsManager:
    def __init__(self):
        self.settings: dict[str, Any] = dict(DEFAULT_SETTINGS)
        BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.settings.update(data)
            except (json.JSONDecodeError, OSError):
                self.settings = dict(DEFAULT_SETTINGS)

    def save(self):
        tmp_file = SETTINGS_FILE.with_suffix(".tmp")
        try:
            tmp_file.write_text(
                json.dumps(self.settings, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp_file, SETTINGS_FILE)
        except OSError:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except OSError:
                    pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        if self.settings.get(key) != value:
            self.settings[key] = value
            self.save()
