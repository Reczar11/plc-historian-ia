from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QMessageBox


class LoginWindow(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle('PLC Historian - Login')
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)

        title = QLabel('PLC Historian')
        title.setStyleSheet('font-size: 20px; font-weight: bold;')
        layout.addWidget(title)

        form = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form.addRow('Username:', self.username_input)
        form.addRow('Password:', self.password_input)
        layout.addLayout(form)

        self.login_button = QPushButton('Login')
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, 'Missing data', 'Please enter username and password.')
            return
        try:
            self.api_client.login(username, password)
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, 'Login failed', str(exc))
