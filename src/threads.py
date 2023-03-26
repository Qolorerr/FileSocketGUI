from pathlib import Path

from PyQt6.QtCore import QObject
from filesocket import ManagingClient

from src.task_thread import TaskThread


class DownloadThread(TaskThread):
    def __init__(self, parent: QObject, client: ManagingClient, path: Path, destination: Path | None = Path('')):
        super().__init__(parent)
        self.client = client
        self.path = path
        self.destination = destination

    def execute(self) -> None:
        self.client.get_file(self.path, self.destination)
        self.task_complete.emit(self.id)


class UploadThread(TaskThread):
    def __init__(self, parent: QObject, client: ManagingClient, path: Path, destination: Path = Path('')):
        super().__init__(parent)
        self.client = client
        self.path = path
        self.destination = destination

    def execute(self) -> None:
        self.client.send_file(self.path, self.destination)
        self.task_complete.emit(self.id)


class CMDThread(TaskThread):
    def __init__(self, parent: QObject, client: ManagingClient, command: str):
        super().__init__(parent)
        self.client = client
        self.command = command

    def execute(self) -> None:
        self.client.cmd_command(self.command)
        self.task_complete.emit(self.id)
