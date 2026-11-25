import json
import os
import shutil
import uuid

from config import (
    BASE_DATA_DIR,
    PROFILES_DIR,
    CONFIG_FILE,
    DEFAULT_URL,
    profile_dir,
    profile_data_dir,
    profile_cache_dir,
    profile_cookie_file,
)


class ProfileManager:
    def __init__(self):
        self.profiles: list[dict] = []
        BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.profiles = data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                self.profiles = []

    def save(self):
        tmp_file = CONFIG_FILE.with_suffix(".tmp")
        try:
            tmp_file.write_text(
                json.dumps(self.profiles, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp_file, CONFIG_FILE)
        except OSError:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except OSError:
                    pass

    def create_profile(self, name: str, url: str = DEFAULT_URL) -> dict:
        profile_id = uuid.uuid4().hex[:12]
        profile = {
            "id": profile_id,
            "name": name,
            "url": url,
            "last_url": url,
            "proxy": "",
            "zoom": 1.0,
        }
        profile_dir(profile_id).mkdir(parents=True, exist_ok=True)
        self.profiles.append(profile)
        self.save()
        return profile

    def rename_profile(self, profile_id: str, new_name: str):
        for p in self.profiles:
            if p["id"] == profile_id:
                p["name"] = new_name
                self.save()
                break

    def update_proxy(self, profile_id: str, proxy_url: str):
        for p in self.profiles:
            if p["id"] == profile_id:
                p["proxy"] = proxy_url.strip()
                self.save()
                break

    def update_zoom(self, profile_id: str, zoom: float):
        zoom = round(max(0.3, min(3.0, float(zoom))), 2)
        for p in self.profiles:
            if p["id"] == profile_id:
                if p.get("zoom", 1.0) != zoom:
                    p["zoom"] = zoom
                    self.save()
                break

    def update_url(self, profile_id: str, url: str):
        if not url or url == "about:blank":
            return
        for p in self.profiles:
            if p["id"] == profile_id:
                if p.get("last_url") != url:
                    p["last_url"] = url
                    self.save()
                break

    def delete_profile(self, profile_id: str):
        d = profile_dir(profile_id)
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
        self.profiles = [p for p in self.profiles if p["id"] != profile_id]
        self.save()

    def get_paths(self, profile_id: str) -> dict:
        return {
            "data": profile_data_dir(profile_id),
            "cache": profile_cache_dir(profile_id),
            "cookies": profile_cookie_file(profile_id),
        }