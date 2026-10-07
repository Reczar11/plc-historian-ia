from datetime import datetime, timedelta, timezone
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
from .theme import color

pg.setConfigOption('background', color('bg'))
pg.setConfigOption('foreground', color('text'))

HISTORY_MINUTES = 10
REFRESH_MS = 2000


class TrendWidget(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.current_tag = None

        layout = QVBoxLayout(self)
        self.title_label = QLabel('Select a tag to view trends here.')
        self.title_label.setObjectName('trendTitle')  # styled in aveva_dark.qss
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.hide()
        layout.addWidget(self.plot_widget)

        self.curve = self.plot_widget.plot(pen=pg.mkPen(color('accent'), width=2))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)

    def show_tag(self, tag_name):
        self.current_tag = tag_name
        self.title_label.setText(tag_name)
        self.plot_widget.show()
        self.refresh_data()
        self.timer.start(REFRESH_MS)

    def refresh_data(self):
        if not self.current_tag:
            return
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=HISTORY_MINUTES)
        try:
            data = self.api_client.get_readings(
                self.current_tag,
                start.isoformat(),
                end.isoformat(),
                resolution='raw',
            )
        except Exception:
            import traceback
            print(f"[TREND_DEBUG] Error fetching readings for tag={self.current_tag!r}")
            traceback.print_exc()
            return
        print(f"[TREND_DEBUG] tag={self.current_tag!r} got {len(data) if data is not None else 'None'} points")
        if not data:
            return
        x_values = []
        y_values = []
        base_time = None
        for point in data:
            timestamp = datetime.fromisoformat(point['time'])
            if base_time is None:
                base_time = timestamp
            x_values.append((timestamp - base_time).total_seconds())
            y_values.append(point['value'])
        self.curve.setData(x_values, y_values)
