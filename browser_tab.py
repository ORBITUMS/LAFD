import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")
from gi.repository import Gtk, GLib, WebKit


def get_child_webkit_pids() -> set[int]:
    """Возвращает PID всех дочерних процессов WebKitWebProcess."""
    my_pid = str(os.getpid())
    pids: set[int] = set()
    try:
        for entry in os.scandir("/proc"):
            if not entry.name.isdigit():
                continue
            try:
                with open(f"/proc/{entry.name}/status", "r", encoding="utf-8") as f:
                    name = ""
                    ppid = ""
                    for line in f:
                        if line.startswith("Name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("PPid:"):
                            ppid = line.split(":", 1)[1].strip()
                        if name and ppid:
                            break
                    if ppid == my_pid and "WebKitWeb" in name:
                        pids.add(int(entry.name))
            except OSError:
                continue
    except OSError:
        pass
    return pids


class BrowserTab(Gtk.Box):
    def __init__(
        self,
        profile: dict,
        profile_manager,
        load_html: str | None = None,
        ephemeral: bool = False,
        proxy_enabled: bool = True,
        claimed_pids: set[int] | None = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.profile = profile
        self._popups: list[Gtk.Window] = []
        self._claimed_pids = claimed_pids if claimed_pids is not None else set()
        self.web_pid: int | None = None

        pids_before = get_child_webkit_pids()

        if ephemeral:
            session = WebKit.NetworkSession.new_ephemeral()
        else:
            paths = profile_manager.get_paths(profile["id"])
            paths["data"].mkdir(parents=True, exist_ok=True)
            paths["cache"].mkdir(parents=True, exist_ok=True)

            cookie_path = paths["cookies"]
            if cookie_path.exists() and cookie_path.stat().st_size == 0:
                try:
                    os.remove(cookie_path)
                except OSError:
                    pass

            session = WebKit.NetworkSession.new(str(paths["data"]), str(paths["cache"]))
            session.get_cookie_manager().set_persistent_storage(
                str(cookie_path), WebKit.CookiePersistentStorage.SQLITE
            )

            proxy_uri = (profile.get("proxy") or "").strip()
            if proxy_enabled and proxy_uri:
                try:
                    proxy_settings = WebKit.NetworkProxySettings.new(proxy_uri, None)
                    session.set_proxy_settings(WebKit.NetworkProxyMode.CUSTOM, proxy_settings)
                except Exception:
                    pass

        self.webview = WebKit.WebView(network_session=session)
        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(True)
        settings.set_javascript_can_open_windows_automatically(True)
        self.webview.set_vexpand(True)
        self.webview.set_zoom_level(float(profile.get("zoom", 1.0)))
        self.webview.connect("create", self._on_create_popup)

        if load_html is not None:
            self.webview.load_html(load_html, "about:blank")
        else:
            start_url = profile.get("last_url") or profile.get("url") or "about:blank"
            self.webview.load_uri(start_url)

        self.append(self.webview)

        # Находим PID нового WebKitWebProcess после его запуска
        GLib.timeout_add(450, self._detect_web_pid, pids_before)
        GLib.timeout_add(1600, self._detect_web_pid, pids_before)

    def _detect_web_pid(self, pids_before: set[int]) -> bool:
        if self.web_pid is not None:
            return False
        current = get_child_webkit_pids()
        new_pids = current - pids_before - self._claimed_pids
        if new_pids:
            self.web_pid = max(new_pids)
            self._claimed_pids.add(self.web_pid)
        return False

    def get_ram_mb(self) -> int | None:
        if not self.web_pid:
            return None
        try:
            with open(f"/proc/{self.web_pid}/status", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1])
                        return max(1, round(kb / 1024))
        except (OSError, ValueError, IndexError):
            self._claimed_pids.discard(self.web_pid)
            self.web_pid = None
        return None

    def set_zoom(self, level: float) -> float:
        clamped = round(max(0.3, min(3.0, level)), 2)
        self.webview.set_zoom_level(clamped)
        return clamped

    def _on_create_popup(self, webview: WebKit.WebView, _navigation_action):
        """Открывает OAuth и target=_blank окна в той же изолированной сессии."""
        popup_view = WebKit.WebView(related_view=webview)
        popup_view.set_vexpand(True)
        popup_view.set_hexpand(True)

        popup_win = Gtk.Window(
            title=self.profile.get("name", "Popup"),
            default_width=640,
            default_height=720,
        )
        root_win = self.get_root()
        if isinstance(root_win, Gtk.Window):
            popup_win.set_transient_for(root_win)

        popup_win.set_child(popup_view)
        self._popups.append(popup_win)

        def on_close(*_):
            if popup_win in self._popups:
                self._popups.remove(popup_win)
            popup_win.close()

        popup_view.connect("ready-to-show", lambda *_: popup_win.present())
        popup_view.connect("close", on_close)
        popup_win.connect(
            "close-request",
            lambda *_: (self._popups.remove(popup_win) if popup_win in self._popups else None) or False,
        )
        return popup_view

    def load_uri(self, uri: str):
        self.webview.load_uri(uri)

    def get_current_url(self) -> str:
        uri = self.webview.get_uri()
        if uri and uri != "about:blank":
            return uri
        return self.profile.get("last_url") or self.profile.get("url", "")

    def close(self):
        if self.web_pid is not None:
            self._claimed_pids.discard(self.web_pid)
            self.web_pid = None
        for win in list(self._popups):
            win.close()
        self._popups.clear()
        self.webview.stop_loading()
        self.webview.try_close()