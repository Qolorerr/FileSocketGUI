from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QWidget
from filesocket import sign_up, ServerError


class SignupDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        uic.loadUi("res/ui/signup_dialog.ui", self)
        self.error_message.hide()
        self.signup.clicked.connect(self.signup_processing)
        self.signin.clicked.connect(self.signin_processing)

    def signup_processing(self) -> None:
        login = self.login.text()
        email = self.email.text()
        password = self.password.text()
        if login.strip() == '' or password.strip() == '' or email.strip() == '':
            return
        try:
            sign_up(login, email, password)
        except ServerError as e:
            self.error_message.show()
            return
        self.accept()

    def signin_processing(self) -> None:
        self.accept()
