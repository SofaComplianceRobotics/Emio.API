import time
import logging
from emioapi.emioapi import emioapi

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main():
    initial_pos_pulse = [2048] * 4
    logger.info(f"Initial position in pulses: {initial_pos_pulse}")
    emioapi.printStatus()

    logging.info(emioapi.moving)

    emioapi.max_velocity = [1000] * 4
    time.sleep(1)
    new_pos = [1023] * 4
    logger.info(new_pos)
    emioapi.angles = new_pos

    emioapi.printStatus()
    time.sleep(1)
    emioapi.printStatus()
    new_pos = [3073] * 4
    logger.info(new_pos)
    emioapi.angles = new_pos
    time.sleep(1)
    emioapi.printStatus()
    emioapi.angles = initial_pos_pulse
    time.sleep(1)
    emioapi.printStatus()


if __name__ == "__main__":
    print("Ctrl-C to Stop")

    try:
        emioapi.openAndConfig()
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        emioapi.close()
