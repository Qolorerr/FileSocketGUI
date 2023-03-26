from random import randint

from PyQt6.QtCore import QObject, pyqtSignal


class TaskThread(QObject):
    task_complete = pyqtSignal(int)

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self.id = randint(1, 2 ** 31)

    def execute(self):
        pass
