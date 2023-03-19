import sys
from pathlib import Path
from typing import Tuple

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QTreeWidgetItem, QFileDialog, QMessageBox
from filesocket import ManagingClient, ServerError, PathNotFoundError


class FileSystemWidget(QWidget):
    def __init__(self, client: ManagingClient):
        super().__init__()
        uic.loadUi("res/ui/file_system_widget.ui", self)

        self.root = self.treeWidget.invisibleRootItem()
        self.client = client
        self.item_old_name = ""

        self.selection_processing()
        self.load_tree_widget(self.root)
        self.treeWidget.itemDoubleClicked.connect(self.open_dir)
        self.treeWidget.itemSelectionChanged.connect(self.selection_processing)
        self.treeWidget.itemChanged.connect(self.rename_processing_back)

        self.downloadBtn.clicked.connect(self.download_processing)
        self.uploadBtn.clicked.connect(self.upload_processing)
        self.renameBtn.clicked.connect(self.rename_processing_front)
        self.deleteBtn.clicked.connect(self.delete_processing)

    # Expand directory
    def load_tree_widget(self, parent: QTreeWidgetItem) -> None:
        if parent == self.root:
            try:
                disks = self.client.cmd_command("wmic logicaldisk get name")['out'].split(':')
            except ServerError:
                sys.exit()
            disks = list(map(lambda s: s.split('\n')[-1], disks[:-1]))
            dirs_to_show = list(map(lambda disk: f"{disk}:/", disks))
            files_to_show = []
        else:
            try:
                file_list = self.client.list_files(self._get_item_path(parent))
            except ServerError:
                sys.exit()
            if file_list is None:
                return
            dirs_to_show = file_list['dirs']
            files_to_show = file_list['files']
        self.import_data(parent, dirs_to_show, files_to_show)

    # Create new items
    @staticmethod
    def import_data(parent: QTreeWidgetItem, dirs_to_show: list, files_to_show: list) -> None:
        for directory in dirs_to_show:
            directory_node = QTreeWidgetItem(parent, (directory, "", "directory", ""))
        for file in files_to_show:
            file_node = QTreeWidgetItem(parent, (file, "", Path(file).suffix[1:], ""))

    # Check is directory
    @staticmethod
    def _is_dir(item: QTreeWidgetItem) -> bool:
        item_type = item.text(2)
        return item_type == "directory"

    # Get path of item
    @staticmethod
    def _get_item_path(item: QTreeWidgetItem) -> Path:
        path = item.text(0)
        parent = item.parent()
        while parent is not None:
            path = f"{parent.text(0)}/{path}"
            parent = parent.parent()
        return Path(path)

    # Expand directory
    def open_dir(self, item: QTreeWidgetItem, column: int) -> None:
        if not self._is_dir(item) or item.childCount() > 0:
            return
        self.load_tree_widget(item)
        self.treeWidget.expandItem(item.parent())
        item.setSelected(False)

    # Change availability of button based on count of selected items
    def selection_processing(self) -> None:
        count = len(self.treeWidget.selectedItems())
        if count == 0:
            self.downloadBtn.setEnabled(False)
            self.uploadBtn.setEnabled(True)
            self.renameBtn.setEnabled(False)
            self.deleteBtn.setEnabled(False)
        elif count == 1:
            self.downloadBtn.setEnabled(True)
            self.uploadBtn.setEnabled(True)
            self.renameBtn.setEnabled(True)
            self.deleteBtn.setEnabled(True)
        else:
            self.downloadBtn.setEnabled(True)
            self.uploadBtn.setEnabled(False)
            self.renameBtn.setEnabled(False)
            self.deleteBtn.setEnabled(True)

    # Download item
    def download_processing(self) -> None:
        items = self.treeWidget.selectedItems()
        try:
            for item in items:
                path = self._get_item_path(item)
                self.client.get_file(path)
        except ServerError | PathNotFoundError | IOError:
            return

    # Upload new item
    def upload_processing(self) -> None:
        items = self.treeWidget.selectedItems()
        destination = Path("") if len(items) == 0 else self._get_item_path(items[0])
        paths = QFileDialog.getOpenFileNames(self, "Choose file to send", "")
        try:
            for path in paths[0]:
                self.client.send_file(Path(path), destination)
        except ServerError | PathNotFoundError:
            return

    # Rename in TreeWidget
    def rename_processing_front(self) -> None:
        item = self.treeWidget.selectedItems()[0]
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.item_old_name = item.text(0)
        self.treeWidget.editItem(item, 0)

    # Rename on PC
    def rename_processing_back(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0 or self.item_old_name == "" or item.parent() is None:
            self.item_old_name = ""
            return
        item_new_name = item.text(0)
        parent_path = self._get_item_path(item.parent())
        try:
            self.client.cmd_command(f"ren {parent_path / self.item_old_name} {item_new_name}")
        except ServerError:
            pass
        self.item_old_name = ""
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def _confirm_delete(self, files: Tuple[str]) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        text = "Are you sure you want to delete following files and dirs:\n"
        text += '\n'.join(files) + '?'
        box.setText(text)
        box.setWindowIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Delete confirmation")
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return box.exec() == QMessageBox.StandardButton.Yes

    # Delete item
    def delete_processing(self) -> None:
        items = self.treeWidget.selectedItems()
        if not self._confirm_delete(tuple(item.text(0) for item in items)):
            return
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
