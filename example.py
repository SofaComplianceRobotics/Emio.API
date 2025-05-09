import time
import logging
from emioapi.emioapi import emioapi


logger = logging.getLogger(__name__)
# FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
# logging.basicConfig(format=FORMAT, level=logging.INFO)
logger.setLevel(logging.INFO)

def main(loops=1):

    initial_pos_pulse = [0] * 4
    emioapi.max_velocity = [1000] * 4
    logger.info(f"Initial position in rad: {initial_pos_pulse}")
    emioapi.angles = initial_pos_pulse
    time.sleep(1)
    emioapi.printStatus()


    for i in range(loops):
        new_pos = [((2*3.14)*((i+1)%8)/8)] * 4
        logger.info(f"new_pos {new_pos}")
        try:
            if emioapi.is_connected:
                emioapi.angles = new_pos
                time.sleep(1)
                emioapi.printStatus()
            else:
                emioapi.openAndConfig()
        except Exception as e:
            logger.error(f"Error during communication: {e}")
            emioapi.close()
            emioapi.openAndConfig()


if __name__ == "__main__":
    try:
        logger.info("Starting EMIO API test...")
        logger.info("Opening and configuring EMIO API...")
        if emioapi.openAndConfig():
            logger.info("EMIO API opened and configured.")
            logger.info("Running main function...")
            main(15)
            logger.info("Main function completed.")
            logger.info("Closing EMIO API...")
            emioapi.close()
            logger.info("EMIO API closed.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        emioapi.close()