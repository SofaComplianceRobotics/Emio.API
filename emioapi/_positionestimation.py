import time
import numpy as np
import cv2 as cv
import json
import os
import csv  # Added import for CSV functionality

import logging
FORMAT = "[%(levelname)s]\t[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_FILENAME = os.path.dirname(__file__) + '/cameraparameter.json'
CALIBRATION_FILENAME = os.path.dirname(__file__) + '/camera_2d_points.csv'


def rigid_transform_3D(image_cloud, absolute_cloud):
    """
    Find the translation vector and the rotation matrix between 2 points clouds
    

    Parameters:
    -----------
    image_cloud         : numpy.ndarray
                                            The points cloud in the camera space
    absolute_cloud      : numpy.ndarray
                                            The points cloud in the our frame space space

    Return:
    -----------
    R                   : numpy.ndarray
                                            The rotation matrix between the clouds
    t                   : numpy.ndarray 
                                            The translation vector between the clouds
    """
    assert image_cloud.shape == absolute_cloud.shape
    N = image_cloud.shape[0]

    centroid_A = np.mean(image_cloud, axis=0)
    centroid_B = np.mean(absolute_cloud, axis=0)

    AA = image_cloud - centroid_A
    BB = absolute_cloud - centroid_B

    H = AA.T @ BB
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    if np.linalg.det(R) < 0:
        Vt[2, :] *= -1
        R = Vt.T @ U.T

    t = centroid_B.T - R @ centroid_A.T
    return R, t

def convert_depth_pixel_to_metric_coordinate(depth, pixel_x, pixel_y, camera_intrinsics):
    """
    Convert the depth and image point information to metric coordinates

    Parameters:
    -----------
    depth 	 	 	 : double
                                               The depth value of the image point
    pixel_x 	  	 	 : double
                                               The x value of the image coordinate
    pixel_y 	  	 	 : double
                                                    The y value of the image coordinate
    camera_intrinsics : The intrinsic values of the imager in whose coordinate
                        system the depth_frame is computed

        Return:
    ----------
    X : double
            The x value in meters
    Y : double
            The y value in meters
    Z : double
            The z value in meters

    """

    X = (pixel_x - camera_intrinsics.ppx) / camera_intrinsics.fx * depth
    Y = (pixel_y - camera_intrinsics.ppy) / camera_intrinsics.fy * depth
    return [X, Y, depth]

def compute_cdg(contour):
    """
    Return the center of the contour

    Parameter:
    ------------
    contour         : cv object list[list[int]]
                                                The contour of the marker
    
    Return:
    -----------
    cX,cY           : int
                                                The center of the contour pixel coordinates
    """
    M = cv.moments(contour)
    cX = 0
    cY = 0
    if M['m00'] != 0:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
    return cX, cY

    

