from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from PyQt6.QtCore import QMimeData, Qt, QUrl
from PyQt6.QtGui import QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PyQt6.QtWidgets import QTreeWidget, QWidget, QAbstractItemView


class DragNDropTreeWidget(QTreeWidget):
    def __init__(self, parent: QWidget, drag_processing: Callable, drop_processing: Callable):
        super().__init__(parent)
        self.logger = parent.logger
        self.drag_processing = drag_processing
        self.drop_processing = drop_processing
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

    # TODO: fix drag&drop in itself
    def startDrag(self, supported_actions):
        items = self.selectedItems()
        if not items:
            return
        mime_data = QMimeData()
        urls = []
        temp_dir = TemporaryDirectory()
        for item in items:
            local_path = self.drag_processing(item, Path(temp_dir.name))
            if local_path is None:
                continue
            urls.append(f"file:{local_path}")
        mime_data.setUrls((QUrl(url) for url in urls))
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(supported_actions, Qt.DropAction.CopyAction)
        temp_dir.cleanup()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat("text/uri-list"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat("text/uri-list"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            position = event.position().toPoint()
            item = self.itemAt(position) if self.indexAt(position).isValid() else None
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.drop_processing(Path(file_path), item)
            self.logger.info("Got new drop")
            event.acceptProposedAction()
