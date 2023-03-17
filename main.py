import sys

from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication
from qt_material import apply_stylesheet
from filesocket import CONFIG_FILE, LOGGER_CONFIG
from filesocket.storekeeper import Storekeeper

from src.signin_dialog import SigninDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("res/ui/main_window.ui", self)

        store_keeper = Storekeeper(LOGGER_CONFIG, CONFIG_FILE)

        state = 1
        while not store_keeper.get_token() and state:
            window = SigninDialog()
            state = window.exec()
        if state == 0:
            sys.exit()

        # TODO: Show list of PCs

        # self.show()

        # TODO: UI of console tab
        # TODO: UI of scripts tab

        # TODO: Realisation of tabs backend


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme="light_red_500.xml")

    window = MainWindow()
    sys.exit(app.exec())