class PositionEstimation:
    """
    This class is used to calculate the real world coordinates based on the pixel coordinates and the depth
    """

    def __init__(self, cameraintrinsinc) -> None:
        """
        Initialize the class
        """

        self.absolute_positions=np.zeros((8, 3))
        self.R=np.zeros((3,3))
        self.t=np.zeros((3))
        self.intr= cameraintrinsinc if cameraintrinsinc else None
        self.points = []
        self.trackers_pos = []
        self.initialized = False

        try:
            with open(CONFIG_FILENAME, 'r') as fp:
                self.parameter = json.load(fp)

        except FileNotFoundError:
            self.parameter = {'hue_h': 90,
                                    'hue_l': 36,
                                    'sat_h': 255,
                                    'sat_l': 100,
                                    'value_h': 255,
                                    'value_l': 35,
                                    'erosion_size': 1,
                                    'area': 1,
                                    }    
    
    
    def init_absolute_pose(self, ids):
        """
        Attribute to each ArUco marker detected an absolute position based on its id

        Parameter:
        -----------
        ids             : list[list[int]]
                                                The ids of all ArUco markers detected
        """
        size_x=8.0
        size_y=10.0
        size_z=4.0
        for i in range(len(self.trackers_pos)):
            id_bin=format(ids[i][0], '03b')
            self.absolute_positions[i]=np.array([(int(id_bin[2])&1)*size_x, (int(id_bin[1])&1)*size_y, (int(id_bin[0])&1)*size_z])

    
    def get_marker_mask(self, corners, frame):
        """
        Create a mask of the ArUco marker

        Paramaters
        ------------
        corners         : list[int]
                                                The list of corners of an ArUco marker
        frame           : numpy.ndarray
                                                The last color frame of the camera 

        Return:
        -----------
        mask            : numpy.ndarray                                        
                                                The mask of the ArUco marker
        """
        frame_shape=frame.shape
        mask = np.zeros(frame_shape[:2], dtype=np.uint8)
        corners = np.array(corners, dtype=np.int32)
        cv.fillPoly(mask, [corners], 255)

        return mask

    def get_depth(self, mask, depth_image):
        """
        Calculate the median depth of the valid pixel in the mask

        Parameters:
        -----------
        mask            : numpy.ndarray
                                                The binary mask where the valid depth are white
        depth_image     : numpy.ndarray
                                                The depth image

        Returns:
        --------
        median_depth          : float
                                                The median depth of th mask
        """

        # Extraire les pixels de profondeur correspondant au marqueur
        depth_values = depth_image[mask == 255]

        # Filtrer les valeurs non valides (par exemple, 0 ou NaN)
        valid_depth_values = depth_values[depth_values > 0]

        if len(valid_depth_values) > 0:
            # Calculer la médiane des valeurs de profondeur valides
            median_depth = np.median(valid_depth_values)/10

        else:
            # Si aucune profondeur valide n'est trouvée, ajouter None
            return None

        return median_depth
    

    def init_position_estimation(self,frame, depth_image, calib):
        """
        Initialize the rotation matrix and the translation vector based ont the marker detected
        Does not initialize if the number of markers is incorrect, the ids of markers are incorrects, two ids are the same
        Marker used : dictionnary : DICT_ARUCO_ORIGINAL Ids: 0 to 7
        if a calibration is done write the necessary values to calculate those matrix and vector in a csv file
        If no calibration is done read the values of the csv file

        Parameters:
        -----------
        frame           : numpy.ndarray
                                                The color image returned by the camera
        depth_image     : numpy.ndarray         
                                                The depth image returned by the camera
        calib           : bool
                                                True if a calibration step is wanted, False otherwise
                                            
        Return:
        -----------
        True if the calibration process is successful, False otherwise
        """
        ids=[]
        self.initialized = False
        self.trackers_pos = []
        # If the calibration step is not require read the values of the last calibration process
        with open(CALIBRATION_FILENAME, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # skipp header
            for row in reader:
                self.points.append((int(row[0]), int(row[1])))
                self.trackers_pos.append(
                    convert_depth_pixel_to_metric_coordinate(
                        float(row[2]),  # depth
                        int(row[0]),  #  X coordinate
                        int(row[1]),  #  Y coordinate
                        self.intr
                    ))
                ids.append([int(row[3])])   
            self.initialized = True
        
        logger.debug(f"{self.initialized}. Trackers positions from config file: {self.trackers_pos}")

        if not self.initialized:
            return False
        
        self.init_absolute_pose(ids)
        self.trackers_pos = np.array(self.trackers_pos)
        self.R, self.t = rigid_transform_3D( self.trackers_pos, self.absolute_positions)
        
        self.initialized = True
        return True

    def calibrate(self, frame, depth_image, window=None):
        """
        Calibrate the camera by detecting the markers and calculating the rotation matrix and translation vector

        Parameters:
        -----------
        frame           : numpy.ndarray
                                                The color image returned by the camera
        depth_image     : numpy.ndarray         
                                                The depth image returned by the camera

        Return:
        -----------
        True if the calibration process is successful, False otherwise
        """
        error = True
        counted=[0, 0, 0, 0, 0, 0, 0, 0]
        aruco_marker_side_length = 0.01
        dictionary = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_ARUCO_ORIGINAL)
        parameters =  cv.aruco.DetectorParameters()
        detector = cv.aruco.ArucoDetector(dictionary, parameters)
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        _,thresh_image = cv.threshold(gray,95,255,cv.THRESH_TOZERO)

        (corners, ids, rejected) = detector.detectMarkers(thresh_image)
        cv.aruco.drawDetectedMarkers(frame, corners, ids, borderColor=(255, 0, 0))

        # cv.imshow("markers", frame)
        if window:
            window.set_frame(frame)

        if ids is None:
            logger.error("No markers detected")
            return False
        if len(ids)<8:
            logger.error("Less than 8 markers detected")
            return False
        if len(ids)>8:
            logger.error("More than 8 markers detected")
            return False
        for id in ids:
            if id[0]>7:
                logger.error("Non valid marker ID detected")
                return False
            if counted[id[0]]==1:
                logger.error("Multiple markers with the same ID detected")
                return False
            counted[id[0]]=1

        self.trackers_pos = []
        self.points = []

        
        for i in range(len(ids)):
            corner=corners[i]
            mask=self.get_marker_mask(corner, frame)
            depth=self.get_depth(mask, depth_image)
            x = int((corner[0][0][0] + corner[0][1][0] + corner[0][2][0] + corner[0][3][0]) / 4)
            y = int((corner[0][0][1] + corner[0][1][1] + corner[0][2][1] + corner[0][3][1]) / 4)
            self.points.append((x, y))
            self.trackers_pos.append(convert_depth_pixel_to_metric_coordinate(depth, x, y, self.intr))

        for p in self.trackers_pos:
            if p[2]<5:
                logger.error("At least one depth is not known")
                return False
          
        logger.debug(f"Trackers {self.trackers_pos}")

        # Write the information in a CSV file for the next calibration processes
        points_2d = [(int(self.points[i][0]), int(self.points[i][1]), self.trackers_pos[i][2], ids[i][0]) for i in range(len(self.trackers_pos))]
        with open(CALIBRATION_FILENAME, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['X', 'Y', 'Depth', 'id'])  # En-tête
            writer.writerows(points_2d)
            logger.debug(f"Calibration data written to {CALIBRATION_FILENAME}: {points_2d}")

        return True

    
    def image_to_3D(self, x, y, depth):
        """
        Calculate the position of the object in our frame space

        Parameters:
        x,y             : int
                                                The pixel coordinates
        depth           : float
                                                The depth of the pixel

        Return:
        -----------
        True if the position was correctly calculated, False otherwise

        position        : numpy.ndarray
                                                The real world coordinates
        """
        position=np.zeros((3))
        p = convert_depth_pixel_to_metric_coordinate(depth, x, y, self.intr)
        position= self.R@p+self.t
        return position


