"""
Document tree widget for displaying and navigating document hierarchies.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import (
    QTreeView,
    QFileSystemModel,
    QAbstractItemView,
    QMenu,
    QAction,
    QFileIconProvider,
    QHeaderView,
    QVBoxLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
)

class DocumentTreeWidget(QTreeView):
    """A tree view widget for displaying and interacting with document hierarchies."""
    
    # Signals
    document_selected = pyqtSignal(str)  # Emitted when a document is selected
    document_double_clicked = pyqtSignal(str)  # Emitted when a document is double-clicked
    
    def __init__(self, parent=None):
        """Initialize the document tree widget."""
        super().__init__(parent)
        
        # Configure the tree view
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        
        # Set up the model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Documents"])
        self.setModel(self.model)
        
        # Configure header
        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        # Connect signals
        self.doubleClicked.connect(self._on_double_click)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Initialize icons
        self.icon_provider = QFileIconProvider()
        
    def add_document(self, path: str, parent: QStandardItem = None) -> QStandardItem:
        """
        Add a document to the tree.
        
        Args:
            path: Path to the document
            parent: Parent item in the tree
            
        Returns:
            The created item
        """
        item = QStandardItem(os.path.basename(path))
        item.setData(path, Qt.UserRole + 1)  # Store full path in item data
        
        # Set icon based on file type
        file_info = Path(path)
        if file_info.is_dir():
            item.setIcon(self.icon_provider.icon(self.icon_provider.Folder))
        else:
            item.setIcon(self.icon_provider.icon(self.icon_provider.File))
        
        if parent is None:
            self.model.appendRow(item)
        else:
            parent.appendRow(item)
            
        return item
    
    def clear_tree(self) -> None:
        """Clear all items from the tree."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Documents"])
    
    def _on_double_click(self, index: QModelIndex) -> None:
        """Handle double-click events on items."""
        item = self.model.itemFromIndex(index)
        if item:
            path = item.data(Qt.UserRole + 1)
            if path and Path(path).is_file():
                self.document_double_clicked.emit(path)
    
    def _show_context_menu(self, position) -> None:
        """Show the context menu for the selected item."""
        index = self.indexAt(position)
        if not index.isValid():
            return
            
        item = self.model.itemFromIndex(index)
        if not item:
            return
            
        menu = QMenu()
        
        # Add actions to the menu
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self._on_open(item))
        menu.addAction(open_action)
        
        show_in_folder_action = QAction("Show in Folder", self)
        show_in_folder_action.triggered.connect(lambda: self._on_show_in_folder(item))
        menu.addAction(show_in_folder_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._on_delete(item))
        menu.addAction(delete_action)
        
        # Show the menu
        menu.exec_(self.viewport().mapToGlobal(position))
    
    def _on_open(self, item: QStandardItem) -> None:
        """Handle the open action."""
        path = item.data(Qt.UserRole + 1)
        if path:
            self.document_selected.emit(path)
    
    def _on_show_in_folder(self, item: QStandardItem) -> None:
        """Show the selected item in the system file manager."""
        path = item.data(Qt.UserRole + 1)
        if path:
            file_path = Path(path)
            if file_path.exists():
                import platform
                import subprocess
                
                if platform.system() == "Windows":
                    os.startfile(file_path.parent if file_path.is_file() else file_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", str(file_path.parent if file_path.is_file() else file_path)])
                else:  # Linux variants
                    subprocess.Popen(["xdg-open", str(file_path.parent if file_path.is_file() else file_path)])
    
    def _on_delete(self, item: QStandardItem) -> None:
        """Handle the delete action."""
        # Note: This is just a UI operation. Actual file deletion should be handled by the parent.
        self.model.removeRow(item.row(), item.parent().index() if item.parent() else QModelIndex())


class DocumentTreeContainer(QWidget):
    """A container widget that includes a DocumentTreeWidget with search and filter controls."""
    
    # Signals
    document_selected = pyqtSignal(str)  # Emitted when a document is selected
    document_double_clicked = pyqtSignal(str)  # Emitted when a document is double-clicked
    
    def __init__(self, parent=None):
        """Initialize the document tree container."""
        super().__init__(parent)
        
        # Create the main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create search bar
        self.search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search documents...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._on_clear_clicked)
        
        self.search_layout.addWidget(QLabel("Search:"))
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.clear_button)
        
        # Create the document tree widget
        self.tree_widget = DocumentTreeWidget()
        self.tree_widget.document_selected.connect(self.document_selected.emit)
        self.tree_widget.document_double_clicked.connect(self.document_double_clicked.emit)
        
        # Add widgets to layout
        self.layout.addLayout(self.search_layout)
        self.layout.addWidget(self.tree_widget)
        
        # Set initial state
        self._update_clear_button()
    
    def _on_search_changed(self, text: str) -> None:
        """Handle search text changes."""
        self._update_clear_button()
        # TODO: Implement search filtering
        
    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.search_input.clear()
        
    def _update_clear_button(self) -> None:
        """Update the clear button state based on search input."""
        self.clear_button.setEnabled(bool(self.search_input.text()))
    
    def add_document(self, path: str, parent: QStandardItem = None) -> QStandardItem:
        """
        Add a document to the tree.
        
        Args:
            path: Path to the document
            parent: Parent item in the tree
            
        Returns:
            The created item
        """
        return self.tree_widget.add_document(path, parent)
    
    def clear_tree(self) -> None:
        """Clear all items from the tree."""
        self.tree_widget.clear_tree()
    
    def set_root_path(self, path: str) -> None:
        """
        Set the root path for the document tree.
        
        Args:
            path: Root directory path
        """
        self.tree_widget.clear_tree()
        if path and Path(path).is_dir():
            self.add_document(path)
    
    def get_selected_path(self) -> Optional[str]:
        """
        Get the path of the currently selected item.
        
        Returns:
            Selected path or None if no item is selected
        """
        selected = self.tree_widget.selectedIndexes()
        if selected:
            item = self.tree_widget.model.itemFromIndex(selected[0])
            if item:
                return item.data(Qt.UserRole + 1)
        return None
