import sys
from PyQt5.QtWidgets import QApplication
from Classes.Main import MainWindow
#nuitka --standalone --onefile --enable-plugin=pyqt5 --include-package=win32api --windows-console-mode=disable run.py



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    try:
        sys.exit(app.exec_())
    finally:
        print("Exited")