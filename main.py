import sys
import darkdetect
from typing import Tuple
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication
from qt_material import apply_stylesheet
from filesocket import CONFIG_FILE, LOGGER_CONFIG, ManagingClient, ServerError
from filesocket.storekeeper import Storekeeper

from src.choose_pc_dialog import ChoosePCDialog
from src.file_system_widget import FileSystemWidget
from src.signin_dialog import SigninDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.signin()

        pc_id, device_secure_token = self.choose_pc()
        device_secure_token = self.get_device_secure_token(pc_id, device_secure_token)
        self.client = ManagingClient(pc_id, device_secure_token)
        try:
            self.client.run(False)
        except ServerError:
            sys.exit()

        uic.loadUi("res/ui/main_window.ui", self)
        self.setup_tabs()
        self.show()

        # TODO: UI of console tab
        # TODO: UI of scripts tab

        # TODO: Realisation of tabs backend

    # Sign in and sign up
    @staticmethod
    def signin() -> None:
        store_keeper = Storekeeper(LOGGER_CONFIG, CONFIG_FILE)
        state = 1
        while not store_keeper.get_token() and state:
            window = SigninDialog()
            state = window.exec()
        if state == 0:
            sys.exit()

    # Choose PC to connect
    @staticmethod
    def choose_pc() -> Tuple[int, str] | Tuple[int, None]:
        result = ChoosePCDialog().execute()
        if result is None:
            sys.exit()
        return result

    # Get secure token from storekeeper
    def get_device_secure_token(self, pc_id: int, secure_token: str | None) -> str | None:
        store_keeper = Storekeeper(LOGGER_CONFIG, CONFIG_FILE)
        try:
            secure_tokens = store_keeper.get_value("secure_token")
        except KeyError:
            secure_tokens = dict()
            store_keeper.add_value("secure_token", secure_tokens)
        if secure_token is not None:
            self.set_device_secure_token(pc_id, secure_token)
            return secure_token
        return secure_tokens[str(pc_id)] if str(pc_id) in secure_tokens else None

    # Add new secure token to storekeeper
    @staticmethod
    def set_device_secure_token(pc_id: int, secure_token: str) -> None:
        store_keeper = Storekeeper(LOGGER_CONFIG, CONFIG_FILE)
        secure_tokens = store_keeper.get_value("secure_token")
        secure_tokens[str(pc_id)] = secure_token
        store_keeper.add_value("secure_token", secure_tokens)

    def setup_tabs(self) -> None:
        self.tab_1 = FileSystemWidget(self.client)
        self.tabWidget.addTab(self.tab_1, "File System")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    if darkdetect.isLight():
        apply_stylesheet(app, theme="light_red_500.xml")
    else:
        apply_stylesheet(app, theme="dark_lightgreen.xml")

    window = MainWindow()
    sys.exit(app.exec())
