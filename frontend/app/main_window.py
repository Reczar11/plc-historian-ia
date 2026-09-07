from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle('PLC Historian')
        self.resize(1000, 700)

        central = QWidget()
        layout = QVBoxLayout(central)
        welcome = QLabel('Logged in as ' + str(api_client.username) + ' (' + str(api_client.role) + ')')
        welcome.setStyleSheet('font-size: 16px; padding: 20px;')
        layout.addWidget(welcome)
        self.setCentralWidget(central)
