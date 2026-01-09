import sys
from PySide6.QtWidgets import QApplication # type: ignore
from .ui.main_windows import MainWindow
from .db.modelos import crear_tablas

def main():
    crear_tablas()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
