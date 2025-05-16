#!/usr/bin/env -S uv run --script

import time
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/..')
from emioapi.emiocamera import EmioCamera

logger = logging.getLogger(__name__)

def main(emio: EmioCamera):

    while emio.is_running:
        try:
            emio.update() # update the camera frame and trackers

            print("-"*20)
            logger.info(f"Camera parameters: {emio.parameters}")
            logger.info(f"Camera show: {emio.show_frames}")
            logger.info(f"Camera tracking: {emio.track_markers}")
            logger.info(f"Camera compute point cloud: {emio.compute_point_cloud}")
            logger.info(f"Camera is running: {emio.is_running}")
            logger.info(f"Count tracker positions: {len(emio.trackers_pos)}")
            logger.info(f"Point cloud shape: {emio.point_cloud.shape}")
            logger.info(f"HSV Frame shape: {emio.hsv_frame.shape}")
            logger.info(f"Mask Frame shape: {emio.mask_frame.shape}")

        except KeyboardInterrupt: 
            logger.info("Keyboard interrupt received.")
            break
        except Exception as e:
            logger.exception(f"Error during communication: {e}")
            break


if __name__ == "__main__":
    try:
        logger.info("Starting EMIO API test...")
        logger.info("Opening and configuring EMIO API...")
        
        emio = EmioCamera(show=True, track_markers=True, compute_point_cloud=True)
        
        if emio.open():
            
            logger.info("Emio camera opened .")
            logger.info("Running main function...")
            main(emio)

            logger.info("Main function completed.")
            logger.info("Closing Emio API...")

            emio.close()

            logger.info("EMIO API closed.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")