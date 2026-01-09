import os
import sys
import json
import random
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QHBoxLayout, QLabel,
    QListWidgetItem, QMenu, QAction, QMessageBox, QFileDialog
)

from Classes.Functions import launch_game, open_link
from Classes.LoaderThread import GameLoaderThread
from Classes.Utils.SteamLib import GameLibrary
from Classes.Utils.Config import JSONConfig
from Classes.GUI.MainWindow import Ui_MainWindow
from Classes.GUI.InfoWindow import GameInfoWindow
from Classes.GUI.PathDialog import SteamPathDialog
from Classes.GUI.APIDialog import SteamApiDialog



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, root_path, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.config = JSONConfig(root_path / 'config.json')
        self.games, self.filtered_games = [], []
        self.show_installed_only = False
        self.cache_dir = root_path / "Cache"

        self.status_label = QLabel("Games Loaded: 0")
        self.statusBar.addWidget(self.status_label)

        self.steam_path, self.api_key, self.steam_id, self.exclusion_file = self.return_config_values()
        self.check_required_settings()
        self.setup_connections()


    def setup_connections(self):
        """Connects UI elements to their respective functions."""
        ui_connections = [
            (self.filter_lineEdit.textChanged, self.filter_games),
            (self.filter_comboBox.currentIndexChanged, self.sort_games),
            (self.filter_checkBox.stateChanged, self.filter_installed_games),
            (self.listWidget.itemDoubleClicked, lambda item: self.show_game_info(*item.data(1))),
            (self.random_pushButton.clicked, self.pick_random_game),
            (self.actionOpen_New_Exclusion_File.triggered, lambda: self.handle_exclusion_file("open")),
            (self.actionSave_Open_Exclusion_File.triggered, lambda: self.handle_exclusion_file("save")),
            (self.actionChoose_Random_Game.triggered, self.pick_random_game),
            (self.actionUpdate_Steam_Path.triggered, lambda: self.show_dialog_prompt(SteamPathDialog)),
            (self.actionUpdate_API_information.triggered, lambda: self.show_dialog_prompt(SteamApiDialog)),
        ]

        # Apply UI element connections
        for signal, slot in ui_connections:
            signal.connect(slot)

        # Restore last used filter setting
        last_used_filter = self.config.get_value(1, "last_used_filter") or "Alphabetical"
        self.filter_comboBox.setCurrentText(last_used_filter)
        install_filter = self.config.get_value(1, "installed_filter") or False
        self.filter_checkBox.setChecked(install_filter)

        self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.show_context_menu)


    def return_config_values(self):
        """Retrieves a configuration value."""
        one = self.config.get_value(1, "steam_path")
        two = self.config.get_value(1, "api_key")
        three = self.config.get_value(1, "profile_id")
        four = self.config.get_value(1, "exclusion_file")
        return one, two, three, four


    def check_required_settings(self):
        """Ensures all required settings are set before proceeding."""
        if not self.steam_path:
            self.show_dialog_prompt(SteamPathDialog, centered=True)

        if not self.api_key or not self.steam_id:
            self.show_dialog_prompt(SteamApiDialog, centered=True, first=True)
        else:
            self.load_games_async()

        if self.exclusion_file:
            self.load_exclusion_contents(self.exclusion_file)


    def show_dialog_prompt(self, dialog_class, centered=False, first=False):
        """Displays a dialog prompt and reloads the game list if needed."""
        dialog = dialog_class(self, centered, first)
        dialog.exec_()
        if dialog.reload:
            self.reload_game_list()


    def update_status_bar(self):
        """Updates the status bar to reflect how many games are currently loaded."""
        num_games = len(self.filtered_games) if self.filtered_games else len(self.games)
        self.status_label.setText(f"Games Loaded: {num_games}")


    def load_games_async(self):
        """Loads games asynchronously using a separate thread."""
        self.steam_path, self.api_key, self.steam_id, _ = self.return_config_values()
        self.game_library = GameLibrary(self.steam_path, self.api_key, self.steam_id)
        self.loader_thread = GameLoaderThread(self.game_library, self.exclusion_file, self.cache_dir)

        self.loader_thread.game_loaded.connect(self.add_game_to_list)
        self.loader_thread.finished_loading.connect(self.on_loading_complete)
        self.loader_thread.progress_update.connect(self.progressBar.setValue)

        self.loader_thread.start()


    def add_game_to_list(self, game, pixmap):
        """Adds a game to the list and updates the display if it matches the filter."""
        self.games.append((game, pixmap))
        if self.is_game_matching_search(game, self.filter_lineEdit.text().lower()):
            self.add_game_to_display(game, pixmap)
        self.update_status_bar()


    def add_game_to_display(self, game, pixmap):
        """Displays a game item in the UI."""
        name, installed = game[0], game[5]
        status_color = "green" if installed else "red"

        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        img_label = QLabel()

        if pixmap:
            img_label.setPixmap(pixmap)

        layout.addWidget(img_label)
        layout.addWidget(QLabel(name, styleSheet=f"color: {status_color};"))
        layout.addStretch()

        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())
        item.setData(1, game)

        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, item_widget)


    def on_loading_complete(self):
        """Handles UI updates once game loading is complete."""
        self.filter_games()
        self.sort_games()
        self.filter_checkBox.setEnabled(self.game_library.install_filter)


    def pick_random_game(self):
        """Selects and displays a random game from the filtered list."""
        if self.filtered_games:
            self.show_game_info(*random.choice(self.filtered_games)[0])


    def show_game_info(self, game_name, app_id, last_played, last_updated, size_on_disk, installed, playtime):
        """Displays the game information window."""
        description = self.game_library.get_game_description(app_id)
        info_window = GameInfoWindow(game_name, app_id, last_played, last_updated, size_on_disk, installed, playtime, description, self.steam_path, self)
        info_window.setAttribute(Qt.WA_DeleteOnClose)
        info_window.show()


    def filter_games(self):
        """Filters the game list based on the search input."""
        search_text = self.filter_lineEdit.text().lower()
        self.filtered_games = [
            (game, pixmap) for game, pixmap in self.games
            if self.is_game_matching_search(game, search_text) and (not self.show_installed_only or game[5])
        ]
        self.sort_games()
        self.update_status_bar()


    def filter_installed_games(self):
        self.show_installed_only = self.filter_checkBox.isChecked()
        self.config.add_entry(1, 'installed_filter', self.filter_checkBox.isChecked(), "bool")
        self.filter_games()


    def is_game_matching_search(self, game, search_text):
        """Checks if a game matches the search criteria."""
        return search_text in game[0].lower() or search_text in str(game[1])


    def sort_games(self):
        """Sorts games based on the selected criteria."""
        self.config.add_entry(1, 'last_used_filter', self.filter_comboBox.currentText(), "str")

        sort_key = {
            "Alphabetical": lambda x: x[0][0].lower(),  # Sort by name (case-insensitive)
            "Last Played": lambda x: x[0][2],  # Sort by last played date
            "Last Updated": lambda x: x[0][3],  # Sort by last updated date
            "Size on Disk": lambda x: x[0][4],  # Sort by size on disk
            "Playtime High to Low": lambda x: int(x[0][6]),  # Sort by playtime forever, high to low (ensure int)
            "Playtime Low to High": lambda x: int(x[0][6]),  # Sort by playtime forever, low to high (ensure int)
        }.get(self.filter_comboBox.currentText())

        if sort_key:
            # If the sorting is for 'Playtime High to Low', we want reverse (highest first)
            reverse_order = self.filter_comboBox.currentText() in ["Last Played", "Last Updated", "Size on Disk", "Playtime High to Low"]
            
            # Sorting the games based on the selected criteria
            self.filtered_games.sort(key=sort_key, reverse=reverse_order)

        self.listWidget.clear()
        for game, pixmap in self.filtered_games:
            self.add_game_to_display(game, pixmap)


    def show_context_menu(self, pos):
        item = self.listWidget.itemAt(pos)
        if not item:
            return
        
        game = item.data(1)
        game_name, app_id, _, _, _, installed, _ = game  # Extract 'installed' status

        menu = QMenu(self)

        actions = [
            ("Launch", lambda: launch_game(self.steam_path, app_id, "launch"), installed),
            (None, None, None),  # Separator
            ("Show Info", lambda: self.show_game_info(*game), True),
            ("Copy App ID", lambda: self.copy_to_clipboard(game_name, app_id), True),
            ("Add to Exclusion List", lambda: self.add_to_exclusion_list(game_name, app_id), True),
            (None, None, None),  # Separator
            ("Open Store Page", lambda: launch_game(self.steam_path, app_id, "store"), True),
            ("Open SteamDB Page", lambda: open_link(2, app_id), True),
        ]

        for action_text, callback, enabled in actions:
            if action_text is None:  # Add a separator if action_text is None
                menu.addSeparator()
            else:
                action = QAction(action_text, self)
                action.triggered.connect(callback)
                action.setEnabled(enabled)
                menu.addAction(action)

        menu.exec_(self.listWidget.viewport().mapToGlobal(pos))


    def copy_to_clipboard(self, game_name, app_id):
        """Copies the game App ID to the clipboard."""
        QApplication.clipboard().setText(str(app_id))
        QMessageBox.information(self, game_name, f"App ID {app_id} copied.")


    def reload_game_list(self):
        """Clears and reloads the game list."""
        self.listWidget.clear()
        self.games.clear()
        self.filtered_games.clear()
        self.load_games_async()


    def load_exclusion_contents(self, file_path):
        try:
            with open(file_path, 'r') as f:
                self.exclusion_plainTextEdit.setPlainText(f.read())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load exclusion file contents: {e}")


    def handle_exclusion_file(self, mode):
        """Handles opening or saving an exclusion file based on mode ('open' or 'save')."""
        
        file_dialog = QFileDialog.getOpenFileName if mode == "open" else QFileDialog.getSaveFileName
        dialog_title = "Open Exclusion File" if mode == "open" else "Save Exclusion File"
        flavor = "opened" if mode == "open" else "saved"
        
        file_path, _ = file_dialog(self, dialog_title, self.exclusion_file if mode == "save" else "", "JSON Files (*.json)")
        if not file_path:
            return  # User canceled the action
        
        try:
            if mode == "open":
                self.load_exclusion_contents(file_path)
            else:  # mode == "save"
                exclusions = json.loads(self.exclusion_plainTextEdit.toPlainText())
                with open(file_path, 'w') as f:
                    json.dump(exclusions, f, indent=4)

            self.exclusion_file = file_path
            self.config.add_entry(1, 'exclusion_file', file_path, "str")
            self.reload_game_list()
            QMessageBox.information(self, f"Exclusion File {flavor.capitalize()}", f"File {flavor}: {file_path}")

        except json.JSONDecodeError:
            QMessageBox.warning(self, "Invalid JSON", "The exclusions text is not valid JSON.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to {mode} exclusion file: {e}")


    def add_to_exclusion_list(self, game_name, game_id):
        exclusion_text = self.exclusion_plainTextEdit.toPlainText()
        try:
            exclusions = json.loads(exclusion_text)
        except json.JSONDecodeError:
            exclusions = {}
        exclusions[game_name] = str(game_id)
        self.exclusion_plainTextEdit.setPlainText(json.dumps(exclusions, indent=4))
