from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QSplitter,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-size: 13px;
}
QTreeWidget {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    color: #e0e0e0;
}
QTreeWidget::item {
    padding: 4px;
}
QTreeWidget::item:selected {
    background-color: #094771;
}
QLabel#statusLabel {
    color: #4ec9b0;
    padding: 8px;
    font-weight: bold;
}
QHeaderView::section {
    background-color: #2d2d30;
    color: #e0e0e0;
    padding: 4px;
    border: none;
}
"""

TAG_COLOR = QColor('#4ec9b0')


class MainWindow(QMainWindow):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle('PLC Historian')
        self.resize(1200, 800)
        self.setStyleSheet(DARK_STYLESHEET)

        central = QWidget()
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        status_label = QLabel('Logged in as ' + str(api_client.username) + ' (' + str(api_client.role) + ')')
        status_label.setObjectName('statusLabel')
        outer_layout.addWidget(status_label)

        splitter = QSplitter(Qt.Horizontal)

        self.tag_tree = QTreeWidget()
        self.tag_tree.setHeaderLabel('Asset Tree')
        self.tag_tree.setMinimumWidth(280)
        splitter.addWidget(self.tag_tree)

        placeholder = QLabel('Select a tag to view trends here.')
        placeholder.setAlignment(Qt.AlignCenter)
        splitter.addWidget(placeholder)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        outer_layout.addWidget(splitter)
        self.setCentralWidget(central)

        self.load_asset_tree()

    def load_asset_tree(self):
        try:
            tree_data = self.api_client.get_assets_tree()
        except Exception as exc:
            QMessageBox.warning(self, 'Could not load assets', str(exc))
            return
        self.tag_tree.clear()
        for node in tree_data:
            item = self.build_tree_item(node)
            self.tag_tree.addTopLevelItem(item)
        self.tag_tree.expandAll()

    def build_tree_item(self, node):
        label = node['name'] + '  [' + node['asset_type'] + ']'
        item = QTreeWidgetItem([label])
        for child in node.get('children', []):
            child_item = self.build_tree_item(child)
            item.addChild(child_item)
        for tag in node.get('tags', []):
            tag_item = QTreeWidgetItem([tag['name']])
            tag_item.setForeground(0, TAG_COLOR)
            item.addChild(tag_item)
        return item
