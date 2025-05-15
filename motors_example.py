import time
import logging
from emioapi import *

logger = logging.getLogger(__name__)

def main(emio: EmioAPI, loops=1):

    initial_pos_pulse = [0] * 4
    emio.motors.max_velocity = [1000] * 4
    logger.info(f"Initial position in rad: {initial_pos_pulse}")
    emio.motors.angles = initial_pos_pulse
    time.sleep(1)
    emio.printStatus()


    for i in range(loops):
        new_pos = [((2*3.14)*((i+1)%8)/8)] * 4
        logger.info(f"new_pos {new_pos}")
        try:
            if emio.motors.is_connected:
                emio.motors.angles = new_pos
                time.sleep(1)
                emio.motors.printStatus()
            else:
                emio.motors.open()
        except Exception as e:
            logger.error(f"Error during communication: {e}")
            emio.motors.close()
            emio.motors.open()


if __name__ == "__main__":
    try:
        logger.info("Starting EMIO API test...")
        logger.info("Opening and configuring EMIO API...")
        
        emio = EmioAPI()
        
        logger.info(EmioAPI.listEmioDevices())
        if emio.motors.open(): 
            logger.info(EmioAPI.listUnusedEmioDevices())
            
            emio.printStatus()

            logger.info("EMIO API opened and configured.")
            logger.info("Running main function...")
            main(emio, 15)

            logger.info("Main function completed.")
            logger.info("Closing EMIO API...")

            emio.motors.close()
            logger.info("EMIO API closed.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        emio.motors.close()