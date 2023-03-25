import sys
from typing import Tuple

from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QPushButton, QListWidgetItem, QWidget
from filesocket import show_all_pc, ManagingClient, ServerError, PCEntity


class ChoosePCDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        uic.loadUi("res/ui/choose_pc_dialog.ui", self)
        self.device_id = None
        self.load_table()

    @staticmethod
    def _check_online(pc: PCEntity) -> bool:
        temp_client = ManagingClient(pc.id)
        temp_client.run(False)
        try:
            return temp_client.check_online()
        except ServerError:
            return False

    def load_table(self) -> None:
        try:
            all_pc = show_all_pc()
        except ServerError:
            sys.exit()
        availability = tuple(map(self._check_online, all_pc))
        all_pc = list(zip(all_pc, availability))
        all_pc.sort(key=lambda pc: pc[1], reverse=True)
        for pc in all_pc:
            button = QPushButton()
            button.setObjectName(f"button_{pc[0].id}")
            button.setText(pc[0].name)
            button.setEnabled(pc[1])
            item = QListWidgetItem(self.table)
            self.table.addItem(item)
            self.table.setItemWidget(item, button)
            button.clicked.connect(self.open_connection)

    def open_connection(self):
        self.device_id = int(self.sender().objectName().removeprefix("button_"))
        self.accept()

    def execute(self) -> Tuple[int, str] | Tuple[int, None] | None:
        state = self.exec()
        if state == 0:
            return None
        secure_token = None if self.secure_token.text().strip() == '' else self.secure_token.text().strip()
        return self.device_id, secure_token
