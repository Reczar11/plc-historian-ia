from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QMessageBox,
    QPushButton,
    QDockWidget,
    QToolBar,
    QSizePolicy,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from .trend_widget import TrendWidget
from .alarms_panel import AlarmsPanel
from .settings_dialog import SettingsDialog
from .theme import color

# Styling now lives in app/theme/aveva_dark.qss (applied globally in main.py)
TAG_COLOR = QColor(color('accent'))


class MainWindow(QMainWindow):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle('PLC Historian')
        self.resize(1300, 850)
        self.setDockNestingEnabled(True)

        # --- Central widget: Trend is always visible, like a SCADA canvas ---
        self.trend_widget = TrendWidget(api_client)
        self.setCentralWidget(self.trend_widget)

        # --- Left dock: Asset Tree ---
        self.tag_tree = QTreeWidget()
        self.tag_tree.setHeaderLabel('Asset Tree')
        self.tag_tree.itemClicked.connect(self.handle_tree_click)

        self.asset_dock = QDockWidget('Asset Tree', self)
        self.asset_dock.setObjectName('asset_dock')
        self.asset_dock.setWidget(self.tag_tree)
        self.asset_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self.asset_dock)

        # --- Bottom dock: Alarms ---
        self.alarms_panel = AlarmsPanel(api_client)
        self.alarms_dock = QDockWidget('Alarms', self)
        self.alarms_dock.setObjectName('alarms_dock')
        self.alarms_dock.setWidget(self.alarms_panel)
        self.alarms_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.BottomDockWidgetArea, self.alarms_dock)

        self.resizeDocks([self.alarms_dock], [220], Qt.Vertical)

        self.build_menu()
        self.build_top_bar()

        self.load_asset_tree()

    def build_top_bar(self):
        # A fixed toolbar pinned to the top of the window (independent of
        # the dock layout), holding the session label and Settings button.
        toolbar = QToolBar('Top Bar', self)
        toolbar.setObjectName('top_bar')
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        status_label = QLabel('Logged in as ' + str(self.api_client.username) + ' (' + str(self.api_client.role) + ')')
        status_label.setObjectName('statusLabel')
        toolbar.addWidget(status_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        settings_button = QPushButton('Settings')
        settings_button.clicked.connect(self.open_settings)
        toolbar.addWidget(settings_button)

    def build_menu(self):
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu('View')
        view_menu.addAction(self.asset_dock.toggleViewAction())
        view_menu.addAction(self.alarms_dock.toggleViewAction())

        admin_menu = menu_bar.addMenu('Admin')
        settings_action = admin_menu.addAction('Settings...')
        settings_action.triggered.connect(self.open_settings)

    def open_settings(self):
        dialog = SettingsDialog(self.api_client, self)
        dialog.exec()
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
            tag_item.setData(0, Qt.UserRole, tag['name'])
            item.addChild(tag_item)
        return item

    def handle_tree_click(self, item, column):
        tag_name = item.data(0, Qt.UserRole)
        if tag_name:
            self.trend_widget.show_tag(tag_name)
