import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from Classes.Main import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app_root = Path(__file__).resolve().parent
    window = MainWindow(app_root)
    window.show()

    try:
        sys.exit(app.exec_())
    finally:
        print("Exited")