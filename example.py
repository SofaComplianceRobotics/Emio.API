import time
import logging
from emioapi.emioapi import emioapi


logger = logging.getLogger(__name__)
# FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
# logging.basicConfig(format=FORMAT, level=logging.INFO)
logger.setLevel(logging.INFO)

def main():

    initial_pos_pulse = [0] * 4
    logger.info(f"Initial position in rad: {initial_pos_pulse}")
    emioapi.printStatus()

    emioapi.max_velocity = [1000] * 4
    time.sleep(1)
    new_pos = [3.14/8] * 4
    logger.info(new_pos)
    emioapi.angles = new_pos

    emioapi.printStatus()
    time.sleep(1)
    emioapi.printStatus()
    new_pos = [3.14/2] * 4
    logger.info(new_pos)
    emioapi.angles = new_pos
    logging.info(emioapi.moving)
    time.sleep(1)
    emioapi.printStatus()
    emioapi.angles = initial_pos_pulse
    time.sleep(1)
    emioapi.printStatus()


if __name__ == "__main__":
    try:
        logger.info("Starting EMIO API test...")
        logger.info("Opening and configuring EMIO API...")
        emioapi.openAndConfig()
        logger.info("EMIO API opened and configured.")
        logger.info("Running main function...")
        main()
        logger.info("Main function completed.")
        logger.info("Closing EMIO API...")
        emioapi.close()
        logger.info("EMIO API closed.")
        logger.info("Reopening and reconfiguring EMIO API...")
        emioapi.openAndConfig()
        logger.info("EMIO API reopened and reconfigured.")
        logger.info("Running main function again...")
        main()
        logger.info("Main function completed again.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
    finally:
        emioapi.close()