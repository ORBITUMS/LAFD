import base64
import json
import mimetypes
import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("WebKit", "6.0")
from gi.repository import Gtk, Gdk, GLib, WebKit

MAX_DROP_FILE_BYTES = 25 * 1024 * 1024  # 25 MB

def get_child_webkit_pids() -> set[int]:
    """Возвращает PID всех процессов WebKitWebProcess в дереве приложения."""
    my_pid = os.getpid()
    children_map: dict[int, list[int]] = {}
    names: dict[int, str] = {}

    try:
        for entry in os.scandir("/proc"):
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            try:
                with open(f"/proc/{pid}/status", "r", encoding="utf-8") as f:
                    name = ""
                    ppid = -1
                    for line in f:
                        if line.startswith("Name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("PPid:"):
                            ppid = int(line.split(":", 1)[1].strip())
                        if name and ppid != -1:
                            break
                    if ppid != -1:
                        children_map.setdefault(ppid, []).append(pid)
                        names[pid] = name
            except (OSError, ValueError):
                continue
    except OSError:
        return set()

    result: set[int] = set()
    stack = [my_pid]
    visited = {my_pid}
    while stack:
        cur = stack.pop()
        for child in children_map.get(cur, ()):
            if child not in visited:
                visited.add(child)
                stack.append(child)
                if "WebKitWeb" in names.get(child, ""):
                    result.add(child)
    return result

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
        settings.set_javascript_can_access_clipboard(True)
        self.webview.set_vexpand(True)
        self.webview.set_zoom_level(float(profile.get("zoom", 1.0)))
        self.webview.connect("create", self._on_create_popup)
        self.webview.connect("permission-request", self._on_permission_request)

        if load_html is not None:
            self.webview.load_html(load_html, "about:blank")
        else:
            start_url = profile.get("last_url") or profile.get("url") or "about:blank"
            self.webview.load_uri(start_url)

        self.append(self.webview)

        if not ephemeral:
            self._setup_image_paste()
            self._setup_file_drop()

        GLib.timeout_add(450, self._detect_web_pid, pids_before)
        GLib.timeout_add(1600, self._detect_web_pid, pids_before)

    # ==================== Разрешения WebKit ====================
    def _on_permission_request(self, _webview, request):
        if hasattr(WebKit, "ClipboardPermissionRequest") and isinstance(
            request, WebKit.ClipboardPermissionRequest
        ):
            request.allow()
            return True
        return False

    # ==================== Вставка скриншотов (Ctrl+V / Ctrl+М) ====================
    def _setup_image_paste(self):
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_ctrl.connect("key-pressed", self._on_paste_key)
        self.webview.add_controller(key_ctrl)

    def _on_paste_key(self, _ctrl, keyval, _keycode, state):
        is_ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        if not (
            is_ctrl
            and keyval in (Gdk.KEY_v, Gdk.KEY_V, Gdk.KEY_Cyrillic_em, Gdk.KEY_Cyrillic_EM)
        ):
            return False

        display = Gdk.Display.get_default()
        if not display:
            return False

        clipboard = display.get_clipboard()
        formats = clipboard.get_formats()
        has_image = (
            formats.contain_gtype(Gdk.Texture)
            or formats.contain_mime_type("image/png")
            or formats.contain_mime_type("image/jpeg")
        )
        has_text = formats.contain_mime_type("text/plain") or formats.contain_mime_type(
            "text/plain;charset=utf-8"
        )

        if has_image and not has_text:
            clipboard.read_texture_async(None, self._on_clipboard_texture_ready)
            return True
        return False

    def _on_clipboard_texture_ready(self, clipboard, result):
        try:
            texture = clipboard.read_texture_finish(result)
            if not texture:
                return
            png_bytes = texture.save_to_png_bytes().get_data()
            if not png_bytes:
                return
            b64 = base64.b64encode(png_bytes).decode("ascii")
            self._inject_paste_image(b64, "screenshot.png", "image/png")
        except Exception:
            pass

    def _inject_paste_image(self, b64_data: str, filename: str, mime: str):
        js = f"""
        (function() {{
            const b64 = {json.dumps(b64_data)};
            const bin = atob(b64);
            const arr = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
            const file = new File([arr], {json.dumps(filename)}, {{ type: {json.dumps(mime)} }});
            const dt = new DataTransfer();
            dt.items.add(file);
            const target = document.activeElement || document.body;
            const ev = new ClipboardEvent('paste', {{
                clipboardData: dt,
                bubbles: true,
                cancelable: true
            }});
            target.dispatchEvent(ev);
        }})();
        """
        self.webview.evaluate_javascript(js, -1, None, None, None, None, None)

    # ==================== Перетаскивание файлов (Drag & Drop) ====================
    def _setup_file_drop(self):
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        drop_target.connect("enter", self._on_file_drag_enter)
        drop_target.connect("motion", self._on_file_drag_motion)
        drop_target.connect("leave", self._on_file_drag_leave)
        drop_target.connect("drop", self._on_file_drop)
        self.webview.add_controller(drop_target)

    def _on_file_drag_enter(self, _target, _x, _y):
        self.add_css_class("file-drop-active")
        return Gdk.DragAction.COPY

    def _on_file_drag_motion(self, _target, _x, _y):
        return Gdk.DragAction.COPY

    def _on_file_drag_leave(self, _target):
        self.remove_css_class("file-drop-active")

    def _on_file_drop(self, _target, value, x, y):
        self.remove_css_class("file-drop-active")
        if not isinstance(value, Gdk.FileList):
            return False

        files_payload = []
        for gfile in value.get_files():
            path = gfile.get_path()
            if not path or not os.path.isfile(path):
                continue
            try:
                if os.path.getsize(path) > MAX_DROP_FILE_BYTES:
                    continue
                with open(path, "rb") as f:
                    data = f.read()
                mime, _ = mimetypes.guess_type(path)
                files_payload.append({
                    "name": os.path.basename(path),
                    "mime": mime or "application/octet-stream",
                    "b64": base64.b64encode(data).decode("ascii"),
                })
            except OSError:
                continue

        if not files_payload:
            return False

        self._inject_drop_files(files_payload, int(x), int(y))
        return True

    def _inject_drop_files(self, files_payload: list[dict], x: int, y: int):
        js = f"""
        (function() {{
            const items = {json.dumps(files_payload)};
            const dt = new DataTransfer();
            for (const item of items) {{
                const bin = atob(item.b64);
                const arr = new Uint8Array(bin.length);
                for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
                dt.items.add(new File([arr], item.name, {{ type: item.mime }}));
            }}
            const target = document.elementFromPoint({x}, {y}) || document.activeElement || document.body;
            let dropHandled = false;
            for (const type of ['dragenter', 'dragover', 'drop']) {{
                const ev = new DragEvent(type, {{
                    dataTransfer: dt,
                    bubbles: true,
                    cancelable: true,
                    clientX: {x},
                    clientY: {y}
                }});
                target.dispatchEvent(ev);
                if (type === 'drop' && ev.defaultPrevented) {{
                    dropHandled = true;
                }}
            }}
            if (!dropHandled) {{
                const fileInput = document.querySelector('input[type="file"]');
                if (fileInput) {{
                    fileInput.files = dt.files;
                    fileInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            }}
        }})();
        """
        self.webview.evaluate_javascript(js, -1, None, None, None, None, None)

    # ==================== PID и RAM ====================
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