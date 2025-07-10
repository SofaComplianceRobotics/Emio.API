import time
import numpy as np
import cv2 as cv
import json
import os
import csv

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

def pixels_to_mm(depth, pixel_x, pixel_y, camera_intrinsics):
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
            The x value in mm
    Y : double
            The y value in mm
    Z : double
            The z value in mm

    """

    X = ((pixel_x - camera_intrinsics.ppx) / camera_intrinsics.fx) * depth
    Y = ((pixel_y - camera_intrinsics.ppy) / camera_intrinsics.fy) * depth
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

        self.absolute_positions=np.zeros((9, 3))
        self.R=np.zeros((9,3))
        self.t=np.zeros((3))
        self.intr= cameraintrinsinc if cameraintrinsinc else None
        self.points = []
        self.trackers_pos = []
        self.initialized = False
        self.count_calibration_frames = 0
        self.calibrationboard_size = (100.0, 3.0, 100.0)  # Size of the calibration board in meters

        hypotenuse = np.sqrt(self.calibrationboard_size[0]**2 + self.calibrationboard_size[2]**2)/2.0
        self.absolute_positions[0] = [-hypotenuse, self.calibrationboard_size[1], 0.0]
        self.absolute_positions[1] = [0.0, self.calibrationboard_size[1], -hypotenuse]
        self.absolute_positions[2] = [hypotenuse, self.calibrationboard_size[1], 0.0]
        self.absolute_positions[3] = [0.0, self.calibrationboard_size[1], hypotenuse]
        self.absolute_positions[4] = (self.absolute_positions[0] + self.absolute_positions[1]) /2.0
        self.absolute_positions[5] = (self.absolute_positions[1] + self.absolute_positions[2]) /2.0
        self.absolute_positions[6] = (self.absolute_positions[2] + self.absolute_positions[3]) /2.0
        self.absolute_positions[7] = (self.absolute_positions[3] + self.absolute_positions[0]) /2.0
        self.absolute_positions[8] = [0, self.calibrationboard_size[1], 0] # center of the calibration board

        logger.info(f"Absolute positions: {self.absolute_positions}")

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
            
    
    def mask_area(self, corners, frame):
        """
        Create a mask of an area defined by the corners of a polygon

        Paramaters
        ------------
        corners         : list[int]
                                                The list of corners of the area 
        frame           : numpy.ndarray
                                                The last color frame of the camera 

        Return:
        -----------
        mask            : numpy.ndarray                                        
                                                The masked frame with only the area visible, rest is black
        """
        frame_shape=frame.shape
        mask = np.zeros(frame_shape[:2], dtype=np.uint8)
        corners = np.array(corners, dtype=np.int32)
        cv.fillPoly(mask, [corners], 255)

        return mask
    

    def init_position_estimation(self):
        """
        Initialize the rotation matrix and the translation vector based ont the marker detected
        Does not initialize if the number of markers is incorrect, the ids of markers are incorrects, two ids are the same
        Marker used : dictionnary : DICT_ARUCO_ORIGINAL Ids: 0 to 7
        if a calibration is done write the necessary values to calculate those matrix and vector in a csv file
        If no calibration is done read the values of the csv file
                                            
        Return:
        -----------
        True if the calibration process is successful, False otherwise
        """
        ids=[]
        self.initialized = False
        self.trackers_pos = []
        self.points = []
        # If the calibration step is not require read the values of the last calibration process
        with open(CALIBRATION_FILENAME, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # skipp header
            for row in reader:
                self.points.append((int(row[0]), int(row[1])))
                self.trackers_pos.append(
                    pixels_to_mm(
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
        
        self.trackers_pos = np.array(self.trackers_pos)
        self.R, self.t = rigid_transform_3D( self.trackers_pos, self.absolute_positions)
        
        self.initialized = True
        return True

    def calibrate(self, frame, depth_image, window=None):
        """
        OLD METHOD:
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
            self.trackers_pos.append(pixels_to_mm(depth, x, y, self.intr))

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
    
    def calibrate_single_marker(self, frame, depth_image, aggregate, window=None):
        """
        Calibrate the camera by detecting a single marker and calculating the rotation matrix and translation vector.
        This method averages the corners positions of the marker and stores them in a CSV file.

        Parameters:
        -----------
        frame           : numpy.ndarray
                                                The color image returned by the camera
        depth_image     : numpy.ndarray         
                                                The depth image returned by the camera
        aggregate       : bool
                                                If True, the corners positions are aggregated over multiple frames
        window          : CameraFeedWindow
                                                The window to display the camera feed
        Return:
        -----------
        True if the calibration process is successful, False otherwise
        """
        dictionary = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_ARUCO_ORIGINAL)
        parameters =  cv.aruco.DetectorParameters()
        detector = cv.aruco.ArucoDetector(dictionary, parameters)
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        _,thresh_image = cv.threshold(gray,95,255,cv.THRESH_TOZERO)

        (corners, ids, rejected) = detector.detectMarkers(thresh_image)        

        logger.debug(f"Detected ids: {ids}")

        if ids is None:
            logger.error("No markers detected")
            return False
        if len(ids)>1:
            logger.error("More than one marker detected")
            return False
        if ids[0] != 672:
            logger.error(f"Marker ID is not 672: {ids}")
            return False
        
        if not aggregate:
            self.trackers_pos = np.zeros((9, 3))
            self.points = np.zeros((9, 2))  # Initialize points array with 5 points and 2 coordinates (x, y)
            self.count_calibration_frames = 0

        # Add the corners positions of the marker to the 2D points and trackers_pos lists
        temp_points = np.zeros((9, 2))
        temp_trackers_pos = np.zeros((9, 3))
        for i in range(len(corners[0][0])):
            corner=corners[0][0][i]
            depth= depth_image[int(corner[1])][int(corner[0])]
            if depth == 0:
                logger.error(f"Depth value is 0 for corner {i} at position ({corner[0]}, {corner[1]})")
                return False

            temp_points[i] = [corner[0], corner[1]]
            temp_trackers_pos[i] = pixels_to_mm(depth, corner[0], corner[1], self.intr)
        
        # Add the the middle points between the corners
        temp_points[4] = [(temp_points[0][0] + temp_points[1][0]) / 2, (temp_points[0][1] + temp_points[1][1]) / 2]
        temp_points[5] = [(temp_points[1][0] + temp_points[2][0]) / 2, (temp_points[1][1] + temp_points[2][1]) / 2]
        temp_points[6] = [(temp_points[2][0] + temp_points[3][0]) / 2, (temp_points[2][1] + temp_points[3][1]) / 2]
        temp_points[7] = [(temp_points[3][0] + temp_points[0][0]) / 2, (temp_points[3][1] + temp_points[0][1]) / 2]


        temp_trackers_pos[4] = [(temp_trackers_pos[0][0] + temp_trackers_pos[1][0]) / 2,
                                (temp_trackers_pos[0][1] + temp_trackers_pos[1][1]) / 2,
                                (temp_trackers_pos[0][2] + temp_trackers_pos[1][2]) / 2]
        temp_trackers_pos[5] = [(temp_trackers_pos[1][0] + temp_trackers_pos[2][0]) / 2,
                                (temp_trackers_pos[1][1] + temp_trackers_pos[2][1]) / 2,
                                (temp_trackers_pos[1][2] + temp_trackers_pos[2][2]) / 2]
        temp_trackers_pos[6] = [(temp_trackers_pos[2][0] + temp_trackers_pos[3][0]) / 2,
                                (temp_trackers_pos[2][1] + temp_trackers_pos[3][1]) / 2,
                                (temp_trackers_pos[2][2] + temp_trackers_pos[3][2]) / 2]
        temp_trackers_pos[7] = [(temp_trackers_pos[3][0] + temp_trackers_pos[0][0]) / 2,
                                (temp_trackers_pos[3][1] + temp_trackers_pos[0][1]) / 2,
                                (temp_trackers_pos[3][2] + temp_trackers_pos[0][2]) / 2]
        
        # Replace the last dimension with the actual depth
        for i in range(4, 8):
            depth = depth_image[int(temp_points[i][1])][int(temp_points[i][0])]
            if depth == 0:
                logger.error(f"Depth value is 0 for corner {i} at position ({temp_points[i][0]}, {temp_points[i][1]})")
                return False
            temp_trackers_pos[i][2] = depth

        # Average the corners positions
        x, y = np.mean(corners[0][0], axis=0)
        x = int(x)
        y = int(y)

        # Adds the center of the marker to the points and trackers_pos lists
        depth= depth_image[y][x]
        if depth == 0:
                logger.error(f"Depth value is 0 for corner {i} at position ({corner[0]}, {corner[1]})")
                return False
        temp_points[8] = [x, y]
        temp_trackers_pos[8] = pixels_to_mm(depth, x, y, self.intr)


        # If the calibration is not aggregated, reset the points and trackers_pos lists, else add the new points and trackers_pos to the existing lists
        self.points = temp_points if not aggregate else self.points + temp_points
        self.trackers_pos = temp_trackers_pos if not aggregate else self.trackers_pos + temp_trackers_pos

        self.count_calibration_frames += 1

        # Write the information in a CSV file for the next calibration processes
        points_2d = [(int(self.points[i][0]/self.count_calibration_frames), int(self.points[i][1]/self.count_calibration_frames), self.trackers_pos[i][2]/self.count_calibration_frames, ids[0][0]) for i in range(9)]
        with open(CALIBRATION_FILENAME, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['X', 'Y', 'Depth', 'id'])  # En-tête
            writer.writerows(points_2d)
            logger.debug(f"Calibration data written to {CALIBRATION_FILENAME}: {points_2d}")
        
        logger.debug(f"Number of calibration frames: {self.count_calibration_frames}")
        logger.debug(f"Aggregated Points: {self.points}")

         # Draw the detected markers and the corners on the frame
        cv.aruco.drawDetectedMarkers(frame, corners, ids, borderColor=(255, 0, 0))
        cv.circle(frame, (int(corners[0][0][1][0]), int(corners[0][0][1][1])), 2, (0, 0, 255), -1)
        cv.circle(frame, (int(corners[0][0][2][0]), int(corners[0][0][2][1])), 2, (0, 255, 0), -1)
        cv.circle(frame, (int(corners[0][0][3][0]), int(corners[0][0][3][1])), 2, (0, 255, 255), -1)
        # draw 2D points on the frame
        [cv.circle(frame, (int(points_2d[i][0]), int(points_2d[i][1])), 5, (0, 0, 255), 1) for i in range(9)]
        [cv.putText(frame, f"{i} ({int(corners[0][0][i][0])}, {int(corners[0][0][i][1])}, {depth_image[int(corners[0][0][i][1]),int(corners[0][0][i][0])]}) ", 
                        (int(corners[0][0][i][0]), int(corners[0][0][i][1])), 
                        cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1) for i in range(4)]
        
        if window:
            window.set_frame(frame)

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
        p = pixels_to_mm(depth, x, y, self.intr)
        position= self.R@p+self.t
        return [position[0], position[1]-305.5, position[2]]


