from multiprocessing.managers import ListProxy
from multiprocessing.sharedctypes import Synchronized
from multiprocessing.managers import SyncManager
from multiprocessing.synchronize import Lock
from multiprocessing import Process
import multiprocessing
import logging
import time

import numpy as np

from ._depthcamera import DepthCamera

logger = logging.getLogger(__name__)


class EmioCamera:
    """
    A class to interface with the realsense camera on Emio.
    This class creates a process using mulltiprocessing to handle the camera.
    
    """
    _compute_point_cloud: Synchronized = None
    _show: Synchronized = None
    _camera_process: Process = None
    _manager: SyncManager = None
    _lock_camera: Lock  = None
    _trackers_pos: ListProxy = None
    _point_cloud: ListProxy = None
    _tracking: Synchronized = None
    _running: Synchronized = None
    _parameter: dict = {'hue_h': 176,
                'hue_l': 120,
                'sat_h': 255,
                'sat_l': 116,
                'value_h': 255,
                'value_l': 50,
                'erosion_size': 1,
                'area': 1,
                }
    _hsv_frame: ListProxy = None
    _mask_frame: ListProxy = None


    def __init__(self, camera_name=None, parameter=None, show=False, tracking=True, compute_point_cloud=False):
        """
        Initialize the camera.
        Args:
            camera_name: str: The name of the camera to connect to. If None, the first camera found will be used.
            parameter: dict:  The camera parameters. If None, the lastest save paramters are used from a file, but if no file is found, default values will be used.
            show: bool:  Whether to show the camera HSV and Mask frames or not.
            tracking: bool:  Whether to track objects or not.
            compute_point_cloud: bool: Whether to compute the point cloud or not.
        """
        multiprocessing.freeze_support()
        self._manager = multiprocessing.Manager()
        self._lock_camera = multiprocessing.Lock()
        self._trackers_pos = self._manager.list()
        self._point_cloud = self._manager.list()
        self._hsv_frame = self._manager.list()
        self._mask_frame = self._manager.list()
        self._running = multiprocessing.Value('b', False)
        self._tracking = multiprocessing.Value('b', tracking)
        self._show = multiprocessing.Value('b', show)
        self._compute_point_cloud = multiprocessing.Value('b', compute_point_cloud)
        if parameter is not None:
            self._parameter = parameter



    ##########################
    #  PROPERTIES
    ##########################



    @property
    def is_running(self):
        """
        Get the running status of the camera.
        Returns:
            bool: The running status of the camera.
        """
        return self._running.value
    

    @property
    def track_markers(self):
        """
        Get whether the camera is tracking objects or not.
        Returns:
            bool: True if the camera is tracking the markers, else False.
        """
        return self._tracking.value
    

    @track_markers.setter
    def track_markers(self, value):
        """
        Set the tracking status of the camera.
        Args:
            value: bool: The new tracking status.
        """
        self._tracking.value = value

    @property
    def compute_point_cloud(self):
        """
        Get whether the camera is computing the point cloud or not.
        Returns:
            bool: True if the camera is computing the point cloud, else False.
        """
        return self._compute_point_cloud.value
    

    @compute_point_cloud.setter
    def compute_point_cloud(self, value):
        """
        Set the point cloud computation status of the camera.
        Args:
            value: bool: The new point cloud computation status.
        """
        self._compute_point_cloud.value = value

    
    @property
    def show_frames(self):
        """
        Get the show status of the camera.
        Returns:
            bool: The show status of the camera.
        """
        return self._show.value
    

    @show_frames.setter
    def show_frames(self, value):
        """
        Set the show status of the camera.
        Args:
            value: bool: The new show status.
        """
        self._show.value = value
        logger.info(f"Show frames set to {self._show.value}")

    
    @property
    def parameters(self):
        """
        Get the camera parameters.
        Returns:
            dict: The camera parameters.
        """
        return self._parameter
    

    @parameters.setter
    def parameters(self, value):
        """
        Set the camera tracking parameters:
            - hue_h: int: The upper hue value.
            - hue_l: int: The lower hue value.
            - sat_h: int: The upper saturation value.
            - sat_l: int: The lower saturation value.
            - value_h: int: The upper value value.
            - value_l: int: The lower value value.
            - erosion_size: int: The size of the erosion kernel.
            - area: int: The minimum area of the detected objects.

        :::warning
        - The camera parameters are not saved to a file. You need to save them manually.
        - The paramters are set when opening the camera. To change the parameters programatically, you need to close the camera and open it again with the wanted parameters.
        :::

        Args:
            value: dict: The new camera parameters.
        """
        self._parameter = value
    

    @property
    def trackers_pos(self):
        """
        Get the positions of the trackers.
        Returns:
            list: The positions of the trackers as a list of lists.
        """
        with self._lock_camera:
            if self._tracking:
                return self._trackers_pos
            else:
                return []
    
    @property
    def point_cloud(self):
        """
        Get the point cloud data.
        Returns:
            The point cloud data as a numpy array.
        """
        with self._lock_camera:
            if self._compute_point_cloud:
                return self._point_cloud[0]
            else:
                return np.array([])

    
    @property
    def hsv_frame(self):
        """
        Get the HSV frame.
        Returns:
            The HSV frame as a numpy array.
        """
        with self._lock_camera:
            if self._hsv_frame:
                return self._hsv_frame[0]
            else:
                return None
    

    @property
    def mask_frame(self):
        """
        Get the mask frame.
        Returns:
            The mask frame as a numpy array.
        """
        with self._lock_camera:
            if self._mask_frame:
                return self._mask_frame[0]
            else:
                return None
            


    ##########################
    #  METHODS
    ##########################



    def __getstate__(self):
        """
        Get the state of the object for pickling.
        This method is used to remove the _manager attribute from the object state based on https://laszukdawid.com/blog/2017/12/13/multiprocessing-in-python-all-about-pickling/
        """
        self_dict = self.__dict__.copy()
        del self_dict['_manager']
        return self_dict

    def open(self) -> bool:
        """
        Initialize and open the camera in another process.
        This function creates a new process to handle the camera and starts it.
        """
        if self._running.value:
             self._camera_process.terminate()

        self._camera_process = Process(target=self._processCamera, args=(self._running, 
                                                                                         self._tracking, 
                                                                                         self._show, 
                                                                                         self._compute_point_cloud, 
                                                                                         self._trackers_pos, 
                                                                                         self._point_cloud, 
                                                                                         self._parameter,
                                                                                         self._hsv_frame,
                                                                                         self._mask_frame))
        self._camera_process.start()

        timeout = time.time() + 5

        while not self._running.value:
            time.sleep(0.5)
            if time.time() > timeout:
                logger.error("Camera process did not start within the timeout period. Exiting.")
                self.close()
                return False
            continue

        return True


    def _processCamera(self, running: Synchronized, tracking: Synchronized, show: Synchronized, 
                       compute_point_cloud: Synchronized, trackers_pos: ListProxy, 
                       point_cloud: ListProxy, parameter: dict=None, hsv_frame: ListProxy=None, mask_frame: ListProxy=None):
        """
        Process to handle the camera.
        This function runs in a separate process and updates the camera frames.
        Args:
            running: bool: A boolean indicating whether the camera is running or not.
            tracking: bool: A boolean indicating whether to track objects or not.
            show: bool: A boolean indicating whether to show the camera frames or not.
            trackersPos: list: A list to store the positions of the trackers.
            point_cloud: list: A list to store the point cloud data.
            parameter: dict: The camera parameters.
            hsv_frame: list: A list to store the HSV frame.
            mask_frame: list: A list to store the mask frame.
        """

        logger.debug("Starting camera process with show: {}, tracking: {}, compute_point_cloud: {}".format(show.value, tracking.value, compute_point_cloud.value))
        camera = DepthCamera(parameter=parameter, compute_point_cloud=compute_point_cloud.value, show_video_feed=show.value, tracking=tracking.value)
        running.value = True
        while running.value:
            camera.update()

            with self._lock_camera:
                del hsv_frame[:]
                hsv_frame.append(camera.hsvFrame)
                del mask_frame[:]
                mask_frame.append(camera.maskFrame)
                self._mask_frame = camera.maskFrame
                if tracking:
                    del trackers_pos[:]
                    trackers_pos.extend(camera.trackers_pos)
                if compute_point_cloud:
                        del point_cloud[:]
                        point_cloud.append(camera.point_cloud)
                

        camera.close()
        running.value = False

        
    def close(self):
        """
        Close the camera and terminate the process. Sets the running status to False.
        """
        self._running.value = False
        if self._camera_process.is_alive():
            self._camera_process.terminate()
