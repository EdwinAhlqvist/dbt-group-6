# This script defines a class for setting up and handling data from a ThorLabs Scientific Camera.
# The script uses ThorLabs python toolkit package from their Windows SDK for Scientific Cameras.

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, OPERATION_MODE
import numpy as np

class CameraHandler:
    # Detects available cameras and defines settings
    def __init__(self):
        self.sdk = TLCameraSDK() # Creates a TLCameraSDK instance. Can only exist one at a time
        available_cameras = self.sdk.discover_available_cameras() # Checks for available camera connections
        if len(available_cameras) < 1:
            print("No cameras detected")
            self.camera = None
            self.sdk.dispose() # Disposes the TLCameraSDK instance if no connection is found
        else:
            self.camera = self.sdk.open_camera(available_cameras[0]) # Opens the first camera detected
            self.camera.exposure_time_us = 11000  # Set exposure to 11 ms
            self.camera.frames_per_trigger_zero_for_unlimited = 0  # Start camera in continuous mode
            self.camera.image_poll_timeout_ms = 1000  # 1 second polling timeout
            self.camera.arm(2) # Readies the camera with an image buffer of 2
            self.camera.issue_software_trigger()

    # Defines image data retrieval
    def get_frame(self):
        if self.camera is None:
            return None
        self.camera.issue_software_trigger()
        frame = self.camera.get_pending_frame_or_null() # Retrieves image from buffer if available
        if frame is not None:
            image_copy = np.copy(frame.image_buffer) # Copies image data from buffer
            return image_copy  # numpy array of pixel intensities
        return None

    # ---- Placeholder for SLM trigger ----
    # Sets operation mode of camera
    def arm_for_trigger(self, mode="software"):
        if self.camera is None:
            return False
        
        try:
            self.camera.disarm()
        except Exception:
            pass # If already disarmed
        
        if mode == "continuous":
            self.camera.operation_mode = OPERATION_MODE.SOFTWARE_TRIGGERED
            self.camera.exposure_time_us = 11000  # Set exposure to 11 ms
            self.camera.frames_per_trigger_zero_for_unlimited = 0  # Start camera in continuous mode
            self.camera.image_poll_timeout_ms = 1000  # 1 second polling timeout
            self.camera.arm(2)

        elif mode == "software":
            self.camera.operation_mode = OPERATION_MODE.SOFTWARE_TRIGGERED
            self.camera.exposure_time_us = 11000  # Set exposure to 11 ms
            self.camera.frames_per_trigger_zero_for_unlimited = 1  # Start camera with 1 frame per trigger
            self.camera.image_poll_timeout_ms = 1000  # 1 second polling timeout
            self.camera.arm(1)

        elif mode == "hardware":
            self.camera.operation_mode = OPERATION_MODE.HARDWARE_TRIGGERED
            self.camera.exposure_time_us = 11000  # Set exposure to 11 ms
            self.camera.frames_per_trigger_zero_for_unlimited = 1  # Start camera with 1 frame per trigger
            self.camera.image_poll_timeout_ms = 1000  # 1 second polling timeout
            self.camera.arm(1)

        else:
            raise ValueError(f"Unknown trigger mode: {mode}")
        
        return True
    
    def trigger_capture(self):
        """For software-triggered acquisition"""
        if self.camera is None:
            return None
        self.camera.issue_software_trigger()
        frame = self.camera.get_pending_frame_or_null()
        if frame is not None:
            image_copy = np.copy(frame.image_buffer)
            return image_copy
        
        # Possible to store like this
        # Convert buffer to numpy image
        # img = np.copy(frame.image_buffer).reshape(
        #     self.camera.image_height_pixels,
        #     self.camera.image_width_pixels
        # )
        # return img
    

        return None
    # ------------------------------------

    # Disarms the camera and disposes TLCameraSDK instance
    def release(self):
        if self.camera is not None:
            try:
                if self.camera.is_armed:
                    self.camera.disarm()
            except Exception:
                pass  # already disarmed

            try:
                self.camera.dispose()
            except Exception:
                pass  # already disposed

            self.camera = None

        if self.sdk is not None:
            try:
                self.sdk.dispose()
            except Exception:
                pass  # already disposed
            self.sdk = None
