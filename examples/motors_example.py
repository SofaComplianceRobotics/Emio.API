#!/usr/bin/env -S uv run --script

import time
import logging
from emioapi import EmioAPI
from emioapi.emiomotors import EmioMotors

logger = logging.getLogger(__name__)

def main(emio: EmioMotors, loops=1):

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
        
        emio_motors = EmioMotors()
        
        if emio_motors.open(): 
            
            emio_motors.printStatus()

            logger.info("Emio motors opened and configured.")
            logger.info("Running main function...")
            main(emio_motors, 15)

            logger.info("Main function completed.")
            logger.info("Closing Emio motor connection...")

            emio_motors.close()
            logger.info("EEmio connection closed.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        emio_motors.close()