## Installation and Launch

### Option 1: Prebuilt Release (Ubuntu 24.04+ / Debian)

1. Install required system libraries:
   ```bash
   sudo apt install gir1.2-gtk-4.0 gir1.2-webkit-6.0 glib-networking
   ```
2. Download the latest -AccountBrowser-linux.tar.gz- from the **Releases** page and extract it:
   ```bash
   tar -xzf AccountBrowser-linux.tar.gz
   cd AccountBrowser
   ```
3. Run the browser directly:
   ```bash
   ./AccountBrowser
   ```
   Or add it to your application menu:
   ```bash
   ./install.sh
   ```

### Option 2: Run from Source

1. Install system dependencies (Ubuntu / Debian):
   ```bash
   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-webkit-6.0 glib-networking
   ```
2. Clone the repository and launch:
   ```bash
   git clone <repository-url>
   cd <project-folder>
   python3 main.py
   ```
