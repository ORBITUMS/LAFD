#!/usr/bin/env python3
import os
import sys

if getattr(sys, "frozen", False):
    for gio_dir in (
        "/usr/lib/x86_64-linux-gnu/gio/modules",
        "/usr/lib/aarch64-linux-gnu/gio/modules",
        "/usr/lib64/gio/modules",
        "/usr/lib/gio/modules",
    ):
        if os.path.exists(os.path.join(gio_dir, "libgiognutls.so")):
            os.environ["GIO_MODULE_DIR"] = gio_dir
            break

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")

from application import AccountBrowserApp

if __name__ == "__main__":
    AccountBrowserApp().run()