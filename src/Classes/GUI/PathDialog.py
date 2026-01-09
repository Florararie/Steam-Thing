import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox



class SteamPathDialog(QDialog):
    def __init__(self, parent=None, centered=False, first=False):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Select Steam Path")
        self.setGeometry(300, 300, 400, 120)  # Adjust size as needed
        self.accepted = False
        self.first = first

        layout = QVBoxLayout(self)

        # Label explaining the purpose of the input field
        label = QLabel("Steam's path is not found inside of the configuration.", self)
        layout.addWidget(label)

        # Create a horizontal layout for the line edit and browse button
        h_layout = QHBoxLayout()

        # Line Edit for the path
        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("Steam Path")

        # Add the line edit to the horizontal layout
        h_layout.addWidget(self.line_edit)

        # Button to browse for the executable
        browse_button = QPushButton("Browse", self)
        browse_button.clicked.connect(self.browse_for_steam_path)
        
        # Add the browse button to the horizontal layout
        h_layout.addWidget(browse_button)

        # Add the horizontal layout to the main layout
        layout.addLayout(h_layout)

        # Determine default Steam path based on OS
        if sys.platform.startswith("win"):
            default_path = r"C:/Program Files (x86)/Steam"
        else:
            default_path = os.path.expanduser("~/.local/share/Steam")

        # Autofill the path if it exists
        if os.path.exists(default_path):
            self.line_edit.setText(default_path)

        # Submit button
        submit_button = QPushButton("Submit", self)
        submit_button.clicked.connect(self.submit_steam_path)
        layout.addWidget(submit_button)

        self.setLayout(layout)

        # Center the window
        if parent:
            self.center_window(parent)

        if centered:
            self.center_dialog(self)


    def browse_for_steam_path(self):
        """Open file dialog to browse and select the Steam executable."""
        initial_dir = r"C:\\Program Files (x86)\Steam" if sys.platform.startswith("win") else os.path.expanduser("~/.local/share/Steam")

        path = QFileDialog.getExistingDirectory(self, "Select Steam Path", initial_dir)
        if path:
            self.line_edit.setText(path)  # Update the line edit with the selected path


    def detect_executable(self, path):
        file_name = 'steam.exe' if sys.platform.startswith('win') else 'steam.sh'
        full_path = os.path.join(path, file_name)
        return os.path.isfile(full_path)


    def submit_steam_path(self):
        """Handle the submit action to save the Steam executable path."""
        self.reload = True
        path = self.line_edit.text()
        
        if path and os.path.exists(path) and self.detect_executable(path):
            self.accepted = True
            self.parent().steam_path = path  # Pass the path to the parent window
            self.parent().config.add_entry(1, 'steam_path', path, "str")  # Save the path to config.json
            self.accept()  # Close the dialog
        else:
            QMessageBox.warning(self, "Invalid Path", "Please provide a valid path for Steam's install.")


    def closeEvent(self, event):
        """Handle the close event to show a warning if the path is not set."""
        self.reload = False
        if self.first:
            self.reload = True
            if not self.line_edit.text() or not os.path.exists(self.line_edit.text()) or not self.accepted:
                QMessageBox.warning(self, "Path Required", "The Steam path is required")
                sys.exit()
        event.accept()  # Accept the close event if the path is set


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