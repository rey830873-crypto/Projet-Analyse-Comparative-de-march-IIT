"""Point d'entrée de l'application Comparateur de marché."""
import sys
from PyQt6.QtWidgets import QApplication

from controllers.main_controller import MainController
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Comparateur de marché")
    app.setStyle("Fusion")
    window = MainWindow()
    controller = MainController(window)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
