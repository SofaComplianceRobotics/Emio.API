import time
import logging

from emioapi.emioapi import EmioAPI

FORMAT = "[%(levelname)s]\t[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main(loops=1):
    emio = EmioAPI()
    emio.camera.show_frames = True

    try:
        emio.camera.openCamera()
        logger.info("Camera opened successfully.")

        while emio.camera.is_running:
            time.sleep(1)
            logger.info(f"Tracker positions: {emio.camera.trackers_pos}")

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Closing camera...")
        emio.camera.closeCamera()
        return
    except Exception as e:
        logger.exception(f"Failed running camera: {e}")
        emio.camera.closeCamera()
        return


if __name__ == "__main__":
    try:
        logger.info("Starting EMIO API test...")
        main()
        logger.info("EMIO API test completed successfully.")

    except Exception as e:
        logger.exception(f"An error occurred: {e}")