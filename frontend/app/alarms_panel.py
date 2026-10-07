from datetime import datetime, timezone
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
    QCheckBox,
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor

REFRESH_MS = 3000

COLUMNS = ['Tag', 'Value', 'Limit', 'Type', 'Triggered', 'Status', 'Ack']

ACTIVE_UNACK_COLOR = QColor('#5a1e1e')
ACTIVE_ACK_COLOR = QColor('#4a3a1e')
CLEARED_COLOR = QColor('#252526')


class AlarmsPanel(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.alarms_by_row = []

        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        self.status_label = QLabel('Alarms')
        self.status_label.setStyleSheet('font-size: 16px; padding: 4px;')
        controls.addWidget(self.status_label)
        controls.addStretch()

        self.show_all_checkbox = QCheckBox('Show all (including cleared)')
        self.show_all_checkbox.stateChanged.connect(self.refresh_data)
        controls.addWidget(self.show_all_checkbox)

        self.ack_button = QPushButton('Acknowledge selected')
        self.ack_button.clicked.connect(self.acknowledge_selected)
        controls.addWidget(self.ack_button)

        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(REFRESH_MS)

        self.refresh_data()

    def format_time(self, iso_string):
        if not iso_string:
            return ''
        try:
            dt = datetime.fromisoformat(iso_string)
            local_dt = dt.astimezone()
            return local_dt.strftime('%H:%M:%S')
        except Exception:
            return iso_string

    def refresh_data(self):
        status = 'all' if self.show_all_checkbox.isChecked() else 'active'
        try:
            alarms = self.api_client.get_alarms(status=status)
        except Exception:
            import traceback
            print('[ALARMS_DEBUG] Error fetching alarms')
            traceback.print_exc()
            return

        self.alarms_by_row = alarms
        self.status_label.setText(f'Alarms ({len(alarms)})')

        self.table.setRowCount(len(alarms))
        for row, alarm in enumerate(alarms):
            values = [
                alarm.get('tag_name', ''),
                f"{alarm.get('value', ''):.4f}" if isinstance(alarm.get('value'), (int, float)) else str(alarm.get('value', '')),
                str(alarm.get('limit_value', '')),
                alarm.get('limit_type', ''),
                self.format_time(alarm.get('triggered_at')),
                alarm.get('status', ''),
                'Yes' if alarm.get('acknowledged') else 'No',
            ]
            is_active = alarm.get('status') == 'active'
            is_ack = alarm.get('acknowledged')
            if is_active and not is_ack:
                row_color = ACTIVE_UNACK_COLOR
            elif is_active and is_ack:
                row_color = ACTIVE_ACK_COLOR
            else:
                row_color = CLEARED_COLOR

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setBackground(row_color)
                self.table.setItem(row, col, item)

    def acknowledge_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, 'No selection', 'Select an alarm row first.')
            return
        row = selected_rows[0].row()
        if row >= len(self.alarms_by_row):
            return
        alarm = self.alarms_by_row[row]
        alarm_id = alarm.get('id')
        try:
            self.api_client.acknowledge_alarm(alarm_id)
        except Exception as exc:
            QMessageBox.warning(self, 'Could not acknowledge alarm', str(exc))
            return
        self.refresh_data()
