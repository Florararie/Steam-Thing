import os
import sys
import subprocess
import webbrowser

from PyQt5.QtWidgets import QMessageBox



def launch_game(steam_path, app_id, mode):
    """Launch the Steam game using the Steam protocol."""
    file_name = 'steam.exe' if sys.platform.startswith('win') else 'steam.sh'

    if mode == "launch":
        command = f"steam://run/{app_id}"
    elif mode == "store":
        command = f"steam://store/{app_id}"

    try:
        # This opens the game in the Steam client using the app_id
        subprocess.run([os.path.join(steam_path, file_name), command])
    except Exception as e:
        QMessageBox.warning(parent, "Launch Failed", f"Failed to launch the game: {e}")



def open_link(option, app_id):
    url_map = {
        1: f"https://store.steampowered.com/app/{app_id}",
        2: f"https://steamdb.info/app/{app_id}",
    }
        
    # Get the URL for the option
    url = url_map.get(option)
    if url:
        webbrowser.open(url)