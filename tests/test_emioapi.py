import time
import logging
import pytest
from emioapi.emioapi import emioapi


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@pytest.fixture
def setupBefore():
    """Setup function to be called before each test."""
    emioapi.openAndConfig()
    logger.info("Setup complete.")

@pytest.fixture
def teardownAfter():
    """Teardown function to be called after each test."""
    emioapi.close()
    logger.info("Teardown complete.")

def test_main(setupBefore):

    initial_pos_pulse = [0] * 4
    logger.info(f"Initial position in pulses: {initial_pos_pulse}")
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
    assert (emioapi.angles == emioapi.angles) , "Motor did not return to initial position."


if __name__ == "__main__":
    try:
        pytest.main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        emioapi.close()
