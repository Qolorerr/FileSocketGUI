import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict

from PyQt6 import uic
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget, QTreeWidgetItem, QFileDialog, QMessageBox, QAbstractItemView, QMenu
from filesocket import ManagingClient, ServerError, PathNotFoundError

from src.threads import DownloadThread, UploadThread, CMDThread
from src.dragndrop_tree_widget import DragNDropTreeWidget
from src.taskbar_processor import TaskbarProcessor


class FileSystemWidget(QWidget):
    def __init__(self, parent: QWidget, client: ManagingClient):
        super().__init__(parent)
        uic.loadUi("res/ui/file_system_widget.ui", self)

        self.logger = parent.logger
        self.client = client

        self.treeWidget = DragNDropTreeWidget(self, self._drag_processing, self._drop_processing)
        self.tree_widget_setup()

        self.root = self.treeWidget.invisibleRootItem()
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

        self.taskbar_processor = TaskbarProcessor(self, self.progressBar, self.progressBarText)

    def _drag_processing(self, item: QTreeWidgetItem, temp_dir: Path) -> Path | None:
        # TODO: fix "File saving error (OSError(22, 'Invalid argument'),)"
        try:
            path = self._get_item_path(item)
            filename = path.name
            local_path = temp_dir / filename
            self.taskbar_processor.add_thread(DownloadThread(self, self.client, path, temp_dir))
        except ServerError as e:
            self.logger.info(f"Server error {e.args}")
            return None
        except PathNotFoundError:
            self.logger.info("Path does not exist")
            return None
        except IOError as e:
            self.logger.info(f"File saving error {e.args}")
            return None
        return local_path

    def _drop_processing(self, path_from: Path, item_to: QTreeWidgetItem | None) -> None:
        if item_to is None:
            destination = Path("")
        else:
            if self._is_dir(item_to):
                item_dir = item_to
            else:
                item_dir = item_to.parent()
            destination = self._get_item_path(item_dir)
        try:
            self.taskbar_processor.add_thread(UploadThread(self, self.client, path_from, destination))
            if item_to is not None:
                self.open_dir(item_dir, 0)
        except ServerError as e:
            self.logger.info(f"Server error {e.args}")
        except PathNotFoundError:
            self.logger.info("Path does not exist")

    def tree_widget_setup(self):
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)
        __qtreewidgetitem.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
        __qtreewidgetitem.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
        __qtreewidgetitem.setTextAlignment(0, Qt.AlignmentFlag.AlignCenter)
        self.treeWidget.setHeaderItem(__qtreewidgetitem)
        self.treeWidget.setObjectName(u"treeWidget")
        self.treeWidget.setGeometry(QRect(10, 60, 781, 501))
        self.treeWidget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.treeWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.header().setDefaultSectionSize(200)
        __qtreewidgetitem.setText(0, "Name")
        __qtreewidgetitem.setText(1, "Date modified")
        __qtreewidgetitem.setText(2, "Type")
        __qtreewidgetitem.setText(3, "Size")
        self.treeWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.open_context_menu)

    # Context menu
    def open_context_menu(self, position: QPoint) -> None:
        self.logger.debug(f"{type(position)}: {position}")
        menu = QMenu(self)
        if self.downloadBtn.isEnabled():
            download_action = QAction("Download", menu)
            download_action.triggered.connect(self.download_processing)
            menu.addAction(download_action)
        if self.uploadBtn.isEnabled():
            download_action = QAction("Upload here", menu)
            download_action.triggered.connect(self.upload_processing)
            menu.addAction(download_action)
        if self.renameBtn.isEnabled():
            download_action = QAction("Rename", menu)
            download_action.triggered.connect(self.rename_processing_front)
            menu.addAction(download_action)
        if self.deleteBtn.isEnabled():
            download_action = QAction("Delete", menu)
            download_action.triggered.connect(self.delete_processing)
            menu.addAction(download_action)
        menu.exec(self.treeWidget.mapToGlobal(position))

    # Expand directory
    def load_tree_widget(self, parent: QTreeWidgetItem) -> None:
        if parent == self.root:
            try:
                disks = self.client.cmd_command("wmic logicaldisk get name")['out'].split(':')
            except ServerError as e:
                self.logger.info(f"Server error {e.args}")
                self.logger.info("Closing")
                sys.exit()
            disks = list(map(lambda s: s.split('\n')[-1], disks[:-1]))
            dirs_to_show = list(map(lambda disk: {"name": f"{disk}:/", "modification_time": None}, disks))
            files_to_show = []
        else:
            try:
                file_list = self.client.list_files(self._get_item_path(parent))
            except ServerError as e:
                self.logger.info(f"Server error {e.args}")
                self.logger.info("Closing")
                sys.exit()
            if file_list is None:
                return
            dirs_to_show = file_list['dirs']
            files_to_show = file_list['files']
        self.import_data(parent, dirs_to_show, files_to_show)

    # Create new items
    @staticmethod
    def import_data(parent: QTreeWidgetItem,
                    dirs_to_show: List[Dict[str, str | int]],
                    files_to_show: List[Dict[str, str | int]]) -> None:
        children = parent.takeChildren()
        for directory in dirs_to_show:
            name = directory['name'] if 'name' in directory else "NOT_FOUND"
            if 'modification_time' in directory and directory['modification_time'] is not None:
                date = datetime.fromtimestamp(directory['modification_time']).strftime("%d.%m.%Y %H:%M")
            else:
                date = ""
            directory_node = QTreeWidgetItem(parent, (name, date, "directory", ""))
        for file in files_to_show:
            name = file['name'] if 'name' in file else "NOT_FOUND"
            if 'modification_time' in file:
                date = datetime.fromtimestamp(file['modification_time']).strftime("%d.%m.%Y %H:%M")
            else:
                date = ""
            size = str(file['size'] // (2 ** 10)) if 'size' in file else ""
            size = ' '.join([size[max(i-3, 0):i] for i in range(len(size), 0, -3)][::-1])
            # TODO: Fix default sort by size
            file_node = QTreeWidgetItem(parent, (name, date, Path(name).suffix[1:], f"{size} KB"))

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
        if not self._is_dir(item):
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
        self.treeWidget.clearSelection()
        try:
            for item in items:
                path = self._get_item_path(item)
                self.taskbar_processor.add_thread(DownloadThread(self, self.client, path))
            self.logger.info(f"Downloading {len(items)} files")
        except ServerError as e:
            self.logger.info(f"Server error {e.args}")
        except PathNotFoundError:
            self.logger.info("Path does not exist")
        except IOError as e:
            self.logger.info(f"File saving error {e.args}")

    # Upload new item
    def upload_processing(self) -> None:
        items = self.treeWidget.selectedItems()
        destination = Path("") if len(items) == 0 else self._get_item_path(items[0])
        paths = QFileDialog.getOpenFileNames(self, "Choose file to send", "")
        self.treeWidget.clearSelection()
        try:
            for path in paths[0]:
                self.taskbar_processor.add_thread(UploadThread(self, self.client, Path(path), destination))
            self.logger.info(f"Uploaded {len(paths[0])} files")
        except ServerError as e:
            self.logger.info(f"Server error {e.args}")
        except PathNotFoundError:
            self.logger.info("Path does not exist")

    # Rename in TreeWidget
    def rename_processing_front(self) -> None:
        item = self.treeWidget.selectedItems()[0]
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.item_old_name = item.text(0)
        self.treeWidget.editItem(item, 0)
        self.treeWidget.clearSelection()

    # Rename on PC
    def rename_processing_back(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0 or self.item_old_name == "" or item.parent() is None:
            self.item_old_name = ""
            return
        item_new_name = item.text(0)
        parent_path = self._get_item_path(item.parent())
        try:
            self.logger.debug(f"""Device rename response 
            {self.client.cmd_command(f'ren "{parent_path / self.item_old_name}" "{item_new_name}"')}""")
            # TODO: fix paths with spaces
        except ServerError as e:
            self.logger.info(f"Server error {e.args}")
        self.item_old_name = ""
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.logger.info("Renamed item")

    # Display confirmation window on delete
    def _confirm_delete(self, files: Tuple[str]) -> bool:
        self.logger.debug(f"Trying to delete {len(files)} files")
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        text = "Are you sure you want to delete following files and dirs:\n"
        text += '\n'.join(files) + '?'
        box.setText(text)
        box.setWindowTitle("Delete confirmation")
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.logger.debug("Created confirmation window")
        return box.exec() == QMessageBox.StandardButton.Yes

    # Delete item
    def delete_processing(self) -> None:
        items = self.treeWidget.selectedItems()
        if not self._confirm_delete(tuple(item.text(0) for item in items)):
            self.logger.debug("User refused delete")
            return
        try:
            for item in items:
                path = self._get_item_path(item)
                if self._is_dir(item):
                    self.taskbar_processor.add_thread(CMDThread(self, self.client, f'rmdir /s "{path}"'))
                else:
                    self.taskbar_processor.add_thread(CMDThread(self, self.client, f'del /f "{path}"'))
                (item.parent() or self.root).removeChild(item)
        except ServerError as e:
            self.logger.info(f"Server error {e.args}")
            return
        self.logger.info(f"Deleted {len(items)} files")
