# Account Browser

A minimalist browser organizer for Linux built with **GTK 4** and **WebKitGTK 6.0**, featuring completely isolated sessions.

Each session stores its own cookies, cache, and site data in a separate folder — allowing you to stay logged into multiple Google accounts, AI tools, or work profiles simultaneously without constantly signing out and back in.

## Features

- **Isolated Sessions** — separate cookie and cache storage for each profile.
- **Per-Session Proxies** — individual `http://` and `socks5://` proxy settings via the right-click context menu.

## Keyboard Shortcuts

| Shortcut                             | Action                      |
| :----------------------------------- | :-------------------------- |
| `Ctrl + T`                           | Create a new session        |
| `Ctrl + L`                           | Focus the address bar       |
| `Ctrl + R` / `F5`                    | Reload / stop loading page  |
| `Alt + ←` / `Alt + →`                | Back / Forward              |
| `Ctrl + 1..9`                        | Switch to session by number |
| `Ctrl + +` / `Ctrl + -` / `Ctrl + 0` | Page zoom                   |
| `Ctrl + ,`                           | Open settings               |

## Installation and Launch

### 1. System Dependencies (Ubuntu / Debian)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-webkit-6.0
git clone <repository-url>
cd <project-folder>
python3 main.py
```
