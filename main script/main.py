# Main script. Calls main_window and opens GUI window.

import os
import sys

# Defines path to find dlls folder
def configure_path():
    is_64bits = sys.maxsize > 2**32
    # Relative path from active folder to dlls folder
    # NOTE: Current path is set according to a specific set of folder levels. Works if folder levels are kept as posted on GitLab.
    relative_path_to_dlls = 'Scientific Camera Interfaces' + os.sep + 'SDK' + os.sep + 'Python Toolkit' + os.sep + 'dlls' + os.sep

    if is_64bits:
        relative_path_to_dlls += '64_lib'
    else:
        relative_path_to_dlls += '32_lib'

    absolute_path_to_file_directory = os.path.dirname(os.path.abspath(__file__))

    absolute_path_to_dlls = os.path.abspath(absolute_path_to_file_directory + os.sep + relative_path_to_dlls)

    os.environ['PATH'] = absolute_path_to_dlls + os.pathsep + os.environ['PATH']

    try:
        # Python 3.8 introduces a new method to specify dll directory
        os.add_dll_directory(absolute_path_to_dlls)
    except AttributeError:
        pass

try:
    configure_path()
except ImportError:
    configure_path = None

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

# Contact: edwinahlqvist@gmail.com


if __name__ == "__main__":
    app = QApplication(sys.argv) # init the Qt application
    window = MainWindow() # Main window class - control program from here
    window.show()
    sys.exit(app.exec())
