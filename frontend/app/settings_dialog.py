from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QTabWidget,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from .tags_admin import TagsTab
from .users_admin import UsersTab
from .reports_tab import ReportsTab


class PLCConnectionTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.source_combo = QComboBox()
        self.source_combo.addItem('Simulated', 'simulated')
        self.source_combo.addItem('Real PLC (Allen-Bradley)', 'real')
        self.source_combo.addItem('Modbus TCP', 'modbus')
        self.source_combo.currentIndexChanged.connect(self.update_field_visibility)
        form.addRow('Data Source:', self.source_combo)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText('e.g. 192.168.1.50 (or 192.168.1.50/1 for Allen-Bradley slot)')
        form.addRow('PLC IP Address:', self.ip_input)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText('502')
        form.addRow('Port (Modbus):', self.port_input)

        self.unit_id_input = QLineEdit()
        self.unit_id_input.setPlaceholderText('1')
        form.addRow('Unit / Slave ID (Modbus):', self.unit_id_input)

        layout.addLayout(form)

        self.modbus_help_label = QLabel(
            "Modbus tags: set each tag's PLC Address as \"<TYPE>:<ADDRESS>\", e.g. "
            "\"HR:100\" (holding register), \"IR:50\" (input register), \"COIL:3\", "
            "\"DI:7\" (discrete input). Address is 0-based. Data Type on the tag "
            "controls decoding: REAL/DINT use 2 registers, INT uses 1, "
            "COIL/DI are always a single bit."
        )
        self.modbus_help_label.setWordWrap(True)
        self.modbus_help_label.setStyleSheet('color: #888888; font-size: 11px;')
        layout.addWidget(self.modbus_help_label)

        self.updated_label = QLabel('')
        self.updated_label.setStyleSheet('color: #888888; font-size: 11px;')
        layout.addWidget(self.updated_label)

        self.status_label = QLabel('')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_config)
        button_row.addWidget(self.save_button)
        layout.addLayout(button_row)

        self.load_config()

    def update_field_visibility(self):
        is_modbus = self.source_combo.currentData() == 'modbus'
        self.port_input.setVisible(is_modbus)
        self.unit_id_input.setVisible(is_modbus)
        self.modbus_help_label.setVisible(is_modbus)

    def load_config(self):
        try:
            config = self.api_client.get_plc_config()
        except Exception as exc:
            self.status_label.setStyleSheet('color: #e06c75;')
            self.status_label.setText('Could not load PLC config: ' + str(exc))
            return

        self.ip_input.setText(config.get('plc_ip') or '')
        index = self.source_combo.findData(config.get('data_source', 'simulated'))
        if index >= 0:
            self.source_combo.setCurrentIndex(index)
        self.port_input.setText(str(config.get('port')) if config.get('port') else '')
        self.unit_id_input.setText(str(config.get('unit_id')) if config.get('unit_id') else '')
        self.update_field_visibility()
        updated_at = config.get('updated_at')
        if updated_at:
            self.updated_label.setText('Last updated: ' + str(updated_at))

    def save_config(self):
        plc_ip = self.ip_input.text().strip() or None
        data_source = self.source_combo.currentData()

        port_text = self.port_input.text().strip()
        unit_id_text = self.unit_id_input.text().strip()
        try:
            port = int(port_text) if port_text else None
            unit_id = int(unit_id_text) if unit_id_text else None
        except ValueError:
            self.status_label.setStyleSheet('color: #e06c75;')
            self.status_label.setText('Port and Unit ID must be whole numbers.')
            return

        self.status_label.setStyleSheet('color: #888888;')
        self.status_label.setText('Saving...')
        self.save_button.setEnabled(False)
        try:
            self.api_client.update_plc_config(plc_ip, data_source, port, unit_id)
        except Exception as exc:
            self.status_label.setStyleSheet('color: #e06c75;')
            self.status_label.setText('Could not save: ' + str(exc))
            self.save_button.setEnabled(True)
            return

        self.status_label.setStyleSheet('color: #4ec9b0;')
        self.status_label.setText('Saved. The driver will pick up this change automatically within ~30 seconds.')
        self.save_button.setEnabled(True)
        self.load_config()


class SettingsDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.resize(760, 520)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(PLCConnectionTab(api_client), 'PLC Connection')
        tabs.addTab(TagsTab(api_client), 'Tags')
        tabs.addTab(UsersTab(api_client), 'Users')
        tabs.addTab(ReportsTab(api_client), 'Reports')
        layout.addWidget(tabs)
