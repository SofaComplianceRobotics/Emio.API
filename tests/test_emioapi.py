import time
import logging
import pytest
from emioapi import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


emio = EmioAPI()

def test_connection():
    """Setup function to be called before each test."""

    emio.connectToEmioDevice()

    assert EmioAPI.listUnusedEmioDevices() == EmioAPI.listEmioDevices-EmioAPI.listUsedEmioDevices(), "Unused devices found."

def test_main(setupBefore):

    initial_pos_pulse = [0] * 4
    logger.info(f"Initial position in pulses: {initial_pos_pulse}")
    emio.printStatus()

    emio.max_velocity = [1000] * 4
    time.sleep(1)
    new_pos = [3.14/8] * 4
    logger.info(new_pos)
    emio.angles = new_pos

    emio.printStatus()
    time.sleep(1)
    emio.printStatus()
    new_pos = [3.14/2] * 4
    logger.info(new_pos)
    emio.angles = new_pos
    logging.info(emio.moving)
    time.sleep(1)
    emio.printStatus()
    emio.angles = initial_pos_pulse
    time.sleep(1)
    emio.printStatus()
    assert (emio.angles == emio.angles) , "Motor did not return to initial position."


if __name__ == "__main__":
    try:
        pytest.main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        emio.close()
