import sys
from PyQt5.QtWidgets import QApplication
from windows.main import MainWindow
import qdarkstyle


## Main Function
def main():
    app = QApplication(sys.argv)
    
    # Set app style
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    # Create main window
    main_window = MainWindow()
    
    # Center main window
    main_window.center_window()
    
    # Show window
    main_window.show()
    
    sys.exit(app.exec_())

    
if __name__ == '__main__':
    main()