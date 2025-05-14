from multiprocessing.managers import ListProxy
from multiprocessing.sharedctypes import Synchronized
from ._depthcamera import DepthCamera
import multiprocessing
import logging
import time

logger = logging.getLogger(__name__)


class EmioCamera:
    """
    A class to interface with the realsense camera on Emio.
    This class creates a process using mulltiprocessing to handle the camera.
    
    """
    _manager = None
    _lockCamera = None
    _trackersPos = None
    tracking = True
    running = False
    show = False

    def __init__(self, camera_name=None, show=False, tracking=True):
        """
        Initialize the camera.
        Args:
            camera_name: The name of the camera to connect to. If None, the first camera found will be used.
            show: Whether to show the camera frames or not.
            tracking: Whether to track objects or not.
        """
        multiprocessing.freeze_support()
        self._manager = multiprocessing.Manager()
        self. _lockCamera = multiprocessing.Lock()
        self._trackersPos = self._manager.list()
        self.running = multiprocessing.Value('b', self.running)
        self.tracking = multiprocessing.Value('b', self.tracking)
        self.show = multiprocessing.Value('b', self.show)

    def __getstate__(self):
        """
        Get the state of the object for pickling.
        This method is used to remove the _manager attribute from the object state based on https://laszukdawid.com/blog/2017/12/13/multiprocessing-in-python-all-about-pickling/
        """
        self_dict = self.__dict__.copy()
        del self_dict['_manager']
        return self_dict

    def openCamera(self):
        """
        Initialize and open the camera in another process.
        This function creates a new process to handle the camera and starts it.
        """
        if self.running.value:
             self._camera_process.terminate()

        self._camera_process = multiprocessing.Process(target=self._processCamera, args=(self.running, self.tracking, self.show, self._trackersPos))
        # self._camera_process.start()

        timeout = time.time() + 5

        while not self.running.value:
            time.sleep(0.5)
            if time.time() > timeout:
                raise TimeoutError("Camera process did not start in time.")
            continue


    def _processCamera(self, running: Synchronized, tracking: Synchronized, show: Synchronized, trackersPos: ListProxy ):
        """
        Process to handle the camera.
        This function runs in a separate process and updates the camera frames.
        Args:
            running: A boolean indicating whether the camera is running or not.
            tracking: A boolean indicating whether to track objects or not.
            show: A boolean indicating whether to show the camera frames or not.
            trackersPos: A list to store the positions of the trackers.
        """
        camera = DepthCamera(comp_point_cloud=True, show_video_feed=show, tracking=tracking)
        running.value = True
        for _ in range(200):
            camera.update()
            del trackersPos[:]
            trackersPos.extend(camera.trackers_pos)

        camera.close()
        running.value = False

        
    def closeCamera(self):
        """
        Close the camera.
        """
        self.running.value = False
        if self._camera_process.is_alive():
            self._camera_process.terminate()


    @property
    def is_running(self):
        """
        Get the running status of the camera.
        Returns:
            The running status of the camera.
        """
        return self.running.value
    

    @property
    def track_markers(self):
        """
        Get the tracking status of the camera.
        Returns:
            The tracking status of the camera.
        """
        return self.tracking.value
    

    @track_markers.setter
    def track_markers(self, value):
        """
        Set the tracking status of the camera.
        Args:
            value: The new tracking status.
        """
        self.tracking.value = value


    @property
    def trackers_pos(self):
        """
        Get the positions of the trackers.
        Returns:
            The positions of the trackers.
        """
        return self._trackersPos
    
    @property
    def show_frames(self):
        """
        Get the show status of the camera.
        Returns:
            The show status of the camera.
        """
        return self.show.value
    

    @show_frames.setter
    def show_frames(self, value):
        """
        Set the show status of the camera.
        Args:
            value: The new show status.
        """
        self.show.value = value

    # get hsv frame

    # get mask frame

    # get point cloud

    # get camera parameters

