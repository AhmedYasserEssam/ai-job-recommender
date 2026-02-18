import logging
import sys

from PyQt6.QtWidgets import QApplication
from ui import CareerApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    app = QApplication(sys.argv)
    window = CareerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
