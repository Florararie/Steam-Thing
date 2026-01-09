import os
import requests
from PyQt5.QtGui import QPixmap, QColor, QPainter, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QThreadPool, QRunnable



class ImageLoaderWorker(QRunnable):
    """Worker to fetch game images in parallel."""
    def __init__(self, app_id, cache_dir, session, callback):
        super().__init__()
        self.app_id = app_id
        self.cache_dir = cache_dir
        self.session = session
        self.callback = callback  # Function to send back the result


    def run(self):
        """Download and cache game images."""
        cached_image_path = os.path.join(self.cache_dir, f"game_{self.app_id}.jpg")
        
        # Load from cache if exists
        if os.path.exists(cached_image_path):
            pixmap = QPixmap(cached_image_path)
        else:
            img_url = f"https://steamcdn-a.akamaihd.net/steam/apps/{self.app_id}/library_600x900_2x.jpg"
            try:
                response = self.session.get(img_url, timeout=3)  # Fast timeout
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(80, 120, Qt.KeepAspectRatio)
                        pixmap.save(cached_image_path)  # Save asynchronously
                    else:
                        pixmap = self.create_placeholder_image()
                else:
                    pixmap = self.create_placeholder_image()
            except Exception as e:
                print(f"Error fetching image for {self.app_id}: {e}")
                pixmap = self.create_placeholder_image()

        self.callback(self.app_id, pixmap)


    def create_placeholder_image(self):
        """Creates a simple placeholder image with text."""
        width, height = 80, 120
        placeholder = QPixmap(width, height)
        placeholder.fill(QColor(200, 200, 200))  # Light gray background

        # Draw "No Image" text on the placeholder
        painter = QPainter(placeholder)
        painter.setPen(QColor(0, 0, 0))  # Black text
        painter.setFont(QFont('Arial', 8))
        painter.drawText(placeholder.rect(), Qt.AlignCenter, "No Image")
        painter.end()

        return placeholder



class GameLoaderThread(QThread):
    game_loaded = pyqtSignal(tuple, QPixmap)  # Signal to update UI with each loaded game and image
    finished_loading = pyqtSignal()  # Signal when all games are loaded
    progress_update = pyqtSignal(int)  # Signal to update progress bar


    def __init__(self, game_library, exclusion_file, cache_dir):
        super().__init__()
        self.game_library = game_library
        self.exclusion_file = exclusion_file
        self.cache_dir = os.path.join(cache_dir, "Games")
        self.thread_pool = QThreadPool.globalInstance()  # Use a thread pool for parallelism
        self.session = requests.Session()  # Keep a session for faster requests
        self.completed_games = 0  # Track how many have finished loading
        self.total_games = 0  # Will be set later
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)


    def run(self):
        """Loads games and images in a separate thread, checking the cache."""
        games = self.game_library.get_all_games(self.exclusion_file)
        self.total_games = len(games)

        if self.total_games == 0:
            self.finished_loading.emit()
            return


        def image_callback(app_id, pixmap):
            """Receives the pixmap and emits it for UI updates."""
            for game in games:
                if game[1] == app_id:  # Match by app_id
                    self.game_loaded.emit(game, pixmap)
                    break
            
            # Track completed games and update progress
            self.completed_games += 1
            progress = int((self.completed_games / self.total_games) * 100)
            self.progress_update.emit(progress)

            # If all games are processed, signal completion
            if self.completed_games >= self.total_games:
                self.finished_loading.emit()

        for game in games:
            _, app_id, _, _, _, _, _ = game

            # Load image in parallel
            worker = ImageLoaderWorker(app_id, self.cache_dir, self.session, image_callback)
            self.thread_pool.start(worker)

        # Ensure the thread pool doesn't exit until all images are processed
        self.thread_pool.waitForDone()
