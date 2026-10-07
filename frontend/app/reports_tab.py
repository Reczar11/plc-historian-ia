from datetime import datetime, timezone

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QListWidget,
    QListWidgetItem,
    QDateTimeEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, QDateTime


def _qdatetime_to_iso_utc(qdt: QDateTime) -> str:
    utc = qdt.toUTC()
    py_dt = datetime(
        utc.date().year(), utc.date().month(), utc.date().day(),
        utc.time().hour(), utc.time().minute(), utc.time().second(),
        tzinfo=timezone.utc,
    )
    return py_dt.isoformat()


class ReportsTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel('Select tags to include (one sheet per tag):'))
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.tag_list)

        form = QFormLayout()

        now_utc = QDateTime.currentDateTimeUtc().toLocalTime()
        self.start_edit = QDateTimeEdit(now_utc.addSecs(-24 * 60 * 60))
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat('yyyy-MM-dd HH:mm')
        form.addRow('Start:', self.start_edit)

        self.end_edit = QDateTimeEdit(now_utc)
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat('yyyy-MM-dd HH:mm')
        form.addRow('End:', self.end_edit)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItem('Raw (max 24h range)', 'raw')
        self.resolution_combo.addItem('1-minute average', '1min')
        self.resolution_combo.addItem('1-hour average', '1hour')
        self.resolution_combo.setCurrentIndex(1)
        form.addRow('Resolution:', self.resolution_combo)

        layout.addLayout(form)

        self.status_label = QLabel('')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.export_button = QPushButton('Export to Excel...')
        self.export_button.clicked.connect(self.export_report)
        button_row.addWidget(self.export_button)
        layout.addLayout(button_row)

        self.load_tags()

    def load_tags(self):
        try:
            tags = self.api_client.get_tags()
        except Exception as exc:
            self.status_label.setStyleSheet('color: #e06c75;')
            self.status_label.setText('Could not load tags: ' + str(exc))
            return

        self.tag_list.clear()
        for tag in tags:
            item = QListWidgetItem(tag['name'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.tag_list.addItem(item)

    def selected_tag_names(self):
        names = []
        for i in range(self.tag_list.count()):
            item = self.tag_list.item(i)
            if item.checkState() == Qt.Checked:
                names.append(item.text())
        return names

    def export_report(self):
        tags = self.selected_tag_names()
        if not tags:
            QMessageBox.information(self, 'No tags selected', 'Check at least one tag to export.')
            return

        start_iso = _qdatetime_to_iso_utc(self.start_edit.dateTime())
        end_iso = _qdatetime_to_iso_utc(self.end_edit.dateTime())
        if self.end_edit.dateTime() <= self.start_edit.dateTime():
            QMessageBox.warning(self, 'Invalid range', 'End must be after start.')
            return

        resolution = self.resolution_combo.currentData()

        default_name = 'plc_report_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.xlsx'
        path, _ = QFileDialog.getSaveFileName(self, 'Save Excel Report', default_name, 'Excel Files (*.xlsx)')
        if not path:
            return
        if not path.lower().endswith('.xlsx'):
            path += '.xlsx'

        self.status_label.setStyleSheet('color: #888888;')
        self.status_label.setText('Generating report...')
        self.export_button.setEnabled(False)
        try:
            content = self.api_client.export_excel_report(tags, start_iso, end_iso, resolution)
            with open(path, 'wb') as f:
                f.write(content)
        except Exception as exc:
            self.status_label.setStyleSheet('color: #e06c75;')
            self.status_label.setText('Could not export report: ' + str(exc))
            self.export_button.setEnabled(True)
            return

        self.status_label.setStyleSheet('color: #4ec9b0;')
        self.status_label.setText('Saved to ' + path)
        self.export_button.setEnabled(True)
