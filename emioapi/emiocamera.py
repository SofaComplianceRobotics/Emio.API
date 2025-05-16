import threading
import logging
import time

import numpy as np

from ._depthcamera import DepthCamera

FORMAT = "[%(levelname)s]\t[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)


class EmioCamera:
    """
    A class to interface with the Realsense camera on Emio.
    This class opens the camera in the same process as the code is running from.

    It is recommendend to use this class if you want to use the camera in a SOFA scene.

    :::warning
    If you want to open the camera in another process, you can use the [MultiprocessEmioCamera](#MultiprocessEmioCamera) class.
    :::

    
    """
    _lock = threading.Lock()
    _compute_point_cloud: bool = False
    _camera: DepthCamera = None
    _tracking: bool = True
    _running: bool = False
    _parameter: dict = None
    _trackers_pos: list = []
    _point_cloud: np.ndarray = None
    _hsv_frame: np.ndarray = None
    _mask_frame: np.ndarray = None


    def __init__(self, camera_name=None, parameter=None, show=False, track_markers=True, compute_point_cloud=False):
        """
        Initialize the camera.
        Args:
            camera_name: str: The name of the camera to connect to. If None, the first camera found will be used.
            parameter: dict:  The camera parameters. If None, the lastest save paramters are used from a file, but if no file is found, default values will be used.
            show: bool:  Whether to show the camera HSV and Mask frames or not.
            track_markers: bool:  Whether to track objects or not.
            compute_point_cloud: bool: Whether to compute the point cloud or not.
        """
        self._tracking = track_markers
        self._show = show
        self._compute_point_cloud = compute_point_cloud
        if parameter is not None:
            self._parameter = parameter



    ##########################
    #  PROPERTIES
    ##########################



    @property
    def is_running(self) -> bool:
        """
        Get the running status of the camera.
        Returns:
            bool: The running status of the camera.
        """
        return self._running
    

    @property
    def track_markers(self) -> bool:
        """
        Get whether the camera is tracking objects or not.
        Returns:
            bool: True if the camera is tracking the markers, else False.
        """
        return self._tracking
    

    @track_markers.setter
    def track_markers(self, value: bool):
        """
        Set the tracking status of the camera.
        Args:
            value: bool: The new tracking status.
        """
        self._tracking = value

    @property
    def compute_point_cloud(self) -> bool:
        """
        Get whether the camera is computing the point cloud or not.
        Returns:
            bool: True if the camera is computing the point cloud, else False.
        """
        return self._compute_point_cloud
    

    @compute_point_cloud.setter
    def compute_point_cloud(self, value: bool):
        """
        Set the point cloud computation status of the camera.
        Args:
            value: bool: The new point cloud computation status.
        """
        self._compute_point_cloud = value

    
    @property
    def show_frames(self) -> bool:
        """
        Get whether the camera HSV and mask frames are shown in windows.
        Returns:
            bool: The show status of the camera.
        """
        if self._camera is not None:
            self._show = self._camera.show_video_feed
        return self._show
    

    @show_frames.setter
    def show_frames(self, value: bool):
        """
        Set the show status of the camera.
        Args:
            value: bool: The new show status.
        """
        self._show = value
        if self._camera is not None:
            self._camera.show_video_feed = value

    
    @property
    def parameters(self) -> dict:
        """
        Get the camera parameters in a dict object:
            - `hue_h`: int: The upper hue value.
            - `hue_l`: int: The lower hue value.
            - `sat_h`: int: The upper saturation value.
            - `sat_l`: int: The lower saturation value.
            - `value_h`: int: The upper value value.
            - `value_l`: int: The lower value value.
            - `erosion_size`: int: The size of the erosion kernel.
            - `area`: int: The minimum area of the detected objects.
        Returns:
            dict: The camera parameters.
        """
        return self._camera.parameter
    

    @parameters.setter
    def parameters(self, value: dict):
        """
        Set the camera tracking parameters from the dict object:
            - `hue_h`: int: The upper hue value.
            - `hue_l`: int: The lower hue value.
            - `sat_h`: int: The upper saturation value.
            - `sat_l`: int: The lower saturation value.
            - `value_h`: int: The upper value value.
            - `value_l`: int: The lower value value.
            - `erosion_size`: int: The size of the erosion kernel.
            - `area`: int: The minimum area of the detected objects.

        :::warning
        - The camera parameters are not saved to a file. You need to save them manually.
        - The paramters are set when opening the camera. To change the parameters programatically, you need to close the camera and open it again with the wanted parameters.
        :::

        Args:
            value: dict: The new camera parameters.
        """
        self._parameter = value
    

    @property
    def trackers_pos(self) -> list:
        """
        Get the positions of the trackers.
        Returns:
            list: The positions of the trackers as a list of lists.
        """
        with self._lock:
            if self._tracking:
                return self._trackers_pos
            else:
                return []
    
    @property
    def point_cloud(self) -> np.ndarray:
        """
        Get the point cloud data.
        Returns:
            The point cloud data as a numpy array.
        """
        with self._lock:
            if self._compute_point_cloud:
                return self._point_cloud
            else:
                return np.array([])

    
    @property
    def hsv_frame(self) -> np.ndarray:
        """
        Get the HSV frame.
        Returns:
            The HSV frame as a numpy array.
        """
        with self._lock:
            if self._hsv_frame is not None:
                return self._hsv_frame
            else:
                return None
    

    @property
    def mask_frame(self) -> np.ndarray:
        """
        Get the mask frame.
        Returns:
            The mask frame as a numpy array.
        """
        with self._lock:
            if self._mask_frame is not None:
                return self._mask_frame
            else:
                return None
            


    ##########################
    #  METHODS
    ##########################



    def open(self) -> bool:
        """
        Initialize and open the camera in another process.
        This function creates a new process to handle the camera and starts it.
        """

        try:
            if self._running:
                self.close()
                self._running = False

            logger.debug("Starting camera with show: {}, tracking: {}, compute_point_cloud: {}".format(self._show, self._tracking, self._compute_point_cloud))
            self._camera = DepthCamera(parameter=self._parameter, 
                                compute_point_cloud=self._compute_point_cloud, 
                                show_video_feed=self._show, 
                                tracking=self._tracking)
            self._running = True
            logger.info("Camera successfully started.")
            return True
        except Exception as e:
            if self._camera:
                self._camera.close()
            self._running = False
            logger.error("Error opening camera: "+str(e))
            return False

    def update(self):
        """
            Update the camera frames and tracking elements (markers and point cloud)
        """
        self._camera.update()
        with self._lock:
            self._hsv_frame = self._camera.hsvFrame
            self._mask_frame = self._camera.maskFrame
            if self._tracking:
                self._trackers_pos = self._camera.trackers_pos
            if self._compute_point_cloud:
                    self._point_cloud = self._camera.point_cloud
        
    def close(self):
        """
        Close the camera and terminate the process. Sets the running status to False.
        """
        self._running = False
        self._camera.close()
