#!/usr/bin/env -S uv run --script

import time
import logging

import numpy as np

from emioapi.emioapi import EmioAPI

FORMAT = "[%(levelname)s]\t[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    emio = EmioAPI()

    emio.camera.show_frames = False # Show camera frames. Default is False.
    emio.camera.track_markers = True # Track objects. Default is True.
    emio.camera.compute_point_cloud = True # Compute point cloud. Default is False.

    # Camera tracking parameters. If None, a config file is read. If there is no config file, default values are used {"hue_h": 90, "hue_l": 36, "sat_h": 255, "sat_l": 138, "value_h": 255, "value_l": 35, "erosion_size": 0, "area": 100}
    emio.camera.parameters = None 

    try:
        if emio.camera.open(): # Open the camera with the current parameters. This will start the camera process.
            logger.info("Camera opened successfully.")

            i = 0
            while i<20:
                time.sleep(1)
                print("--" * 20)
                # all properties of the emiocamera
                logger.info(f"Camera parameters: {emio.camera.parameters}")
                logger.info(f"Camera show: {emio.camera.show_frames}")
                logger.info(f"Camera tracking: {emio.camera.track_markers}")
                logger.info(f"Camera compute point cloud: {emio.camera.compute_point_cloud}")
                logger.info(f"Camera is running: {emio.camera.is_running}")
                logger.info(f"Count tracker positions: {len(emio.camera.trackers_pos)}")
                logger.info(f"Point cloud shape: {emio.camera.point_cloud.shape}")
                logger.info(f"HSV Frame shape: {emio.camera.hsv_frame.shape}")
                logger.info(f"Mask Frame shape: {emio.camera.mask_frame.shape}")

                i += 1


    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Closing camera...")
        emio.camera.close()
        return
    except Exception as e:
        logger.exception(f"Failed running camera: {e}")
        emio.camera.close()
        return


if __name__ == "__main__":
    try:
        logger.info("Starting EMIO API test...")
        main()
        logger.info("EMIO API test completed successfully.")

    except Exception as e:
        logger.exception(f"An error occurred: {e}")