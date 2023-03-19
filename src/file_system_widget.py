import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QTreeWidgetItem, QFileDialog
from filesocket import ManagingClient, ServerError, PathNotFoundError


class FileSystemWidget(QWidget):
    def __init__(self, client: ManagingClient):
        super().__init__()
        uic.loadUi("res/ui/file_system_widget.ui", self)

        self.current_path = Path("")
        self.tree_widget_items = dict()
        self.root = self.treeWidget.invisibleRootItem()
        self.client = client

        self.selection_processing()
        self.load_tree_widget()
        self.treeWidget.itemDoubleClicked.connect(self.open_dir)
        self.treeWidget.itemSelectionChanged.connect(self.selection_processing)
        self.downloadBtn.clicked.connect(self.download_processing)
        self.uploadBtn.clicked.connect(self.upload_processing)
        self.deleteBtn.clicked.connect(self.delete_processing)

    def load_tree_widget(self) -> None:
        if str(self.current_path) == '.':
            try:
                disks = self.client.cmd_command("wmic logicaldisk get name")['out'].split(':')
            except ServerError:
                sys.exit()
            disks = list(map(lambda s: s.split('\n')[-1], disks[:-1]))
            dirs_to_show = list(map(lambda disk: f"{disk}:/", disks))
            files_to_show = []
        else:
            try:
                file_list = self.client.list_files(self.current_path)
            except ServerError:
                sys.exit()
            if file_list is None:
                return
            dirs_to_show = file_list['dirs']
            files_to_show = file_list['files']
        self.import_data(dirs_to_show, files_to_show)

    def import_data(self, dirs_to_show: list, files_to_show: list) -> None:
        if str(self.current_path) in self.tree_widget_items:
            parent = self.tree_widget_items[str(self.current_path)]
        else:
            parent = self.root
        for directory in dirs_to_show:
            directory_node = QTreeWidgetItem(parent, (directory, "", "directory", ""))
            self.tree_widget_items[str(self.current_path / directory)] = directory_node
        for file in files_to_show:
            file_node = QTreeWidgetItem(parent, (file, "", Path(file).suffix[1:], ""))
            self.tree_widget_items[str(self.current_path / file)] = file_node

    @staticmethod
    def _is_dir(item: QTreeWidgetItem) -> bool:
        item_type = item.text(2)
        return item_type == "directory"

    @staticmethod
    def _get_item_path(item: QTreeWidgetItem) -> Path:
        path = item.text(0)
        parent = item.parent()
        while parent is not None:
            path = f"{parent.text(0)}/{path}"
            parent = parent.parent()
        return Path(path)

    def open_dir(self, item: QTreeWidgetItem, column: int) -> None:
        if not self._is_dir(item) or item.childCount() > 0:
            return
        self.current_path = self._get_item_path(item)
        self.load_tree_widget()
        self.treeWidget.expandItem(item.parent())
        item.setSelected(False)

    def selection_processing(self) -> None:
        count = len(self.treeWidget.selectedItems())
        if count == 0:
            self.downloadBtn.setEnabled(False)
            self.uploadBtn.setEnabled(True)
            self.deleteBtn.setEnabled(False)
        elif count == 1:
            self.downloadBtn.setEnabled(True)
            self.uploadBtn.setEnabled(True)
            self.deleteBtn.setEnabled(True)
        else:
            self.downloadBtn.setEnabled(True)
            self.uploadBtn.setEnabled(False)
            self.deleteBtn.setEnabled(True)

    def download_processing(self) -> None:
        items = self.treeWidget.selectedItems()
        try:
            for item in items:
                path = self._get_item_path(item)
                self.client.get_file(path)
        except ServerError | PathNotFoundError | IOError:
            return

    def upload_processing(self) -> None:
        items = self.treeWidget.selectedItems()
        destination = Path("") if len(items) == 0 else self._get_item_path(items[0])
        paths = QFileDialog.getOpenFileNames(self, "Choose file to send", "")
        try:
            for path in paths[0]:
                self.client.send_file(Path(path), destination)
        except ServerError | PathNotFoundError:
            return

    def delete_processing(self) -> None:
        items = self.treeWidget.selectedItems()
        try:
            for item in items:
                path = self._get_item_path(item)
                if self._is_dir(item):
                    self.client.cmd_command(f"rmdir /s {path}")
                else:
                    self.client.cmd_command(f"del /f {path}")
                (item.parent() or self.root).removeChild(item)
        except ServerError:
            return
