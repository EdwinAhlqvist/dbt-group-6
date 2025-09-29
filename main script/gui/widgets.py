# Classes for displaying images. Used in main_window.py to display camera images onto a GUI

from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# We use this to keep main_window modularized 

class ImageDisplay(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set a visible border and background color
        self.setStyleSheet("""
            border: 2px solid black;
            background-color: #f0f0f0;
        """)
        # Optional: center placeholder text
        self.setAlignment(Qt.AlignCenter)
        self.setText("Camera Display")

    def set_image(self, frame: np.ndarray):
        if frame is None:
            return
        if frame.ndim == 2:
            bit_depth = 16 if frame.dtype == np.uint else 8
            
            if bit_depth == 16:
                frame8 = (frame >> (bit_depth - 8)).astype(np.uint8)
            else:
                frame8 = frame.astype(np.uint8)

            frame_rgb = np.stack([frame8]*3, axis=-1)

        elif frame.ndim == 3 and frame.shape[2] == 3:
            frame_rgb = frame.astype(np.uint8)

        else:
            return

        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qt_image))

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
