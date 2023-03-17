from PyQt6 import uic
from PyQt6.QtWidgets import QDialog
from filesocket import sign_in, ServerError

from src.signup_dialog import SignupDialog


class SigninDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("res/ui/signin_dialog.ui", self)
        self.error_message.hide()
        self.signin.clicked.connect(self.signin_processing)
        self.signup.clicked.connect(self.signup_processing)

    def signin_processing(self) -> None:
        login = self.login.text()
        password = self.password.text()
        if login.strip() == '' or password.strip() == '':
            return
        try:
            sign_in(login, password)
        except ServerError as e:
            self.error_message.show()
            return
        self.accept()

    def signup_processing(self) -> None:
        self.hide()
        window = SignupDialog()
        state = window.exec()
        if state == 0:
            self.reject()
        else:
            self.accept()
