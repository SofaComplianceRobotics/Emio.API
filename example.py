import time
import logging
from emioapi import emio


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main(loops=1):

    initial_pos_pulse = [0] * 4
    emio.max_velocity = [1000] * 4
    logger.info(f"Initial position in rad: {initial_pos_pulse}")
    emio.angles = initial_pos_pulse
    time.sleep(1)
    emio.printStatus()


    for i in range(loops):
        new_pos = [((2*3.14)*((i+1)%8)/8)] * 4
        logger.info(f"new_pos {new_pos}")
        try:
            if emio.is_connected:
                emio.angles = new_pos
                time.sleep(1)
                emio.printStatus()
            else:
                emio.openAndConfig()
        except Exception as e:
            logger.error(f"Error during communication: {e}")
            emio.close()
            emio.openAndConfig()


if __name__ == "__main__":
    try:
        logger.info("Starting EMIO API test...")
        logger.info("Opening and configuring EMIO API...")
        if emio.openAndConfig():
            emio.printStatus()
            logger.info("EMIO API opened and configured.")
            logger.info("Running main function...")
            main(15)
            logger.info("Main function completed.")
            logger.info("Closing EMIO API...")
            emio.close()
            logger.info("EMIO API closed.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        emio.close()