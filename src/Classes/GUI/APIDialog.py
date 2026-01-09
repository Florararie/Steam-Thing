import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from Classes.Utils.SteamLib import is_valid_steam_id, is_valid_api_key



class SteamApiDialog(QDialog):
    def __init__(self, parent=None, centered=False, first=False):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Enter Steam API Key and Profile ID")
        self.setGeometry(300, 300, 400, 180)  # Adjust size as needed
        self.first = first

        layout = QVBoxLayout(self)

        # Label for API Key
        details_label = QLabel("If details are not provided, will only be able to show locally installed games", self)
        api_key_label = QLabel("Enter your Steam API Key - EX: 4F5E6D7C8B9A0F1E2D3C4B5A6E7F8A9B", self)
        layout.addWidget(details_label)
        layout.addWidget(api_key_label)

        # Line Edit for Steam API Key
        self.api_key_edit = QLineEdit(self)
        self.api_key_edit.setPlaceholderText("Steam API Key")
        layout.addWidget(self.api_key_edit)

        # Label for Profile ID
        profile_id_label = QLabel("Enter your Steam Profile ID (64) - EX: 76561198833313974", self)
        layout.addWidget(profile_id_label)

        # Line Edit for Steam Profile ID
        self.profile_id_edit = QLineEdit(self)
        self.profile_id_edit.setPlaceholderText("Steam Profile ID (64)")
        layout.addWidget(self.profile_id_edit)

        # Submit button
        submit_button = QPushButton("Submit", self)
        submit_button.clicked.connect(self.submit_credentials)
        layout.addWidget(submit_button)

        self.setLayout(layout)

        # Center the window
        if parent:
            self.center_window(parent)
            self.api_key_edit.setText(self.parent().config.get_value(1, "api_key"))
            steam_id = self.parent().config.get_value(1, "profile_id")
            self.profile_id_edit.setText(str(steam_id) if steam_id is not None else "")

        if centered:
            self.center_dialog(self)


    def submit_credentials(self):
        """Handle the submit action to save the API Key and Profile ID."""
        api_key = self.api_key_edit.text()
        profile_id = self.profile_id_edit.text()
        self.reload = True

        self.parent().config.add_entry(1, 'api_key', api_key, "str")
        self.parent().config.add_entry(1, 'profile_id', profile_id, "str")

        if is_valid_api_key(api_key) and is_valid_steam_id(profile_id):  # Steam Profile ID is 17 characters long
            self.parent().api_key = api_key  # Pass the API key to the parent window
            self.parent().profile_id = profile_id  # Pass the Profile ID to the parent window
            self.accept()  # Close the dialog
        else:
            QMessageBox.warning(self, "Input Error", "Invalid inputs provided, API features will not be utilized.")
            #self.parent().config.remove_entry(1, 'api_key')
            #self.parent().config.remove_entry(1, 'profile_id')
            self.reject()


    def closeEvent(self, event):
        """Handle the close event to ensure input is provided."""
        self.reload = False
        if self.first:
            self.reload = True
            QMessageBox.warning(self, "Input Error", "Invalid inputs provided, API features will not be utilized.")
        event.accept()


    def center_window(self, parent):
        """Center the dialog window relative to its parent."""
        parent_rect = parent.geometry()
        x = parent_rect.left() + (parent_rect.width() - self.width()) // 2
        y = parent_rect.top() + (parent_rect.height() - self.height()) // 2
        self.move(x, y)


    def center_dialog(self, dialog: QDialog):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - dialog.width()) // 2
        y = (screen_geometry.height() - dialog.height()) // 2
        dialog.move(x, y)