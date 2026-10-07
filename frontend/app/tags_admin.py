from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QHeaderView,
)

DATA_TYPES = ['REAL', 'DINT', 'INT', 'BOOL', 'STRING']

COLUMNS = ['ID', 'Name', 'PLC Address', 'Type', 'Unit', 'Alarm Low', 'Alarm High', 'Asset']


def flatten_assets(tree, depth=0, out=None):
    if out is None:
        out = []
    for node in tree:
        label = ('  ' * depth) + node['name'] + ' [' + node['asset_type'] + ']'
        out.append((node['id'], label))
        flatten_assets(node.get('children', []), depth + 1, out)
    return out


def build_asset_name_lookup(tree, out=None):
    if out is None:
        out = {}
    for node in tree:
        out[node['id']] = node['name']
        build_asset_name_lookup(node.get('children', []), out)
    return out


def _to_float_or_none(text):
    text = text.strip()
    if not text:
        return None
    return float(text)


class TagFormDialog(QDialog):
    def __init__(self, asset_options, tag=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Edit Tag' if tag else 'Add Tag')
        self.resize(380, 320)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        form.addRow('Name:', self.name_input)

        self.plc_address_input = QLineEdit()
        self.plc_address_input.setPlaceholderText('optional')
        form.addRow('PLC Address:', self.plc_address_input)

        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(DATA_TYPES)
        form.addRow('Data Type:', self.data_type_combo)

        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText('e.g. bar, F, mm/s')
        form.addRow('Engineering Unit:', self.unit_input)

        self.alarm_low_input = QLineEdit()
        self.alarm_low_input.setPlaceholderText('optional')
        form.addRow('Alarm Low:', self.alarm_low_input)

        self.alarm_high_input = QLineEdit()
        self.alarm_high_input.setPlaceholderText('optional')
        form.addRow('Alarm High:', self.alarm_high_input)

        self.asset_combo = QComboBox()
        self.asset_combo.addItem('(none)', None)
        for asset_id, label in asset_options:
            self.asset_combo.addItem(label, asset_id)
        form.addRow('Asset:', self.asset_combo)

        layout.addLayout(form)

        self.error_label = QLabel('')
        self.error_label.setStyleSheet('color: #e06c75;')
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.try_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if tag:
            self.name_input.setText(tag.get('name', ''))
            self.plc_address_input.setText(tag.get('plc_address') or '')
            index = self.data_type_combo.findText(tag.get('data_type', 'REAL'))
            if index >= 0:
                self.data_type_combo.setCurrentIndex(index)
            self.unit_input.setText(tag.get('engineering_unit') or '')
            if tag.get('alarm_low') is not None:
                self.alarm_low_input.setText(str(tag['alarm_low']))
            if tag.get('alarm_high') is not None:
                self.alarm_high_input.setText(str(tag['alarm_high']))
            asset_index = self.asset_combo.findData(tag.get('asset_id'))
            if asset_index >= 0:
                self.asset_combo.setCurrentIndex(asset_index)

    def try_accept(self):
        if not self.name_input.text().strip():
            self.error_label.setText('Name is required.')
            return
        try:
            self.get_tag_data()
        except ValueError:
            self.error_label.setText('Alarm Low / Alarm High must be numbers (or left empty).')
            return
        self.accept()

    def get_tag_data(self):
        return {
            'name': self.name_input.text().strip(),
            'plc_address': self.plc_address_input.text().strip() or None,
            'data_type': self.data_type_combo.currentText(),
            'engineering_unit': self.unit_input.text().strip() or None,
            'alarm_low': _to_float_or_none(self.alarm_low_input.text()),
            'alarm_high': _to_float_or_none(self.alarm_high_input.text()),
            'asset_id': self.asset_combo.currentData(),
        }


class TagsTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.tags_by_row = []
        self.asset_options = []
        self.asset_names = {}

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        self.add_button = QPushButton('Add Tag')
        self.add_button.clicked.connect(self.add_tag)
        toolbar.addWidget(self.add_button)

        self.edit_button = QPushButton('Edit Selected')
        self.edit_button.clicked.connect(self.edit_selected)
        toolbar.addWidget(self.edit_button)

        self.delete_button = QPushButton('Delete Selected')
        self.delete_button.clicked.connect(self.delete_selected)
        toolbar.addWidget(self.delete_button)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.status_label = QLabel('')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.refresh()

    def refresh(self):
        try:
            tree = self.api_client.get_assets_tree()
            tags = self.api_client.get_tags()
        except Exception as exc:
            self.status_label.setStyleSheet('color: #e06c75;')
            self.status_label.setText('Could not load tags: ' + str(exc))
            return

        self.asset_options = flatten_assets(tree)
        self.asset_names = build_asset_name_lookup(tree)
        self.tags_by_row = tags
        self.status_label.setText('')

        self.table.setRowCount(len(tags))
        for row, tag in enumerate(tags):
            asset_id = tag.get('asset_id')
            asset_label = self.asset_names.get(asset_id, '') if asset_id else ''
            values = [
                str(tag.get('id', '')),
                tag.get('name', ''),
                tag.get('plc_address') or '',
                tag.get('data_type', ''),
                tag.get('engineering_unit') or '',
                '' if tag.get('alarm_low') is None else str(tag.get('alarm_low')),
                '' if tag.get('alarm_high') is None else str(tag.get('alarm_high')),
                asset_label,
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def selected_tag(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        if row >= len(self.tags_by_row):
            return None
        return self.tags_by_row[row]

    def add_tag(self):
        dialog = TagFormDialog(self.asset_options, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_tag_data()
        try:
            self.api_client.create_tag(data)
        except Exception as exc:
            QMessageBox.warning(self, 'Could not create tag', str(exc))
            return
        self.refresh()

    def edit_selected(self):
        tag = self.selected_tag()
        if tag is None:
            QMessageBox.information(self, 'No selection', 'Select a tag row first.')
            return
        dialog = TagFormDialog(self.asset_options, tag=tag, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_tag_data()
        try:
            self.api_client.update_tag(tag['id'], data)
        except Exception as exc:
            QMessageBox.warning(self, 'Could not update tag', str(exc))
            return
        self.refresh()

    def delete_selected(self):
        tag = self.selected_tag()
        if tag is None:
            QMessageBox.information(self, 'No selection', 'Select a tag row first.')
            return
        confirm = QMessageBox.question(
            self,
            'Delete tag',
            'Delete tag "' + tag.get('name', '') + '"? This cannot be undone.',
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.api_client.delete_tag(tag['id'])
        except Exception as exc:
            QMessageBox.warning(self, 'Could not delete tag', str(exc))
            return
        self.refresh()
