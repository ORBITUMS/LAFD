import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from i18n import t

ASCII_ART = r"""
             ;::::; 
           ;::::; :; 
         ;:::::'   :; 
        ;:::::;     ;. 
       ,:::::'       ;           OOO\ 
       ::::::;       ;          OOOOO\ 
       ;:::::;       ;         OOOOOOOO 
      ,;::::::;     ;'         / OOOOOOO 
    ;:::::::::`. ,,,;.        /  / DOOOOOO 
  .';:::::::::::::::::;,     /  /     DOOOO 
,::::::;::::::;;;;::::;,   /  /        DOO 
;`::::::`'::::::;;;::::: ,#/  /          DOOO 
:`:::::::`;::::::;;::: ;::#  /            DOOO 
::`:::::::`;:::::::: ;::::# /              DOO 
`:`:::::::`;:::::: ;::::::#/               DOO 
:::`:::::::`;; ;:::::::::##                OO 
::::`:::::::`;::::::::;:::#                OO 
`:::::`::::::::::::;'`:;::#                O 
  `:::::`::::::::;' /  / `:# 
   ::::::`:::::;'  /  /   `#
""".strip("\n")


class WelcomePage(Gtk.Box):
    def __init__(self, settings_manager):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("welcome-container")
        self.settings_manager = settings_manager

        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        center.set_valign(Gtk.Align.CENTER)
        center.set_halign(Gtk.Align.CENTER)
        center.set_vexpand(True)

        title = Gtk.Label(label="Welcome")
        title.add_css_class("welcome-title")
        center.append(title)

        self.subtitle = Gtk.Label()
        self.subtitle.add_css_class("welcome-subtitle")
        self.subtitle.set_justify(Gtk.Justification.CENTER)
        center.append(self.subtitle)

        self.append(center)

        art = Gtk.Label()
        art.set_use_markup(False)
        art.set_text(ASCII_ART)
        art.add_css_class("ascii-art")
        art.set_halign(Gtk.Align.CENTER)
        art.set_valign(Gtk.Align.END)
        art.set_margin_bottom(100)
        self.append(art)

        self.update_language()

    def update_language(self):
        lang = self.settings_manager.get("language", "en")
        self.subtitle.set_text(t("welcome_subtitle", lang))
