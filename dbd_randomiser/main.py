"""
Entry point for the DBD Perk Roulette application.
Initializes the QApplication and shows the main window.
"""

import sys, traceback
from PyQt6.QtWidgets import QApplication
from ui_main_window import MainWindow

def main():
    """Create the app, show the main window, and start the event loop."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

def excepthook(exc_type, exc_value, exc_tb):
    # print a full Python traceback when anything un-caught happens
    traceback.print_exception(exc_type, exc_value, exc_tb)
    # now shut down
    sys.exit(1)

sys.excepthook = excepthook

if __name__ == "__main__":
    main()
