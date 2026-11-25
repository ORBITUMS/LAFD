import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk

from config import APP_ID
from styles import APP_CSS
from window import MainWindow


class AccountBrowserApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        display = Gdk.Display.get_default()
        if display:
            provider = Gtk.CssProvider()
            # ❌ БЫЛО: provider.load_from_data(APP_CSS.encode("utf-8"))
            # ✅ СТАЛО:
            provider.load_from_string(APP_CSS)
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def do_activate(self):
        if not self.window:
            self.window = MainWindow(self)
        self.window.present()
