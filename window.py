import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from urllib.parse import quote

from browser_tab import BrowserTab
from profile_manager import ProfileManager
from settings_manager import SettingsManager
from settings_window import SettingsWindow
from welcome_page import WelcomePage
from help_content import HELP_HTML
from config import DEFAULT_URL
from i18n import t

HELP_TAB_ID = "__help__"


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application)
        self.set_title("Account Browser")

        self.profile_manager = ProfileManager()
        self.settings_manager = SettingsManager()
        self.set_default_size(
            self.settings_manager.get("window_width", 1100),
            self.settings_manager.get("window_height", 750),
        )

        self.tabs: dict[str, BrowserTab] = {}
        self.buttons: dict[str, Gtk.ToggleButton] = {}
        self._h_wrappers: dict[str, Gtk.Revealer] = {}
        self._h_dots: dict[str, Gtk.Box] = {}
        self._v_rows: dict[str, tuple[Gtk.Button, Gtk.Box]] = {}
        self._v_ram_labels: dict[str, Gtk.Label] = {}
        self._claimed_pids: set[int] = set()
        self._uri_handlers: dict[str, tuple] = {}
        self._recent_order: list[str] = []
        self._open_popovers = 0
        self._footer_hide_timer: int | None = None
        self.onboarding = None
        self._settings_window: SettingsWindow | None = None

        self._apply_app_theme()
        self._setup_shortcuts()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(root)

        self.top_bar = self._build_top_bar()
        root.append(self.top_bar)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.add_css_class("load-progress")
        self.progress_bar.set_visible(False)
        root.append(self.progress_bar)

        self.main_overlay = Gtk.Overlay()
        self.main_overlay.set_vexpand(True)
        root.append(self.main_overlay)

        self.stack = Gtk.Stack()
        self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.main_overlay.set_child(self.stack)

        self.welcome_page = WelcomePage(self.settings_manager)
        self.stack.add_named(self.welcome_page, "welcome")

        # Зона наведения внизу для автоскрытия футера
        self.hover_trigger = Gtk.Box()
        self.hover_trigger.set_halign(Gtk.Align.FILL)
        self.hover_trigger.set_valign(Gtk.Align.END)
        self.hover_trigger.set_size_request(-1, 14)
        trigger_motion = Gtk.EventControllerMotion()
        trigger_motion.connect("enter", self._on_footer_hover_enter)
        self.hover_trigger.add_controller(trigger_motion)
        self.main_overlay.add_overlay(self.hover_trigger)

        # Плавающий стеклянный футер внутри Revealer
        self._build_footer()
        self.footer_revealer = Gtk.Revealer()
        self.footer_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.footer_revealer.set_transition_duration(240)
        self.footer_revealer.set_halign(Gtk.Align.FILL)
        self.footer_revealer.set_valign(Gtk.Align.END)
        self.footer_revealer.set_child(self.footer_container)
        self.footer_revealer.set_reveal_child(True)

        footer_motion = Gtk.EventControllerMotion()
        footer_motion.connect("enter", self._on_footer_hover_enter)
        footer_motion.connect("leave", self._on_footer_hover_leave)
        self.footer_revealer.add_controller(footer_motion)

        self.main_overlay.add_overlay(self.footer_revealer)

        self._apply_theme_to_chrome()
        self._apply_language()
        self._apply_auto_hide_state()
        self._load_existing()
        self.connect("close-request", self._on_close)

        # Периодическое обновление счётчика RAM каждые 3 секунды
        self._ram_timer_id = GLib.timeout_add_seconds(3, self._refresh_ram_usage)

        if self.settings_manager.get("first_run", True):
            GLib.timeout_add(400, self._show_onboarding)

    # ==================== Автоскрытие футера ====================
    def _apply_auto_hide_state(self):
        auto_hide = self.settings_manager.get("auto_hide_footer", False)
        self.hover_trigger.set_visible(auto_hide)
        if not auto_hide:
            self._cancel_hide_timer()
            self.footer_revealer.set_reveal_child(True)
        else:
            self._schedule_footer_hide(900)

    def _cancel_hide_timer(self):
        if self._footer_hide_timer is not None:
            GLib.source_remove(self._footer_hide_timer)
            self._footer_hide_timer = None

    def _schedule_footer_hide(self, delay_ms: int = 450):
        if not self.settings_manager.get("auto_hide_footer", False):
            return
        if self._open_popovers > 0 or self.v_sessions_btn.get_active():
            return
        self._cancel_hide_timer()

        def hide():
            self._footer_hide_timer = None
            if (
                self.settings_manager.get("auto_hide_footer", False)
                and self._open_popovers == 0
                and not self.v_sessions_btn.get_active()
            ):
                self.footer_revealer.set_reveal_child(False)
            return False

        self._footer_hide_timer = GLib.timeout_add(delay_ms, hide)

    def _on_footer_hover_enter(self, *_args):
        self._cancel_hide_timer()
        self.footer_revealer.set_reveal_child(True)

    def _on_footer_hover_leave(self, *_args):
        self._schedule_footer_hide(450)

    # ==================== Горячие клавиши и масштаб ====================
    def _setup_shortcuts(self):
        ctrl = Gtk.EventControllerKey()
        ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(ctrl)

    def _change_zoom(self, delta: float | None):
        tab = self._current_tab()
        if not tab or tab.profile.get("id", "").startswith("__"):
            return
        pid = tab.profile["id"]
        cur = tab.webview.get_zoom_level()
        new_zoom = 1.0 if delta is None else cur + delta
        applied = tab.set_zoom(new_zoom)
        tab.profile["zoom"] = applied
        self.profile_manager.update_zoom(pid, applied)

    def _on_key_pressed(self, _ctrl, keyval, _keycode, state):
        is_ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        is_alt = bool(state & Gdk.ModifierType.ALT_MASK)

        if keyval == Gdk.KEY_F5 or (
            is_ctrl and keyval in (Gdk.KEY_r, Gdk.KEY_R, Gdk.KEY_Cyrillic_ka, Gdk.KEY_Cyrillic_KA)
        ):
            self._on_reload(None)
            return True
        if is_ctrl and keyval in (Gdk.KEY_l, Gdk.KEY_L, Gdk.KEY_Cyrillic_de, Gdk.KEY_Cyrillic_DE):
            if self.top_bar.get_visible() and self.search_entry.get_sensitive():
                self.search_entry.grab_focus()
                self.search_entry.select_region(0, -1)
            return True
        if is_ctrl and keyval in (Gdk.KEY_t, Gdk.KEY_T, Gdk.KEY_Cyrillic_ie, Gdk.KEY_Cyrillic_IE):
            self.footer_revealer.set_reveal_child(True)
            self._on_plus_clicked(self.plus_button)
            return True
        if is_ctrl and keyval in (Gdk.KEY_comma, Gdk.KEY_Cyrillic_be, Gdk.KEY_Cyrillic_BE):
            self._open_settings()
            return True
        if is_ctrl and keyval in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
            self._change_zoom(0.1)
            return True
        if is_ctrl and keyval in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
            self._change_zoom(-0.1)
            return True
        if is_ctrl and keyval in (Gdk.KEY_0, Gdk.KEY_KP_0):
            self._change_zoom(None)
            return True
        if is_alt and keyval == Gdk.KEY_Left:
            self._on_back(None)
            return True
        if is_alt and keyval == Gdk.KEY_Right:
            self._on_forward(None)
            return True
        if is_ctrl and Gdk.KEY_1 <= keyval <= Gdk.KEY_9:
            idx = keyval - Gdk.KEY_1
            if idx < len(self.profile_manager.profiles):
                pid = self.profile_manager.profiles[idx]["id"]
                if pid in self.buttons:
                    self.buttons[pid].set_active(True)
            return True
        return False

    # ==================== Счётчик RAM ====================
    def _update_tab_tooltip(self, pid: str):
        btn = self.buttons.get(pid)
        if not btn:
            return
        tab = self.tabs.get(pid)
        profile = next((p for p in self.profile_manager.profiles if p["id"] == pid), None)
        uri = (tab.webview.get_uri() if tab else None) or (profile.get("last_url", "") if profile else "")

        if self.settings_manager.get("show_ram", True):
            if tab:
                ram = tab.get_ram_mb()
                ram_text = f"{ram} MB" if ram is not None else "..."
            else:
                ram_text = t("ram_sleeping", self._lang())
            tooltip = f"{uri}  •  {ram_text}" if uri else ram_text
        else:
            tooltip = uri

        btn.set_tooltip_text(tooltip)

    def _refresh_ram_usage(self) -> bool:
        show_ram = self.settings_manager.get("show_ram", True)
        lang = self._lang()

        for profile in self.profile_manager.profiles:
            pid = profile["id"]
            self._update_tab_tooltip(pid)

            ram_lbl = self._v_ram_labels.get(pid)
            if not ram_lbl:
                continue
            ram_lbl.set_visible(show_ram)
            if not show_ram:
                continue

            tab = self.tabs.get(pid)
            if tab:
                ram = tab.get_ram_mb()
                ram_lbl.set_text(f"{ram} MB" if ram is not None else "…")
            else:
                ram_lbl.set_text(t("ram_sleeping", lang))

        return True

    # ==================== Вспомогательные методы ====================
    def _create_glass_popover(self, parent: Gtk.Widget) -> Gtk.Popover:
        self._open_popovers += 1
        self._cancel_hide_timer()

        popover = Gtk.Popover()
        popover.add_css_class("glass-popover")
        if self._is_light():
            popover.add_css_class("light")
        popover.set_parent(parent)
        popover.set_position(Gtk.PositionType.TOP)
        popover.set_has_arrow(False)
        popover.set_offset(0, -10)
        popover.set_autohide(True)

        def on_closed(p):
            self._open_popovers = max(0, self._open_popovers - 1)
            self._schedule_footer_hide(450)
            GLib.idle_add(lambda: (p.unparent() if p.get_parent() else None) or False)

        popover.connect("closed", on_closed)
        return popover

    def _make_menu_button(self, label: str, icon_name: str | None = None, destructive: bool = False) -> Gtk.Button:
        btn = Gtk.Button()
        btn.add_css_class("menu-item-btn")
        if destructive:
            btn.add_css_class("destructive")

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_halign(Gtk.Align.START)
        if icon_name:
            img = Gtk.Image.new_from_icon_name(icon_name)
            img.set_pixel_size(15)
            box.append(img)
        lbl = Gtk.Label(label=label)
        lbl.set_halign(Gtk.Align.START)
        box.append(lbl)
        btn.set_child(box)
        return btn

    def _lang(self) -> str:
        return self.settings_manager.get("language", "en")

    def _is_light(self) -> bool:
        return self.settings_manager.get("theme", "dark") == "light"

    def _apply_app_theme(self):
        Gtk.Settings.get_default().set_property(
            "gtk-application-prefer-dark-theme",
            self.settings_manager.get("theme", "dark") == "dark",
        )

    def _apply_theme_to_chrome(self):
        is_light = self._is_light()
        for w in (self.footer_container, self.top_bar, self.welcome_page, self.v_sessions_popover):
            if is_light:
                w.add_css_class("light")
            else:
                w.remove_css_class("light")

    def _apply_language(self):
        lang = self._lang()
        self.search_entry.set_placeholder_text(t("search_placeholder", lang))
        self.plus_button.set_tooltip_text(t("create_session_tooltip", lang))
        self.quick_links_btn.set_tooltip_text(t("quick_links_tooltip", lang))
        self.gear_button.set_tooltip_text(t("settings_tooltip", lang))
        self._update_v_button_label()
        self.welcome_page.update_language()

    def _update_status_dots(self):
        show_dots = self.settings_manager.get("status_dots", True)
        current = self.stack.get_visible_child_name()
        recent_two = [pid for pid in self._recent_order if pid != current][:2]

        for pid in set(self._h_dots.keys()) | set(self._v_rows.keys()):
            if pid == current:
                state_cls = "active"
            elif pid not in self.tabs and pid != HELP_TAB_ID:
                state_cls = "sleeping"
            elif pid in recent_two:
                state_cls = "recent"
            else:
                state_cls = "old"

            if pid in self._h_dots:
                dot = self._h_dots[pid]
                dot.set_visible(show_dots)
                for c in ("active", "recent", "old", "sleeping"):
                    dot.remove_css_class(c)
                dot.add_css_class(state_cls)

            if pid in self._v_rows:
                v_btn, v_dot = self._v_rows[pid]
                v_dot.set_visible(show_dots)
                for c in ("active", "recent", "old", "sleeping"):
                    v_dot.remove_css_class(c)
                v_dot.add_css_class(state_cls)
                if pid == current:
                    v_btn.add_css_class("active-session")
                else:
                    v_btn.remove_css_class("active-session")

    def _update_v_button_label(self):
        lang = self._lang()
        current = self.stack.get_visible_child_name()
        if current and current in self.buttons:
            profile = next((p for p in self.profile_manager.profiles if p["id"] == current), None)
            name = profile["name"] if profile else t("help_tab_title", lang)
            self.v_btn_label.set_label(name)
            self.v_sessions_btn.set_tooltip_text(name)
        else:
            has_items = bool(self.profile_manager.profiles) or (HELP_TAB_ID in self.tabs)
            self.v_btn_label.set_label(t("sessions_btn", lang) if has_items else t("empty_sessions", lang))
            self.v_sessions_btn.set_tooltip_text(t("sessions_btn", lang))

        self._update_status_dots()

    # ==================== Верхняя навигация ====================
    def _build_top_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.add_css_class("top-bar")
        bar.set_margin_start(8)
        bar.set_margin_end(8)
        bar.set_margin_top(6)
        bar.set_margin_bottom(2)
        bar.set_visible(False)

        self.back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.back_button.add_css_class("nav-btn")
        self.back_button.set_sensitive(False)
        self.back_button.connect("clicked", self._on_back)
        bar.append(self.back_button)

        self.forward_button = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.forward_button.add_css_class("nav-btn")
        self.forward_button.set_sensitive(False)
        self.forward_button.connect("clicked", self._on_forward)
        bar.append(self.forward_button)

        self.reload_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.reload_button.add_css_class("nav-btn")
        self.reload_button.connect("clicked", self._on_reload)
        bar.append(self.reload_button)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("activate", self._on_search)
        bar.append(self.search_entry)
        return bar

    def _on_back(self, _):
        tab = self._current_tab()
        if tab and not tab.profile.get("id", "").startswith("__") and tab.webview.can_go_back():
            tab.webview.go_back()

    def _on_forward(self, _):
        tab = self._current_tab()
        if tab and not tab.profile.get("id", "").startswith("__") and tab.webview.can_go_forward():
            tab.webview.go_forward()

    def _on_reload(self, _):
        tab = self._current_tab()
        if not tab or tab.profile.get("id", "").startswith("__"):
            return
        if tab.webview.is_loading():
            tab.webview.stop_loading()
        else:
            tab.webview.reload()

    def _on_search(self, entry):
        query = entry.get_text().strip()
        if not query:
            return
        tab = self._current_tab()
        if not tab or tab.profile.get("id", "").startswith("__"):
            return

        if query.startswith(("http://", "https://", "file://")):
            target = query
        elif query.startswith("localhost") or query.startswith("127.0.0.1"):
            target = f"http://{query}"
        elif "." in query and " " not in query:
            target = f"https://{query}"
        else:
            target = f"https://www.google.com/search?q={quote(query)}"

        tab.load_uri(target)
        tab.webview.grab_focus()

    def _current_tab(self) -> BrowserTab | None:
        current = self.stack.get_visible_child_name()
        return self.tabs.get(current) if current else None

    def _sync_address_bar(self):
        tab = self._current_tab()
        if not tab or tab.profile.get("id", "").startswith("__"):
            self.search_entry.set_text("")
            return
        if not self.search_entry.has_focus():
            uri = tab.webview.get_uri() or ""
            self.search_entry.set_text("" if uri == "about:blank" else uri)

    def _update_progress(self):
        tab = self._current_tab()
        if not tab or tab.profile.get("id", "").startswith("__"):
            self.progress_bar.set_visible(False)
            return
        wv = tab.webview
        progress = wv.get_estimated_load_progress()
        if wv.is_loading() and 0.0 < progress < 1.0:
            self.progress_bar.set_fraction(progress)
            self.progress_bar.set_visible(True)
        else:
            self.progress_bar.set_visible(False)

    def _update_nav_state(self):
        current = self.stack.get_visible_child_name()
        if current in (None, "welcome"):
            self.top_bar.set_visible(False)
            self.progress_bar.set_visible(False)
            self._update_v_button_label()
            return

        self.top_bar.set_visible(True)
        tab = self.tabs.get(current)
        if not tab:
            for b in (self.back_button, self.forward_button, self.reload_button):
                b.set_sensitive(False)
            self.search_entry.set_sensitive(False)
            self.progress_bar.set_visible(False)
            return

        wv = tab.webview
        is_help = tab.profile.get("id", "").startswith("__")
        self.back_button.set_sensitive(not is_help and wv.can_go_back())
        self.forward_button.set_sensitive(not is_help and wv.can_go_forward())
        self.reload_button.set_sensitive(not is_help)
        self.reload_button.set_icon_name(
            "process-stop-symbolic" if (not is_help and wv.is_loading()) else "view-refresh-symbolic"
        )
        self.search_entry.set_sensitive(not is_help)
        self._sync_address_bar()
        self._update_progress()
        self._update_v_button_label()

    # ==================== Плавающий стеклянный футер ====================
    def _build_footer(self):
        self.footer_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.footer_container.add_css_class("footer")
        self.footer_container.set_halign(Gtk.Align.FILL)
        self.footer_container.set_margin_start(16)
        self.footer_container.set_margin_end(16)
        self.footer_container.set_margin_bottom(14)

        self.left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.left_box.set_halign(Gtk.Align.START)
        self.left_box.set_valign(Gtk.Align.CENTER)
        self.left_box.set_hexpand(True)
        self.footer_container.append(self.left_box)

        # Прокручиваемый горизонтальный список сессий + надёжный Drag & Drop на контейнере
        self.h_sessions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.h_sessions_box.set_halign(Gtk.Align.START)
        self._setup_container_reorder()

        self.h_sessions_scroll = Gtk.ScrolledWindow()
        self.h_sessions_scroll.add_css_class("h-sessions-scroll")
        self.h_sessions_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.h_sessions_scroll.set_propagate_natural_width(True)
        self.h_sessions_scroll.set_propagate_natural_height(True)
        self.h_sessions_scroll.set_child(self.h_sessions_box)

        # Кнопка вертикального списка
        self.v_sessions_btn = Gtk.MenuButton()
        self.v_sessions_btn.add_css_class("footer-btn")

        v_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.v_btn_label = Gtk.Label(label="Сессии")
        self.v_btn_label.set_max_width_chars(22)
        v_btn_box.append(self.v_btn_label)
        v_chevron = Gtk.Image.new_from_icon_name("pan-up-symbolic")
        v_chevron.set_pixel_size(14)
        v_btn_box.append(v_chevron)
        self.v_sessions_btn.set_child(v_btn_box)

        self.v_sessions_popover = Gtk.Popover()
        self.v_sessions_popover.add_css_class("glass-popover")
        self.v_sessions_popover.set_position(Gtk.PositionType.TOP)
        self.v_sessions_popover.set_has_arrow(False)
        self.v_sessions_popover.set_offset(0, -10)
        self.v_sessions_popover.connect("closed", lambda _: self._schedule_footer_hide(450))
        self.v_sessions_btn.connect("notify::active", lambda btn, _: self._refresh_ram_usage() if btn.get_active() else None)

        self.v_list_box = Gtk.ListBox()
        self.v_list_box.add_css_class("v-sessions-list")
        self.v_list_box.set_selection_mode(Gtk.SelectionMode.NONE)

        v_scroll = Gtk.ScrolledWindow()
        v_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        v_scroll.set_max_content_height(320)
        v_scroll.set_min_content_width(240)
        v_scroll.set_propagate_natural_width(True)
        v_scroll.set_propagate_natural_height(True)
        v_scroll.set_child(self.v_list_box)

        self.v_sessions_popover.set_child(v_scroll)
        self.v_sessions_btn.set_popover(self.v_sessions_popover)

        # Кнопка Плюс
        self.plus_button = Gtk.Button(label="+")
        self.plus_button.add_css_class("footer-btn")
        self.plus_button.add_css_class("plus-btn")
        self.plus_button.connect("clicked", self._on_plus_clicked)

        # Кнопка Быстрых ссылок (Синий плюс)
        self.quick_links_btn = Gtk.Button(label="+")
        self.quick_links_btn.add_css_class("quick-link-btn")
        self.quick_links_btn.connect("clicked", self._on_quick_links_clicked)

        # Шестерёнка
        self.gear_button = Gtk.Button(label="⚙")
        self.gear_button.add_css_class("footer-btn")
        self.gear_button.add_css_class("gear-btn")
        self.gear_button.connect("clicked", lambda _: self._open_settings())
        self.footer_container.append(self.gear_button)

    def _update_h_scroll_visibility(self):
        has_items = bool(self.profile_manager.profiles) or (HELP_TAB_ID in self.tabs)
        self.h_sessions_scroll.set_visible(has_items)

    def _apply_orientation(self):
        ori = self.settings_manager.get("orientation", "horizontal")

        child = self.left_box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.left_box.remove(child)
            child = nxt

        if ori == "horizontal":
            self.left_box.append(self.h_sessions_scroll)
        else:
            self.left_box.append(self.v_sessions_btn)

        self.left_box.append(self.plus_button)
        self.left_box.append(self.quick_links_btn)

        self._rebuild_sessions()

    def _disconnect_uri_handler(self, pid: str):
        if pid in self._uri_handlers:
            wv, hid = self._uri_handlers.pop(pid)
            try:
                wv.disconnect(hid)
            except Exception:
                pass

    def _rebuild_sessions(self):
        current_visible = self.stack.get_visible_child_name()

        for pid in list(self._uri_handlers.keys()):
            self._disconnect_uri_handler(pid)

        for container in (self.h_sessions_box, self.v_list_box):
            child = container.get_first_child()
            while child:
                nxt = child.get_next_sibling()
                container.remove(child)
                child = nxt

        self.buttons.clear()
        self._h_wrappers.clear()
        self._h_dots.clear()
        self._v_rows.clear()
        self._v_ram_labels.clear()

        for profile in self.profile_manager.profiles:
            self._add_session_button(profile, animate=False)

        if HELP_TAB_ID in self.tabs:
            self._add_help_button()

        if current_visible and current_visible in self.buttons:
            btn = self.buttons[current_visible]
            btn.handler_block_by_func(self._on_button_toggled)
            btn.set_active(True)
            btn.handler_unblock_by_func(self._on_button_toggled)

        self._update_h_scroll_visibility()
        self._update_v_button_label()
        self._refresh_ram_usage()
        self.quick_links_btn.set_visible(self.settings_manager.get("suggestions", True))

    def _add_session_button(self, profile: dict, animate: bool = True):
        pid = profile["id"]

        # Горизонтальная кнопка со статус-точкой
        h_btn = Gtk.ToggleButton()
        h_btn.add_css_class("footer-btn")

        h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        h_dot = Gtk.Box()
        h_dot.add_css_class("status-dot")
        h_dot.set_valign(Gtk.Align.CENTER)
        h_box.append(h_dot)

        h_lbl = Gtk.Label(label=profile["name"])
        h_box.append(h_lbl)
        h_btn.set_child(h_box)

        h_btn.connect("toggled", self._on_button_toggled, pid)
        self._attach_context_menu(h_btn, profile)

        rev = Gtk.Revealer()
        rev.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)
        rev.set_transition_duration(220 if animate else 0)
        rev.set_child(h_btn)
        self.h_sessions_box.append(rev)
        rev.set_reveal_child(True)

        self.buttons[pid] = h_btn
        self._h_wrappers[pid] = rev
        self._h_dots[pid] = h_dot

        # Вертикальная строка-пилюля со статус-точкой и RAM-бейджем
        row = Gtk.ListBoxRow()
        v_btn = Gtk.Button()
        v_btn.add_css_class("v-row-btn")
        v_btn.set_halign(Gtk.Align.FILL)

        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        v_dot = Gtk.Box()
        v_dot.add_css_class("status-dot")
        v_dot.set_valign(Gtk.Align.CENTER)
        row_box.append(v_dot)

        lbl = Gtk.Label(label=profile["name"])
        lbl.set_xalign(0.0)
        lbl.set_width_chars(14)
        lbl.set_max_width_chars(24)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.set_halign(Gtk.Align.FILL)
        lbl.set_hexpand(True)
        row_box.append(lbl)

        ram_lbl = Gtk.Label()
        ram_lbl.add_css_class("ram-badge")
        ram_lbl.set_valign(Gtk.Align.CENTER)
        ram_lbl.set_visible(self.settings_manager.get("show_ram", True))
        row_box.append(ram_lbl)

        v_btn.set_child(row_box)
        v_btn.connect("clicked", lambda _, p=pid: (self._on_button_toggled_v(p), self.v_sessions_popover.popdown()))
        self._attach_context_menu(v_btn, profile)
        row.set_child(v_btn)
        self.v_list_box.append(row)
        self._v_rows[pid] = (v_btn, v_dot)
        self._v_ram_labels[pid] = ram_lbl

        self._bind_tab_uri_to_button(pid, h_btn)
        self._update_h_scroll_visibility()
        self._update_status_dots()
        self._refresh_ram_usage()

    def _bind_tab_uri_to_button(self, pid: str, h_btn: Gtk.Widget):
        self._disconnect_uri_handler(pid)
        tab = self.tabs.get(pid)
        if not tab:
            self._update_tab_tooltip(pid)
            return

        def on_uri(_wv, _p):
            self._update_tab_tooltip(pid)
            if self.stack.get_visible_child_name() == pid:
                self._sync_address_bar()

        self._update_tab_tooltip(pid)
        hid = tab.webview.connect("notify::uri", on_uri)
        self._uri_handlers[pid] = (tab.webview, hid)

    def _on_button_toggled_v(self, pid: str):
        if pid in self.buttons:
            self.buttons[pid].set_active(True)

    # ==================== Надёжное живое перетаскивание вкладок ====================
    def _setup_container_reorder(self):
        gesture = Gtk.GestureDrag()
        gesture.set_button(1)
        gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        state = {"pid": None, "start_x": 0.0, "dragging": False}

        def find_pid_at(x: float) -> str | None:
            for p in self.profile_manager.profiles:
                pid = p["id"]
                wrapper = self._h_wrappers.get(pid)
                if not wrapper:
                    continue
                ok, rect = wrapper.compute_bounds(self.h_sessions_box)
                if ok and rect.origin.x <= x <= rect.origin.x + rect.size.width:
                    return pid
            return None

        def on_begin(_g, start_x, _start_y):
            state["pid"] = None
            state["dragging"] = False
            if not self.settings_manager.get("drag_and_drop", False):
                return
            state["pid"] = find_pid_at(start_x)
            state["start_x"] = start_x

        def on_update(g, offset_x, _offset_y):
            pid = state["pid"]
            if not pid:
                return
            if not state["dragging"]:
                if abs(offset_x) < 12:
                    return
                state["dragging"] = True
                g.set_state(Gtk.EventSequenceState.CLAIMED)
                if pid in self.buttons:
                    self.buttons[pid].add_css_class("dragging")

            cur_x = state["start_x"] + offset_x
            profiles = self.profile_manager.profiles
            idx = next((i for i, p in enumerate(profiles) if p["id"] == pid), -1)
            if idx == -1:
                return

            if idx < len(profiles) - 1:
                right_id = profiles[idx + 1]["id"]
                ok, rect = self._h_wrappers[right_id].compute_bounds(self.h_sessions_box)
                if ok and cur_x > rect.origin.x + rect.size.width * 0.45:
                    profiles[idx], profiles[idx + 1] = profiles[idx + 1], profiles[idx]
                    self.h_sessions_box.reorder_child_after(
                        self._h_wrappers[pid], self._h_wrappers[right_id]
                    )
                    return

            if idx > 0:
                left_id = profiles[idx - 1]["id"]
                ok, rect = self._h_wrappers[left_id].compute_bounds(self.h_sessions_box)
                if ok and cur_x < rect.origin.x + rect.size.width * 0.55:
                    profiles[idx], profiles[idx - 1] = profiles[idx - 1], profiles[idx]
                    prev_sibling = self._h_wrappers[profiles[idx - 2]["id"]] if idx >= 2 else None
                    self.h_sessions_box.reorder_child_after(self._h_wrappers[pid], prev_sibling)

        def on_end(_g, _offset_x, _offset_y):
            pid = state["pid"]
            if state["dragging"] and pid:
                if pid in self.buttons:
                    self.buttons[pid].remove_css_class("dragging")
                self.profile_manager.save()
                GLib.idle_add(lambda: self._rebuild_sessions() or False)
            state["pid"] = None
            state["dragging"] = False

        gesture.connect("drag-begin", on_begin)
        gesture.connect("drag-update", on_update)
        gesture.connect("drag-end", on_end)
        self.h_sessions_box.add_controller(gesture)

    # ==================== Контекстное меню (macOS стиль) ====================
    def _attach_context_menu(self, button: Gtk.Widget, profile: dict):
        gesture = Gtk.GestureClick()
        gesture.set_button(3)
        gesture.connect("pressed", self._on_right_click, button, profile)
        button.add_controller(gesture)

    def _on_right_click(self, _gesture, _n_press, _x, _y, button: Gtk.Widget, profile: dict):
        lang = self._lang()
        pid = profile["id"]
        popover = self._create_glass_popover(button)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        stack.set_transition_duration(150)
        stack.set_hhomogeneous(False)
        stack.set_vhomogeneous(False)
        popover.set_child(stack)

        # 1. Основное меню
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        menu_box.set_size_request(195, -1)

        rename_btn = self._make_menu_button(t("rename_btn", lang), "document-edit-symbolic")
        rename_btn.connect("clicked", lambda _: stack.set_visible_child_name("rename"))
        menu_box.append(rename_btn)

        if pid in self.tabs:
            sleep_btn = self._make_menu_button(t("sleep_btn", lang), "weather-clear-night-symbolic")
            sleep_btn.connect(
                "clicked",
                lambda _: (popover.popdown(), GLib.idle_add(lambda: self._on_sleep_session(profile) or False)),
            )
            menu_box.append(sleep_btn)

        if self.settings_manager.get("proxy_enabled", True):
            proxy_btn = self._make_menu_button(t("proxy_btn", lang), "network-server-symbolic")
            proxy_btn.connect("clicked", lambda _: stack.set_visible_child_name("proxy"))
            menu_box.append(proxy_btn)

        sep = Gtk.Separator()
        sep.add_css_class("popover-sep")
        menu_box.append(sep)

        delete_btn = self._make_menu_button(t("delete_btn", lang), "user-trash-symbolic", destructive=True)
        delete_btn.connect("clicked", lambda _: stack.set_visible_child_name("delete"))
        menu_box.append(delete_btn)
        stack.add_named(menu_box, "menu")

        # 2. Подтверждение удаления
        del_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for m in ("top", "bottom", "start", "end"):
            getattr(del_box, f"set_margin_{m}")(2)

        cancel_btn = self._make_menu_button(t("close_btn", lang))
        cancel_btn.connect("clicked", lambda _: stack.set_visible_child_name("menu"))
        del_box.append(cancel_btn)

        confirm_btn = self._make_menu_button(t("confirm_btn", lang), "user-trash-symbolic", destructive=True)
        confirm_btn.connect(
            "clicked",
            lambda _: (popover.popdown(), GLib.idle_add(lambda: self._on_deleted(profile) or False)),
        )
        del_box.append(confirm_btn)
        stack.add_named(del_box, "delete")

        # 3. Переименование
        ren_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for m in ("top", "bottom", "start", "end"):
            getattr(ren_box, f"set_margin_{m}")(4)

        ren_entry = Gtk.Entry()
        ren_entry.add_css_class("glass-entry")
        ren_entry.set_placeholder_text(t("new_name_placeholder", lang))
        ren_entry.set_text(profile["name"])
        ren_box.append(ren_entry)

        def submit_rename(*_):
            text = ren_entry.get_text().strip()
            if text:
                popover.popdown()
                self._on_renamed(profile, text)

        ren_entry.connect("activate", submit_rename)
        ren_ctrl = Gtk.EventControllerKey()
        ren_ctrl.connect(
            "key-pressed",
            lambda _c, keyval, _kc, _st: (stack.set_visible_child_name("menu"), True)
            if keyval == Gdk.KEY_Escape
            else False,
        )
        ren_entry.add_controller(ren_ctrl)
        stack.add_named(ren_box, "rename")

        # 4. Настройка прокси
        proxy_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for m in ("top", "bottom", "start", "end"):
            getattr(proxy_box, f"set_margin_{m}")(4)

        proxy_entry = Gtk.Entry()
        proxy_entry.add_css_class("glass-entry")
        proxy_entry.set_placeholder_text(t("proxy_placeholder", lang))
        proxy_entry.set_text(profile.get("proxy", ""))
        proxy_box.append(proxy_entry)

        def submit_proxy(*_):
            popover.popdown()
            self._on_proxy_changed(profile, proxy_entry.get_text().strip())

        proxy_entry.connect("activate", submit_proxy)
        proxy_ctrl = Gtk.EventControllerKey()
        proxy_ctrl.connect(
            "key-pressed",
            lambda _c, keyval, _kc, _st: (stack.set_visible_child_name("menu"), True)
            if keyval == Gdk.KEY_Escape
            else False,
        )
        proxy_entry.add_controller(proxy_ctrl)
        stack.add_named(proxy_box, "proxy")

        popover.popup()

        def on_stack_changed(stk, _p):
            name = stk.get_visible_child_name()
            if name == "rename":
                GLib.idle_add(lambda: self._focus_entry(ren_entry) or False)
            elif name == "proxy":
                GLib.idle_add(lambda: self._focus_entry(proxy_entry) or False)

        stack.connect("notify::visible-child-name", on_stack_changed)

    def _focus_entry(self, entry: Gtk.Entry) -> bool:
        entry.grab_focus()
        entry.select_region(0, -1)
        return False

    # ==================== Загрузка / Переключение ====================
    def _load_existing(self):
        self._apply_orientation()

        if not self.profile_manager.profiles:
            self.stack.set_visible_child_name("welcome")
            self._update_nav_state()
            return

        target_id = self.settings_manager.get("last_active_profile")
        if target_id not in self.buttons:
            target_id = self.profile_manager.profiles[0]["id"]

        self.buttons[target_id].set_active(True)

    def _get_or_create_tab(self, profile_id: str) -> BrowserTab | None:
        if profile_id in self.tabs:
            return self.tabs[profile_id]

        profile = next((p for p in self.profile_manager.profiles if p["id"] == profile_id), None)
        if not profile:
            return None

        tab = BrowserTab(
            profile,
            self.profile_manager,
            proxy_enabled=self.settings_manager.get("proxy_enabled", True),
            claimed_pids=self._claimed_pids,
        )
        self.stack.add_named(tab, profile_id)
        self.tabs[profile_id] = tab

        wv = tab.webview
        wv.connect("notify::can-go-back", lambda *_: self._update_nav_state())
        wv.connect("notify::can-go-forward", lambda *_: self._update_nav_state())
        wv.connect("notify::is-loading", lambda *_: self._update_nav_state())
        wv.connect("notify::estimated-load-progress", lambda *_: self._update_progress())
        wv.connect("load-changed", lambda *_: self._update_nav_state())

        if profile_id in self.buttons:
            self._bind_tab_uri_to_button(profile_id, self.buttons[profile_id])

        return tab

    def _on_button_toggled(self, button: Gtk.ToggleButton, profile_id: str):
        if not button.get_active():
            return

        current = self.stack.get_visible_child_name()
        if current and current in self.tabs and not current.startswith("__"):
            url = self.tabs[current].get_current_url()
            if url:
                self.profile_manager.update_url(current, url)

        for pid, btn in self.buttons.items():
            if pid != profile_id and btn.get_active():
                btn.handler_block_by_func(self._on_button_toggled)
                btn.set_active(False)
                btn.handler_unblock_by_func(self._on_button_toggled)

        if not profile_id.startswith("__"):
            self._get_or_create_tab(profile_id)
            self.settings_manager.set("last_active_profile", profile_id)
            if profile_id in self._recent_order:
                self._recent_order.remove(profile_id)
            self._recent_order.insert(0, profile_id)

        self.stack.set_visible_child_name(profile_id)
        self._update_nav_state()

    # ==================== Действия с сессиями ====================
    def _on_sleep_session(self, profile: dict) -> bool:
        pid = profile["id"]
        self._disconnect_uri_handler(pid)
        tab = self.tabs.pop(pid, None)
        if tab:
            url = tab.get_current_url()
            if url:
                self.profile_manager.update_url(pid, url)
            tab.close()
            self.stack.remove(tab)

        if self.stack.get_visible_child_name() == pid:
            btn = self.buttons.get(pid)
            if btn:
                btn.handler_block_by_func(self._on_button_toggled)
                btn.set_active(False)
                btn.handler_unblock_by_func(self._on_button_toggled)
            self.stack.set_visible_child_name("welcome")

        self._update_nav_state()
        self._refresh_ram_usage()
        return False

    def _on_proxy_changed(self, profile: dict, proxy_url: str):
        pid = profile["id"]
        self.profile_manager.update_proxy(pid, proxy_url)
        profile["proxy"] = proxy_url

        if pid in self.tabs:
            was_active = self.stack.get_visible_child_name() == pid
            self._on_sleep_session(profile)
            if was_active and pid in self.buttons:
                self.buttons[pid].set_active(True)

    def _on_plus_clicked(self, button: Gtk.Widget):
        lang = self._lang()
        popover = self._create_glass_popover(button)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for m in ("top", "bottom", "start", "end"):
            getattr(box, f"set_margin_{m}")(4)

        entry = Gtk.Entry()
        entry.add_css_class("glass-entry")
        entry.set_placeholder_text(t("session_name_placeholder", lang))
        box.append(entry)

        def submit(*_):
            text = entry.get_text().strip()
            if text:
                popover.popdown()
                self._on_session_created(text)

        entry.connect("activate", submit)
        ctrl = Gtk.EventControllerKey()
        ctrl.connect(
            "key-pressed",
            lambda _c, keyval, _kc, _st: (popover.popdown(), True)
            if keyval == Gdk.KEY_Escape
            else False,
        )
        entry.add_controller(ctrl)

        popover.set_child(box)
        popover.popup()
        GLib.idle_add(lambda: self._focus_entry(entry) or False)

    def _on_quick_links_clicked(self, button: Gtk.Widget):
        popover = self._create_glass_popover(button)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_size_request(190, -1)

        header = Gtk.Label(label=t("quick_links_tooltip", self._lang()).upper())
        header.add_css_class("popover-header")
        header.set_halign(Gtk.Align.START)
        box.append(header)

        sites = [
            ("DeepSeek", "https://chat.deepseek.com/"),
            ("ChatGPT", "https://chatgpt.com/"),
            ("Claude", "https://claude.ai/"),
            ("Google", "https://www.google.com/"),
        ]

        for name, url in sites:
            btn = self._make_menu_button(name, "web-browser-symbolic")
            btn.connect(
                "clicked",
                lambda _, n=name, u=url: (popover.popdown(), self._on_quick_session_created(n, u)),
            )
            box.append(btn)

        popover.set_child(box)
        popover.popup()

    def _on_quick_session_created(self, name, url):
        profile = self.profile_manager.create_profile(name, url)
        self._get_or_create_tab(profile["id"])
        self._add_session_button(profile, animate=True)
        self.buttons[profile["id"]].set_active(True)
        self._update_v_button_label()

    def _on_session_created(self, name: str):
        default_url = self.settings_manager.get("default_url", DEFAULT_URL) or DEFAULT_URL
        profile = self.profile_manager.create_profile(name, default_url)
        self._get_or_create_tab(profile["id"])
        self._add_session_button(profile, animate=True)
        self.buttons[profile["id"]].set_active(True)
        self._update_v_button_label()

    def _on_renamed(self, profile: dict, new_name: str):
        self.profile_manager.rename_profile(profile["id"], new_name)
        profile["name"] = new_name
        self._rebuild_sessions()

    def _on_deleted(self, profile: dict) -> bool:
        pid = profile["id"]
        self._disconnect_uri_handler(pid)
        if pid in self._recent_order:
            self._recent_order.remove(pid)

        tab = self.tabs.pop(pid, None)
        if tab:
            tab.close()
            self.stack.remove(tab)

        self.profile_manager.delete_profile(pid)

        if self.settings_manager.get("last_active_profile") == pid:
            self.settings_manager.set("last_active_profile", None)

        self._rebuild_sessions()

        if self.profile_manager.profiles:
            first_id = self.profile_manager.profiles[0]["id"]
            self.buttons[first_id].set_active(True)
        elif HELP_TAB_ID in self.tabs:
            self.buttons[HELP_TAB_ID].set_active(True)
        else:
            self.stack.set_visible_child_name("welcome")

        self._update_nav_state()
        return False

    # ==================== Помощь ====================
    def _open_help_tab(self):
        if HELP_TAB_ID in self.tabs:
            self.buttons[HELP_TAB_ID].set_active(True)
            return

        profile = {"id": HELP_TAB_ID, "name": t("help_tab_title", self._lang()), "url": "about:blank"}
        tab = BrowserTab(profile, self.profile_manager, load_html=HELP_HTML, ephemeral=True)
        self.stack.add_named(tab, HELP_TAB_ID)
        self.tabs[HELP_TAB_ID] = tab

        self._add_help_button()
        self.buttons[HELP_TAB_ID].set_active(True)
        self._update_v_button_label()

    def _add_help_button(self):
        title = t("help_tab_title", self._lang())

        btn = Gtk.ToggleButton(label=title)
        btn.add_css_class("footer-btn")
        btn.connect("toggled", self._on_button_toggled, HELP_TAB_ID)
        self._attach_help_context_menu(btn)
        self.h_sessions_box.append(btn)
        self.buttons[HELP_TAB_ID] = btn

        row = Gtk.ListBoxRow()
        v_btn = Gtk.Button()
        v_btn.add_css_class("v-row-btn")
        v_btn.set_halign(Gtk.Align.FILL)

        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dot = Gtk.Box()
        dot.add_css_class("status-dot")
        dot.set_valign(Gtk.Align.CENTER)
        row_box.append(dot)

        lbl = Gtk.Label(label=title)
        lbl.set_halign(Gtk.Align.START)
        row_box.append(lbl)

        v_btn.set_child(row_box)
        v_btn.connect("clicked", lambda _: (self._on_button_toggled_v(HELP_TAB_ID), self.v_sessions_popover.popdown()))
        self._attach_help_context_menu(v_btn)
        row.set_child(v_btn)
        self.v_list_box.append(row)
        self._v_rows[HELP_TAB_ID] = (v_btn, dot)
        self._update_h_scroll_visibility()

    def _attach_help_context_menu(self, widget: Gtk.Widget):
        def on_help_right_click(_g, _n, _x, _y, b):
            popover = self._create_glass_popover(b)
            close_btn = self._make_menu_button(t("close_btn", self._lang()), "window-close-symbolic")
            close_btn.connect(
                "clicked",
                lambda _: (popover.popdown(), GLib.idle_add(lambda: self._close_help_tab() or False)),
            )
            popover.set_child(close_btn)
            popover.popup()

        gesture = Gtk.GestureClick()
        gesture.set_button(3)
        gesture.connect("pressed", on_help_right_click, widget)
        widget.add_controller(gesture)

    def _close_help_tab(self) -> bool:
        if HELP_TAB_ID not in self.tabs:
            return False
        tab = self.tabs.pop(HELP_TAB_ID)
        tab.close()
        self.stack.remove(tab)
        self.buttons.pop(HELP_TAB_ID, None)
        self._rebuild_sessions()

        if self.profile_manager.profiles:
            self.buttons[self.profile_manager.profiles[0]["id"]].set_active(True)
        else:
            self.stack.set_visible_child_name("welcome")
        self._update_nav_state()
        return False

    # ==================== Настройки и первая подсказка ====================
    def _open_settings(self):
        if self._settings_window is not None:
            self._settings_window.present()
            return

        win = SettingsWindow(
            self,
            self.settings_manager,
            self._on_theme_changed,
            self._on_layout_changed,
            self._open_help_tab,
        )
        self._settings_window = win
        win.connect("close-request", lambda *_: setattr(self, "_settings_window", None) or False)

    def _on_theme_changed(self, _theme: str):
        self._apply_app_theme()
        self._apply_theme_to_chrome()

    def _on_layout_changed(self):
        self._apply_language()
        self._apply_orientation()
        self._apply_auto_hide_state()
        self._update_status_dots()
        self._refresh_ram_usage()

    def _show_onboarding(self) -> bool:
        lang = self._lang()
        self.onboarding = Gtk.Box()
        self.onboarding.add_css_class("onboarding-overlay")
        self.onboarding.set_halign(Gtk.Align.FILL)
        self.onboarding.set_valign(Gtk.Align.FILL)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_hexpand(True)
        content.set_vexpand(True)
        content.set_halign(Gtk.Align.CENTER)
        content.set_valign(Gtk.Align.CENTER)
        content.set_margin_start(32)
        content.set_margin_end(32)

        lbl = Gtk.Label(label=t("onboarding_text", lang))
        lbl.add_css_class("onboarding-text")
        lbl.set_wrap(True)
        lbl.set_justify(Gtk.Justification.CENTER)

        btn = Gtk.Button(label=t("onboarding_btn", lang))
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._dismiss_onboarding)

        content.append(lbl)
        content.append(btn)
        self.onboarding.append(content)

        self.main_overlay.add_overlay(self.onboarding)
        return False

    def _dismiss_onboarding(self, _btn):
        self.settings_manager.set("first_run", False)
        if self.onboarding:
            self.main_overlay.remove_overlay(self.onboarding)
            self.onboarding = None

    def _on_close(self, _window):
        if self._ram_timer_id:
            GLib.source_remove(self._ram_timer_id)
            self._ram_timer_id = None

        w, h = self.get_width(), self.get_height()
        if w > 200 and h > 200:
            self.settings_manager.set("window_width", w)
            self.settings_manager.set("window_height", h)

        for pid, tab in self.tabs.items():
            if pid.startswith("__"):
                tab.close()
                continue
            url = tab.get_current_url()
            if url:
                for p in self.profile_manager.profiles:
                    if p["id"] == pid:
                        p["last_url"] = url
                        break
            tab.close()
        self.profile_manager.save()
        return False