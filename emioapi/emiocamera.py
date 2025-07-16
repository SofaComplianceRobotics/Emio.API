import threading
import numpy as np

from emioapi._depthcamera import *
from emioapi._logging_config import logger


class EmioCamera:
    """
    A class to interface with the Realsense camera on Emio.
    This class opens the camera in the same process as the code is running from.

    It is recommendend to use this class if you want to use the camera in a SOFA scene.

    :::warning
    If you want to open the camera in another process, you can use the [MultiprocessEmioCamera](#MultiprocessEmioCamera) class.
    :::


    Example:
        ```python
        from emioapi import EmioCamera

        # Create an instance of EmioCamera
        camera = EmioCamera(show=True, track_markers=True, compute_point_cloud=True)

        # Open the camera
        if camera.open():
            try:
                while camera.is_running:
                    # Update camera frames and tracking
                    camera.update()

                    # Access tracker positions
                    positions = camera.trackers_pos
                    print("Tracker positions:", positions)

                    # Access point cloud data
                    pc = camera.point_cloud
                    print("Point cloud shape:", pc.shape)

                    # Access HSV and mask frames
                    hsv = camera.hsv_frame
                    mask = camera.mask_frame

                    # ... (process frames as needed)

                    # For demonstration, break after one iteration
                    break
            finally:
                # Close the camera when done
                camera.close()
        ```

    
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

    camera_serial: str = None


    def __init__(self, camera_serial=None, parameter=None, show=False, track_markers=True, compute_point_cloud=False):
        """
        Initialize the camera.
        Args:
            camera_serial: str: The serial number of the camera to connect to. If None, the first camera found will be used.
            parameter: dict:  The camera parameters. If None, the lastest save paramters are used from a file, but if no file is found, default values will be used.
            show: bool:  Whether to show the camera HSV and Mask frames or not.
            track_markers: bool:  Whether to track objects or not.
            compute_point_cloud: bool: Whether to compute the point cloud or not.
        """
        self.camera_serial = camera_serial
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
            
    @property
    def calibration_status(self) -> int:
        """
        Get the calibration status of the camera.
        Returns:
            int: The calibration status of the camera.
        """
        return self._camera.calibration_status
            


    ##########################
    #  METHODS
    ##########################


    @staticmethod
    def listCameras() -> list:
        """
        Static method to list all the Realsense cameras connected to the computer

        Returns:
            list: A list of the serial numbers as string.
        """
        return listCameras()
    
    @staticmethod
    def camera_to_emio(position: list) -> list:
        """
        Convert the real world position into the simulation pose of emio

        Args:
            position: list[float]: The position in camera frame

        Returns:
            list[float]: The position in the simulation frame 
        """
        # Convert the position from our frame to the simulation's frame
        qx=0
        qy=0
        qz=0
        qw=0
        pose=[position[0], position[1], position[2], qx, qy, qz, qw]

        return pose
    

    def open(self, camera_serial: str=None) -> bool:
        """
        Initialize and open the camera in another process.
        This function creates a new handle to the camera and starts it.

        Args:
            camera_serial: str: the serial number of the camera to open. If None, the first found Realsense camera will be opened. If the `camera_serial` was set as a parameter or before, the given camera will be opened.

        Returns:
            bool: True if a camera was opened, else False

        """

        try:
            if self._running:
                self.close()
                self._running = False

            if camera_serial is not None:
                self.camera_serial = camera_serial

            logger.debug("Starting camera with show: {}, tracking: {}, compute_point_cloud: {}".format(self._show, self._tracking, self._compute_point_cloud))
            self._camera = DepthCamera(camera_serial=self.camera_serial, parameter=self._parameter, 
                                compute_point_cloud=self._compute_point_cloud, 
                                show_video_feed=self._show, 
                                tracking=self._tracking)
            self.camera_serial = self._camera.camera_serial
            self._running = True
            logger.info(f"Camera {self.camera_serial} successfully started.")
            return True
        except Exception as e:
            if self._camera:
                self._camera.close()
            self._running = False
            logger.error("Error opening camera: "+str(e))
            return False
        
        
    def calibrate(self):
        """
        Calibrate the camera.

        """
        self._camera.calibrate()


    def update(self):
        """
            Update the camera frames and tracking elements (markers and point cloud)
        """
        self._camera.update()
        with self._lock:
            self._hsv_frame = self._camera.hsvFrame
            self._mask_frame = self._camera.maskFrame
            if self._tracking:
                self._trackers_pos = []
                for p_camera in self._camera.trackers_pos:
                    p_emio = EmioCamera.camera_to_emio(p_camera)
                    self._trackers_pos.append(p_emio[0:3])
                logger.debug(f"Trackers positions in camera frame: {self._camera.trackers_pos}, converted to Emio frame: {self._trackers_pos}")
            if self._compute_point_cloud:
                    self._point_cloud = self._camera.point_cloud
        
    def close(self):
        """
        Close the camera and terminate the process. Sets the running status to False.
        """
        self._running = False
        if self._camera is not None: 
            self._camera.close()
