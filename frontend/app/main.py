import os
import sys
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QDialog
from .api_client import ApiClient
from .login_window import LoginWindow
from .main_window import MainWindow
from .theme import apply_theme

load_dotenv()


def main():
    app = QApplication(sys.argv)
    apply_theme(app)  # global theme: login, main window and every dialog
    base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')
    api_client = ApiClient(base_url)

    login = LoginWindow(api_client)
    if login.exec() != QDialog.Accepted:
        sys.exit(0)

    window = MainWindow(api_client)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
