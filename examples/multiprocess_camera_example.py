#!/usr/bin/env -S uv run --script

import time
import logging
import sys
import os

import numpy as np

sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/..')
from emioapi import MultiprocessEmioCamera
from emioapi._logging_config import logger


def main():
    camera = MultiprocessEmioCamera()

    camera.show_frames = True # Show camera frames. Default is False.
    camera.track_markers = True # Track objects. Default is True.
    camera.compute_point_cloud = True # Compute point cloud. Default is False.

    # Camera tracking parameters. If None, a config file is read. If there is no config file, default values are used {"hue_h": 90, "hue_l": 36, "sat_h": 255, "sat_l": 138, "value_h": 255, "value_l": 35, "erosion_size": 0, "area": 100}
    camera.parameters = None 

    try:
        logger.info("List of available cameras: "+str(MultiprocessEmioCamera.listCameras()))

        if camera.open(): # Open the camera with the current parameters. This will start the camera process.
            logger.info(f"Camera {camera.camera_serial} opened successfully.")

            i = 0
            while i<20 and camera.is_running:
                time.sleep(1)
                try:
                    print("--" * 20)

                    print(camera._camera_process)
                    
                    # all properties of the emiocamera
                    logger.info(f"Camera parameters: {camera.parameters}")
                    logger.info(f"Camera show: {camera.show_frames}")
                    logger.info(f"Camera tracking: {camera.track_markers}")
                    logger.info(f"Camera compute point cloud: {camera.compute_point_cloud}")
                    logger.info(f"Camera is running: {camera.is_running}")
                    logger.info(f"Count tracker positions: {len(camera.trackers_pos)}")
                    logger.info(f"Point cloud shape: {camera.point_cloud.shape}")
                    logger.info(f"HSV Frame shape: {camera.hsv_frame.shape}")
                    logger.info(f"Mask Frame shape: {camera.mask_frame.shape}")

                    i += 1
                except Exception as e:
                    logger.info(f"An error occured while getting camera: {e}")
                    break

            camera.close()


    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Closing camera...")
        camera.close()
        return
    except Exception as e:
        logger.exception(f"Failed running camera: {e}")
        camera.close()
        return


if __name__ == "__main__":
    try:
        logger.info("Starting EMIO API test...")
        main()
        logger.info("EMIO API test completed successfully.")

    except Exception as e:
        logger.exception(f"An error occurred: {e}")