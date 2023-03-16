import sys

from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication
from qt_material import apply_stylesheet


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("res/ui/main_window.ui", self)

        # TODO: UI of console tab
        # TODO: UI of scripts tab

        # TODO: Realisation of tabs backend


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme="light_red_500.xml")

    # TODO: Token check
    # TODO: If not, signin/signup form
    # TODO: Show list of PCs

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
