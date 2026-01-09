import os
import requests
from io import BytesIO
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QFrame, QDialog
from Classes.Functions import launch_game



class GameInfoWindow(QDialog):
    def __init__(self, game_name, app_id, last_played, last_updated, size_on_disk, installed, playtime, description, steam_path, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(f"{game_name} - [{app_id}]")
        layout = QVBoxLayout(self)

        self.cache_dir = f"{parent.cache_dir}/Headers"
        if not os.path.exists(self.cache_dir):  # Create cache directory if it doesn't exist
            os.makedirs(self.cache_dir)

        # Header image
        header_image_url = f"https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/header.jpg"
        image_label = QLabel()

        # Load header image (with caching)
        if pixmap := self.fetch_header_image(header_image_url, app_id):
            image_label.setPixmap(pixmap)
            image_label.setScaledContents(True)
            image_label.setFixedSize(460, 215)
        layout.addWidget(image_label)

        # Format game details
        size_label = QLabel(f"Size on Disk: {self.format_size(int(size_on_disk))}")
        layout.addWidget(size_label)

        playtime_label = QLabel(f"Playtime: {self.format_playtime(int(playtime))}")
        layout.addWidget(playtime_label)

        last_played_label = QLabel(f"Last Played: {self.format_date(int(last_played))}")
        layout.addWidget(last_played_label)

        last_updated_label = QLabel(f"Last Updated: {self.format_date(int(last_updated))}")
        layout.addWidget(last_updated_label)

        # Separator (horizontal line)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Description
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        # Launch button
        launch_button = QPushButton("Launch")
        launch_button.setEnabled(installed)
        launch_button.clicked.connect(lambda: [launch_game(steam_path, app_id, "launch", self.parent()), self.close()])
        layout.addWidget(launch_button)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)


    def fetch_header_image(self, url, app_id):
        cached_image_path = os.path.join(self.cache_dir, f"header_{app_id}.jpg")
        
        # Check if image is cached
        if os.path.exists(cached_image_path):
            pixmap = QPixmap(cached_image_path)  # Load from cache
            return pixmap

        # If not cached, download and save the image
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(BytesIO(response.content).read())  # Convert image data to QPixmap
                pixmap = pixmap.scaled(460, 215, Qt.KeepAspectRatio)  # Resize to fit the label

                # Cache the image locally
                pixmap.save(cached_image_path)

                return pixmap
        except Exception as e:
            print(f"Failed to fetch header image: {e}")
        
        return None


    def format_date(self, timestamp, mode='12'):
        if timestamp == 0:
            return "NaN"

        # Convert UNIX timestamp to local time
        dt = datetime.fromtimestamp(timestamp)

        if mode == '12':
            # Return 12-hour time with AM/PM
            return dt.strftime('%m/%d/%Y - %I:%M %p')  # %I = 12-hour format, %p = AM/PM
        else:
            # Return 24-hour time (default)
            return dt.strftime('%m/%d/%Y - %H:%M')  # %H = 24-hour format


    def format_size(self, size_in_bytes):
        if size_in_bytes == 0:
            return "Not installed"

        # Convert file size from bytes to a human-readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} PB"


    def format_playtime(self, minutes):
        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes / 60
            return f"{round(hours, 1)} hours"