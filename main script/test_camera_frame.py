import numpy as np
import os
import cv2
import sys
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, OPERATION_MODE

# Defines path to find dlls folder
def configure_path():
    is_64bits = sys.maxsize > 2**32
    # Relative path from active folder to dlls folder
    # NOTE: Current path is set according to a specific set of folder levels. Works if folder levels are kept as posted on GitLab.
    relative_path_to_dlls = '..' + os.sep + 'Scientific Camera Interfaces' + os.sep + 'SDK' + os.sep + 'Python Toolkit' + os.sep + 'dlls' + os.sep

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

try:
    # if on Windows, use the provided setup script to add the DLLs folder to the PATH
    from windows_setup import configure_path
    configure_path()
except ImportError:
    configure_path = None

with TLCameraSDK() as sdk:
    available_cameras = sdk.discover_available_cameras()
    if len(available_cameras) < 1:
        print("no cameras detected")

    with sdk.open_camera(available_cameras[0]) as camera:
        camera.exposure_time_us = 10000  # set exposure to 11 ms
        camera.frames_per_trigger_zero_for_unlimited = 0  # start camera in continuous mode
        camera.image_poll_timeout_ms = 1000  # 1 second polling timeout

        camera.arm(2)
        camera.issue_software_trigger()

        frame = camera.get_pending_frame_or_null()
        if frame is not None:
            print("frame #{} received!".format(frame.frame_count))
            frame.image_buffer
            image_buffer_copy = np.copy(frame.image_buffer)
            numpy_shaped_image = image_buffer_copy.reshape(camera.image_height_pixels, camera.image_width_pixels)
            nd_image_array = np.full((camera.image_height_pixels, camera.image_width_pixels, 3), 0, dtype=np.uint8)
            nd_image_array[:,:,0] = numpy_shaped_image
            nd_image_array[:,:,1] = numpy_shaped_image
            nd_image_array[:,:,2] = numpy_shaped_image
            
            cv2.imshow("Image From TSI Cam", nd_image_array)
        else:
            print("Unable to acquire image, program exiting...")
            exit()
            
        cv2.waitKey(0)
        camera.disarm()

#  Because we are using the 'with' statement context-manager, disposal has been taken care of.

print("program completed")