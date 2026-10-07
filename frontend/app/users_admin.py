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
)

ROLES = ['operator', 'engineer', 'admin']

COLUMNS = ['ID', 'Username', 'Role', 'Created At']


class UserFormDialog(QDialog):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.is_edit = user is not None
        self.setWindowTitle('Edit User' if self.is_edit else 'Add User')
        self.resize(360, 220)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.username_input = QLineEdit()
        if self.is_edit:
            self.username_input.setText(user.get('username', ''))
            self.username_input.setEnabled(False)
        form.addRow('Username:', self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        if self.is_edit:
            self.password_input.setPlaceholderText('Leave blank to keep current password')
        else:
            self.password_input.setPlaceholderText('At least 6 characters')
        form.addRow('Password:', self.password_input)

        self.role_combo = QComboBox()
        self.role_combo.addItems(ROLES)
        if self.is_edit:
            index = self.role_combo.findText(user.get('role', 'operator'))
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
        form.addRow('Role:', self.role_combo)

        layout.addLayout(form)

        self.error_label = QLabel('')
        self.error_label.setStyleSheet('color: #e06c75;')
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.try_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def try_accept(self):
        password = self.password_input.text()
        if not self.is_edit:
            if not self.username_input.text().strip():
                self.error_label.setText('Username is required.')
                return
            if len(password) < 6:
                self.error_label.setText('Password must be at least 6 characters.')
                return
        else:
            if password and len(password) < 6:
                self.error_label.setText('Password must be at least 6 characters (or leave blank).')
                return
        self.accept()

    def get_user_data(self):
        if not self.is_edit:
            return {
                'username': self.username_input.text().strip(),
                'password': self.password_input.text(),
                'role': self.role_combo.currentText(),
            }
        data = {'role': self.role_combo.currentText()}
        password = self.password_input.text()
        if password:
            data['password'] = password
        return data


class UsersTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.users_by_row = []

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        self.add_button = QPushButton('Add User')
        self.add_button.clicked.connect(self.add_user)
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
            users = self.api_client.get_users()
        except Exception as exc:
            self.status_label.setStyleSheet('color: #e06c75;')
            self.status_label.setText('Could not load users: ' + str(exc))
            return

        self.users_by_row = users
        self.status_label.setText('')

        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            values = [
                str(user.get('id', '')),
                user.get('username', ''),
                user.get('role', ''),
                str(user.get('created_at', '')),
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def selected_user(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        if row >= len(self.users_by_row):
            return None
        return self.users_by_row[row]

    def add_user(self):
        dialog = UserFormDialog(parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_user_data()
        try:
            self.api_client.create_user(data['username'], data['password'], data['role'])
        except Exception as exc:
            QMessageBox.warning(self, 'Could not create user', str(exc))
            return
        self.refresh()

    def edit_selected(self):
        user = self.selected_user()
        if user is None:
            QMessageBox.information(self, 'No selection', 'Select a user row first.')
            return
        dialog = UserFormDialog(user=user, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_user_data()
        try:
            self.api_client.update_user(user['id'], password=data.get('password'), role=data.get('role'))
        except Exception as exc:
            QMessageBox.warning(self, 'Could not update user', str(exc))
            return
        self.refresh()

    def delete_selected(self):
        user = self.selected_user()
        if user is None:
            QMessageBox.information(self, 'No selection', 'Select a user row first.')
            return
        confirm = QMessageBox.question(
            self,
            'Delete user',
            'Delete user "' + user.get('username', '') + '"? This cannot be undone.',
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self.api_client.delete_user(user['id'])
        except Exception as exc:
            QMessageBox.warning(self, 'Could not delete user', str(exc))
            return
        self.refresh()
