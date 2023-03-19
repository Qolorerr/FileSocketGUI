from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
from filesocket import ManagingClient, ServerError


class ConsoleWidget(QWidget):
    def __init__(self, client: ManagingClient):
        super().__init__()
        uic.loadUi("res/ui/console_widget.ui", self)

        self.client = client

        self.send.clicked.connect(self.send_command_processing)

    def send_command_processing(self):
        try:
            result = self.client.cmd_command(self.textEdit.toPlainText())['out']
        except ServerError:
            return
        self.textBrowser.setText(result)
