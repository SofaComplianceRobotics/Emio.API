import time
import logging
import pytest
from emioapi.emioapi import EmioAPI


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@pytest.fixture
def setupBefore():
    """Setup function to be called before each test."""
    EmioAPI.openAndConfig()
    logger.info("Setup complete.")

@pytest.fixture
def teardownAfter():
    """Teardown function to be called after each test."""
    EmioAPI.close()
    logger.info("Teardown complete.")

def test_main(setupBefore):

    initial_pos_pulse = [0] * 4
    logger.info(f"Initial position in pulses: {initial_pos_pulse}")
    EmioAPI.printStatus()

    EmioAPI.max_velocity = [1000] * 4
    time.sleep(1)
    new_pos = [3.14/8] * 4
    logger.info(new_pos)
    EmioAPI.angles = new_pos

    EmioAPI.printStatus()
    time.sleep(1)
    EmioAPI.printStatus()
    new_pos = [3.14/2] * 4
    logger.info(new_pos)
    EmioAPI.angles = new_pos
    logging.info(EmioAPI.moving)
    time.sleep(1)
    EmioAPI.printStatus()
    EmioAPI.angles = initial_pos_pulse
    time.sleep(1)
    EmioAPI.printStatus()
    assert (EmioAPI.angles == EmioAPI.angles) , "Motor did not return to initial position."


if __name__ == "__main__":
    try:
        pytest.main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        EmioAPI.close()
