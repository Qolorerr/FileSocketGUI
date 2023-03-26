from threading import Thread

from PyQt6.QtWidgets import QProgressBar, QWidget, QLabel

from src.task_thread import TaskThread


class TaskbarProcessor:
    def __init__(self, parent: QWidget, progress_bar: QProgressBar, text: QLabel):
        self.parent = parent
        self.logger = parent.logger
        self.bar = progress_bar
        self.text = text
        self.threads = set()
        self.threads_count = 0
        self.load_bar()

    def load_bar(self) -> None:
        if self.threads_count == 0 or len(self.threads) == 0:
            self.threads_count = 0
            self.bar.hide()
            self.text.setText("")
            return
        self.bar.setValue(int(100 * (self.threads_count - len(self.threads)) / self.threads_count))
        self.text.setText(f"{self.threads_count - len(self.threads)}/{self.threads_count}")
        self.bar.show()

    def add_thread(self, thread: TaskThread) -> None:
        self.threads.add(thread.id)
        thread.task_complete.connect(self.remove_thread)
        self.threads_count += 1
        self.logger.debug("Added thread")
        self.load_bar()
        worker = Thread(target=thread.execute)
        worker.start()

    def remove_thread(self, thread_id: int) -> None:
        self.threads.remove(thread_id)
        self.logger.debug("Removed thread")
        self.load_bar()
