"""
Main application window for speckle imaging GUI. 

Script starts here from main.py


"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit, QTableWidget, QTableWidgetItem, QGridLayout, QApplication
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIntValidator
import numpy as np

# Local imports
from gui.widgets import ImageDisplay, MplCanvas
from camera.camera_handler import CameraHandler
from processing.speckle import SpeckleProcessor

class PlotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speckle Plot")
        self.setGeometry(200, 200, 600, 600)

        layout = QVBoxLayout()
        self.canvas = MplCanvas(self, width=5, height=5, dpi=100)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speckle Imaging GUI")
        self.setGeometry(100, 100, 1200, 800) # Main window 1200x800 px

        # Storage for images
        self.Iref = None
        self.object_images = [] 

        # Camera handler + processor
        self.camera = CameraHandler()
        self.mode = "live"
        self.processor = SpeckleProcessor()  # empty for now

        # Central widget + grid layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout()
        central_widget.setLayout(main_layout)

        # Top-left: Camera status + live feed
        camera_layout = QVBoxLayout()
        self.camera_status = QLabel("Camera disconnected")
        self.camera_status.setStyleSheet("color: red; font-weight: bold;")
        self.camera_display = ImageDisplay()
        self.camera_display.setFixedSize(300, 300)
        camera_layout.addWidget(self.camera_status, alignment=Qt.AlignCenter)
        camera_layout.addWidget(self.camera_display, alignment=Qt.AlignCenter)

        button_layout = QHBoxLayout()
        self.activate_btn = QPushButton("Activate Camera")
        self.activate_btn.clicked.connect(self.activate_camera)
        button_layout.addWidget(self.activate_btn, alignment=Qt.AlignCenter)
        self.deactivate_btn = QPushButton("Dectivate Camera")
        self.deactivate_btn.clicked.connect(self.deactivate_camera)
        button_layout.addWidget(self.deactivate_btn, alignment=Qt.AlignCenter)
        button_layout.insertStretch(2, 2)
        button_layout.insertStretch(0, 2)
        camera_layout.addLayout(button_layout)

        camera_mode_layout = QHBoxLayout()
        self.software_triggered_btn = QPushButton("SLM triggered")
        self.software_triggered_btn.clicked.connect(self.set_camera_mode_software_triggered)
        camera_mode_layout.addWidget(self.software_triggered_btn, alignment=Qt.AlignCenter)
        self.live_feed_btn = QPushButton("Live feed")
        self.live_feed_btn.clicked.connect(self.set_camera_mode_live_feed)
        camera_mode_layout.addWidget(self.live_feed_btn, alignment=Qt.AlignCenter)
        camera_mode_layout.insertStretch(2, 2)
        camera_mode_layout.insertStretch(0, 2)
        camera_layout.addLayout(camera_mode_layout)

        # Number of object images input
        num_input_layout = QHBoxLayout()
        self.num_images_label = QLabel("Number of desired object images (integer ≥ 1):")
        self.num_images_label.setStyleSheet("color: black; font-weight: bold;")
        self.num_images_input = QLineEdit()
        self.num_images_input.setValidator(QIntValidator(1, 9999))
        self.num_images_input.setFixedWidth(60)
        num_input_layout.addWidget(self.num_images_label, alignment=Qt.AlignLeft)
        num_input_layout.addWidget(self.num_images_input, alignment=Qt.AlignLeft)
        num_input_layout.insertStretch(-1, -2)
        camera_layout.addLayout(num_input_layout)

        camera_widget = QWidget()
        camera_widget.setLayout(camera_layout)
        main_layout.addWidget(camera_widget, 0, 0)

        # Top-right: Controls + previews + buttons
        controls_layout = QVBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)

        # Reference preview
        self.iref_preview = ImageDisplay()
        self.iref_preview.setFixedSize(200, 200)
        self.iref_preview.setStyleSheet("border: 2px solid blue; background-color: #f0f0f0;")
        controls_layout.addWidget(QLabel("Reference Image Preview"), alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.iref_preview, alignment=Qt.AlignCenter)

        # Capture reference button
        self.capture_iref_btn = QPushButton("Capture Reference Image")
        self.capture_iref_btn.clicked.connect(self.capture_iref)
        controls_layout.addWidget(self.capture_iref_btn, alignment=Qt.AlignCenter)

        # Object previews
        obj_preview_layout = QHBoxLayout()

        self.first_obj_preview = ImageDisplay()
        self.first_obj_preview.setFixedSize(100, 100)
        self.first_obj_preview.setStyleSheet("border: 2px solid green; background-color: #f0f0f0;")
        obj_preview_layout.addWidget(self.first_obj_preview)
        
        self.last_obj_preview = ImageDisplay()
        self.last_obj_preview.setFixedSize(100, 100)
        self.last_obj_preview.setStyleSheet("border: 2px solid red; background-color: #f0f0f0;")
        obj_preview_layout.addWidget(self.last_obj_preview)

        controls_layout.addWidget(QLabel("Object Images (First / Last)"), alignment=Qt.AlignCenter)
        # Object count
        self.object_count_label = QLabel("Captured: 0")
        controls_layout.addWidget(self.object_count_label, alignment=Qt.AlignCenter)
        controls_layout.addLayout(obj_preview_layout)

        # Capture object button
        self.capture_obj_btn = QPushButton("Capture Object Images")
        self.capture_obj_btn.clicked.connect(self.capture_object)
        controls_layout.addWidget(self.capture_obj_btn, alignment=Qt.AlignCenter)

        # Process data button
        self.process_speckle_btn = QPushButton("Process Speckle Images")
        self.process_speckle_btn.clicked.connect(self.process_speckle)
        controls_layout.addWidget(self.process_speckle_btn, alignment=Qt.AlignBottom)

        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        main_layout.addWidget(controls_widget, 0, 1)

        # ---------- Bottom-left: Error / Status log ----------
        log_layout = QVBoxLayout()
        self.log_label = QLabel("Status / Error Log")
        self.log_label.setStyleSheet("color: black; font-weight: bold;")
        log_layout.addWidget(self.log_label, alignment=Qt.AlignBottom)
        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        self.error_log.setFixedHeight(150)
        log_layout.addWidget(self.error_log, alignment=Qt.AlignBottom)

        log_widget = QWidget()
        log_widget.setLayout(log_layout)
        main_layout.addWidget(log_widget, 1, 0)

        # ---------- Bottom-right: Biomass table ----------
        table_layout = QVBoxLayout()
        self.table_label = QLabel("Biomass Properties")
        self.table_label.setStyleSheet("color: black; font-weight: bold;")
        table_layout.addWidget(self.table_label, alignment=Qt.AlignBottom)

        self.biomass_table = QTableWidget(4, 2)
        self.biomass_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.biomass_table.setFixedSize(300, 150)

        for i in range(4):
            self.biomass_table.setItem(i, 0, QTableWidgetItem(f"Property {i+1}"))
            self.biomass_table.setItem(i, 1, QTableWidgetItem("---"))

        table_layout.addWidget(self.biomass_table, alignment=Qt.AlignCenter)

        table_widget = QWidget()
        table_widget.setLayout(table_layout)
        main_layout.addWidget(table_widget, 1, 1)

        # ---------- Plot Window ----------
        self.plot_window = PlotWindow()
        self.plot_window.show()

        # Camera handler + timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
        self.timer.start(30)  # ~30 FPS
    
    def log_error(self, message: str):
        # Append error message to the error log
        self.error_log.append(f"<span style='color: red;'>Warning: {message}</span>")

    def log_info(self, message: str):
        # Append status message to error log
        self.error_log.append(f"<span style='color: black;'>Status: {message}</span>")

    # Arms camera for image capturing, with settings assigned in camera_handler.py
    def activate_camera(self):
        if not self.camera or self.camera.camera is None:
            self.camera = CameraHandler()
            if self.camera.camera is None:
                self.log_error("No camera connection found")
                return
            self.log_info("Camera activated")
            self.log_info("Select operation mode")
        if not self.camera or self.camera.camera is not None:
            self.log_info("Camera already activated")
            self.log_info("Select operation mode")
        self.set_camera_status(self.camera.camera is not None)

    # Deactivates camera and image capturing
    def deactivate_camera(self):
        if not self.camera or self.camera.camera is not None:
            self.camera.release()
            self.set_camera_status(False)
            self.log_info("Camera deactivated")
        else:
            self.log_info("No camera to deactivate")

    # Updates status of camera connection in the GUI
    def set_camera_status(self, connected: bool):
        if connected:
            self.camera_status.setText("Camera connected")
            self.camera_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.camera_status.setText("Camera disconnected")
            self.camera_status.setStyleSheet("color: red; font-weight: bold;")

    # Sets operation mode of camera to live feed
    def set_camera_mode_live_feed(self):
        if not self.camera or self.camera.camera is None:
            self.log_error("No active camera. Please activate first")
            return
        if self.mode == "live":
            self.log_info("Camera already set to live feed")
        else:
            self.camera.arm_for_trigger("continuous")
            self.log_info("Camera set to live feed mode")
            self.mode = "live"

    # Sets operation mode of camera to software triggered
    def set_camera_mode_software_triggered(self):
        if not self.camera or self.camera.camera is None:
            self.log_error("No active camera. Please activate first.")
            return
        if self.mode == "SLM":
            self.log_info("Camera already set to SLM mode")
        else:
            self.camera.arm_for_trigger("software")
            self.log_info("Camera set to SLM mode")
            self.mode = "SLM"

    # Captures reference image
    def capture_iref(self):
        if not self.camera or self.camera.camera is None:
            self.log_error("Activate camera")
            return
        if self.mode != "live":
            self.log_error("Select live feed")
            return
        frame = self.camera.trigger_capture()
        if frame is not None:
            self.Iref = frame
            self.camera_display.set_image(frame)
            self.iref_preview.set_image(frame)    # show captured reference in preview box
            # self.log_info("Reference image captured")
             # Show shape of the frame (matrix size)
            h, w = frame.shape[:2]
            if frame.ndim == 3:
                c = frame.shape[2]
                self.log_info(f"{h}x{w} pixels, {c} channels")
            else:
                self.log_info(f"{h}x{w} pixels (grayscale)")

    # Captures object image and appends to object_images stack. 
    def capture_object(self):
        if not self.camera or self.camera.camera is None:
            self.log_error("No camera connected")
            return

        # if (self.mode != "live") or (self.mode != "SLM"):
        #     self.log_error("Select camera mode")
        #     return

        
        # ------ Placeholder for SLM sync ------
        # if self.mode == "SLM":
            #num_images = int(self.num_images_input.text() or 0)
            #if num_images <= 0:
                #self.log_error("Number of object images should be integer ≥ 1")
                #return

        #   for i in range(num_images):
        #       TODO: wait for SLM trigger or send SLM command here
        #       frame = self.camera.trigger_capture()
        #       self.object_images.append(frame)
        #
        #       if len(self.object_images) == 1:
        #           self.first_obj_preview.set_image(frame)
        #       elif len(self.object_images) == num_images:
        #           self.last_obj_preview.set_image(frame)
        #           self.log_info(f"Captured object frame #{len(self.object_images)}.")
        # ---------------------------------------
        # if self.mode == "SLM":
        #     self.log_error("SLM currently not synced")
        #     return

        if self.mode == "live":
            frame = self.camera.trigger_capture()
            if frame is not None:
                self.object_images.append(frame)
                self.camera_display.set_image(frame)
                self.object_count_label.setText(f"Captured: {len(self.object_images)}")

                # Update first and last previews
                if len(self.object_images) == 1:
                    self.first_obj_preview.set_image(frame)
                self.last_obj_preview.set_image(frame)

                self.log_info(f"Captured object frame #{len(self.object_images)}.")


    # Updates camera image displayed on GUI live feed
    def update_camera(self):
        frame = self.camera.trigger_capture()
        if frame is not None:
            self.camera_display.set_image(frame)
    
    def closeEvent(self, event):
        if self.camera:
            try:
                self.camera.release()
            except Exception as e:
                self.log_error(f"Error releasing camera: {e}")

        event.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QApplication.quit()
        else:
            super().keyPressEvent(event)

    # Uses ref image and object image stack to retrieve processed speckle data. Currently only displays displacement field
    def process_speckle(self):
        if self.Iref is None or len(self.object_images) == 0:
            self.log_error("Need reference and object stack")
            return

        # assume Iref captured as single frame but we want a stack for ref -> replicate or capture more frames
        Iref_stack = [self.Iref] * 10  # if you have only one ref; better capture N_ref frames
        Iobj_stack = self.object_images   # list of frames captured

        proc = SpeckleProcessor(M=64, n_workers=4)
        u_image, c_image, e_image, sc_image, rows, cols = proc.process(Iref_stack, Iobj_stack, method='mean')

        # visualize correlation map and vector field on your canvas
        U = np.real(u_image)
        V = np.imag(u_image)
        # draw quiver (use matplotlib axes in your MplCanvas)
        ax = self.canvas.ax
        ax.clear()
        ax.quiver(cols, rows, V, U)   # note mapping of axes depending on how rows/cols defined
        ax.set_title("Displacement (quiver)")
        self.canvas.draw()

