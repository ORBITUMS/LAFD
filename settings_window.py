import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib

from config import DEFAULT_URL
from i18n import t


class SettingsWindow(Gtk.Window):
    def __init__(self, parent, settings_manager, on_theme_changed, on_layout_changed, on_help):
        super().__init__(
            modal=True,
            transient_for=parent,
            default_width=480,
            default_height=-1,
            resizable=False,
            decorated=False,
        )
        self.set_application(parent.get_application())
        self.add_css_class("settings-window")
        self.settings_manager = settings_manager
        self.on_theme_changed = on_theme_changed
        self.on_layout_changed = on_layout_changed
        self.on_help = on_help

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key)
        self.add_controller(key_ctrl)

        self.dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.dialog_box.add_css_class("glass-dialog")
        if self._is_light():
            self.dialog_box.add_css_class("light")
        self.set_child(self.dialog_box)

        handle = Gtk.WindowHandle()
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_margin_start(22)
        header.set_margin_end(18)
        header.set_margin_top(18)
        header.set_margin_bottom(6)

        self.title_lbl = Gtk.Label()
        self.title_lbl.add_css_class("settings-title")
        self.title_lbl.set_hexpand(True)
        self.title_lbl.set_halign(Gtk.Align.START)
        header.append(self.title_lbl)

        close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_btn.add_css_class("glass-close-btn")
        close_btn.set_valign(Gtk.Align.CENTER)
        close_btn.connect("clicked", lambda _: self.close())
        header.append(close_btn)
        handle.set_child(header)
        self.dialog_box.append(handle)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(8)
        content.set_margin_bottom(22)
        self.dialog_box.append(content)

        # Карточка 1: Внешний вид
        card_appearance = self._make_card()
        theme_row, self.theme_lbl = self._make_row()
        self.theme_switch = self._make_switch(
            self.settings_manager.get("theme", "dark") == "dark",
            self._on_theme_toggled,
        )
        theme_row.append(self.theme_switch)
        card_appearance.append(theme_row)
        card_appearance.append(self._make_sep())

        lang_row, self.lang_lbl = self._make_row()
        self.lang_drop = Gtk.DropDown.new_from_strings(["English", "Русский", "XD"])
        cur_lang = self.settings_manager.get("language", "en")
        self.lang_drop.set_selected(0 if cur_lang == "en" else (1 if cur_lang == "ru" else 2))
        self.lang_drop.connect("notify::selected", self._on_lang_changed)
        lang_row.append(self.lang_drop)
        card_appearance.append(lang_row)
        card_appearance.append(self._make_sep())

        ori_row, self.ori_lbl = self._make_row()
        self.ori_model = Gtk.StringList()
        self.ori_drop = Gtk.DropDown(model=self.ori_model)
        self.ori_drop.connect("notify::selected", self._on_ori_changed)
        ori_row.append(self.ori_drop)
        card_appearance.append(ori_row)
        card_appearance.append(self._make_sep())

        dots_row, self.dots_lbl = self._make_row()
        self.dots_switch = self._make_switch(
            self.settings_manager.get("status_dots", True),
            lambda sw, _: self._set_and_update("status_dots", sw.get_active()),
        )
        dots_row.append(self.dots_switch)
        card_appearance.append(dots_row)
        card_appearance.append(self._make_sep())

        hide_row, self.hide_lbl = self._make_row()
        self.hide_switch = self._make_switch(
            self.settings_manager.get("auto_hide_footer", False),
            lambda sw, _: self._set_and_update("auto_hide_footer", sw.get_active()),
        )
        hide_row.append(self.hide_switch)
        card_appearance.append(hide_row)
        content.append(card_appearance)

        # Карточка 2: Функции
        card_features = self._make_card()
        sug_row, self.sug_lbl = self._make_row()
        self.sug_switch = self._make_switch(
            self.settings_manager.get("suggestions", True),
            lambda sw, _: self._set_and_update("suggestions", sw.get_active()),
        )
        sug_row.append(self.sug_switch)
        card_features.append(sug_row)
        card_features.append(self._make_sep())

        dnd_row, self.dnd_lbl = self._make_row()
        self.dnd_switch = self._make_switch(
            self.settings_manager.get("drag_and_drop", False),
            lambda sw, _: self._set_and_update("drag_and_drop", sw.get_active()),
        )
        dnd_row.append(self.dnd_switch)
        card_features.append(dnd_row)
        card_features.append(self._make_sep())

        ram_row, self.ram_lbl = self._make_row()
        self.ram_switch = self._make_switch(
            self.settings_manager.get("show_ram", True),
            lambda sw, _: self._set_and_update("show_ram", sw.get_active()),
        )
        ram_row.append(self.ram_switch)
        card_features.append(ram_row)
        card_features.append(self._make_sep())

        proxy_row, self.proxy_lbl = self._make_row()
        self.proxy_switch = self._make_switch(
            self.settings_manager.get("proxy_enabled", True),
            lambda sw, _: self._set_and_update("proxy_enabled", sw.get_active()),
        )
        proxy_row.append(self.proxy_switch)
        card_features.append(proxy_row)
        card_features.append(self._make_sep())

        url_row, self.url_lbl = self._make_row()
        self.url_entry = Gtk.Entry()
        self.url_entry.add_css_class("glass-entry")
        self.url_entry.set_width_chars(22)
        self.url_entry.set_text(self.settings_manager.get("default_url", DEFAULT_URL))
        self.url_entry.connect("activate", lambda _: self._save_default_url())
        url_row.append(self.url_entry)
        card_features.append(url_row)
        content.append(card_features)

        # Карточка 3: Документация
        card_help = self._make_card()
        help_row, self.help_lbl = self._make_row()
        self.help_btn = Gtk.Button()
        self.help_btn.add_css_class("premium-btn")
        self.help_btn.connect("clicked", self._on_help_clicked)
        help_row.append(self.help_btn)
        card_help.append(help_row)
        content.append(card_help)

        self.connect("close-request", self._on_close_request)
        self._apply_language()
        self.present()

    def _make_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.add_css_class("settings-card")
        return card

    def _make_row(self):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.set_margin_top(7)
        row.set_margin_bottom(7)
        lbl = Gtk.Label()
        lbl.add_css_class("settings-label")
        lbl.set_hexpand(True)
        lbl.set_halign(Gtk.Align.START)
        row.append(lbl)
        return row, lbl

    def _make_switch(self, active: bool, callback):
        sw = Gtk.Switch()
        sw.add_css_class("premium-switch")
        sw.set_valign(Gtk.Align.CENTER)
        sw.set_active(active)
        sw.connect("notify::active", callback)
        return sw

    def _make_sep(self):
        sep = Gtk.Separator()
        sep.add_css_class("settings-sep")
        return sep

    def _is_light(self):
        return self.settings_manager.get("theme", "dark") == "light"

    def _set_and_update(self, key: str, value):
        self.settings_manager.set(key, value)
        self.on_layout_changed()

    def _save_default_url(self):
        raw = self.url_entry.get_text().strip()
        if not raw:
            url = DEFAULT_URL
        elif raw.startswith(("http://", "https://", "file://")):
            url = raw
        elif raw.startswith(("localhost", "127.0.0.1")):
            url = f"http://{raw}"
        else:
            url = f"https://{raw}"
        self.settings_manager.set("default_url", url)
        if self.url_entry.get_text() != url:
            self.url_entry.set_text(url)

    def _on_close_request(self, _win):
        self._save_default_url()
        return False

    def _apply_language(self):
        lang = self.settings_manager.get("language", "en")
        self.title_lbl.set_text(t("settings_title", lang))
        self.theme_lbl.set_text(t("dark_theme", lang))
        self.lang_lbl.set_text(t("language_label", lang))
        self.ori_lbl.set_text(t("orientation_label", lang))
        self.dots_lbl.set_text(t("status_dots_label", lang))
        self.hide_lbl.set_text(t("auto_hide_label", lang))
        self.sug_lbl.set_text(t("suggestions_label", lang))
        self.dnd_lbl.set_text(t("drag_drop_label", lang))
        self.ram_lbl.set_text(t("show_ram_label", lang))
        self.proxy_lbl.set_text(t("proxy_enabled_label", lang))
        self.url_lbl.set_text(t("default_url_label", lang))
        self.url_entry.set_placeholder_text(t("default_url_placeholder", lang))
        self.help_lbl.set_text(t("documentation_label", lang))
        self.help_btn.set_label(t("open_help_btn", lang))

        cur_ori = 0 if self.settings_manager.get("orientation", "horizontal") == "horizontal" else 1
        self.ori_drop.handler_block_by_func(self._on_ori_changed)
        self.ori_model.splice(0, self.ori_model.get_n_items(), [
            t("ori_horizontal", lang),
            t("ori_vertical", lang),
        ])
        self.ori_drop.set_selected(cur_ori)
        self.ori_drop.handler_unblock_by_func(self._on_ori_changed)

    def _on_key(self, _c, keyval, _kc, _st):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _on_theme_toggled(self, switch, _param):
        theme = "dark" if switch.get_active() else "light"
        self.settings_manager.set("theme", theme)
        self.on_theme_changed(theme)
        if theme == "light":
            self.dialog_box.add_css_class("light")
        else:
            self.dialog_box.remove_css_class("light")

    def _on_lang_changed(self, drop, _param):
        idx = drop.get_selected()
        lang = "en" if idx == 0 else ("ru" if idx == 1 else "xd")
        self.settings_manager.set("language", lang)
        self._apply_language()
        self.on_layout_changed()

    def _on_ori_changed(self, drop, _param):
        ori = "horizontal" if drop.get_selected() == 0 else "vertical"
        self.settings_manager.set("orientation", ori)
        self.on_layout_changed()

    def _on_help_clicked(self, _btn):
        self.close()
        GLib.idle_add(lambda: self._trigger_help() or False)

    def _trigger_help(self):
        self.on_help()
        return False