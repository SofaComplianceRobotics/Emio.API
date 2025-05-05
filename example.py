import time
import logging
import emioapi

def main():
    initial_pos_pulse = [2048] * 4
    emioapi.printStatus()

    emioapi.setVelicityProfile([1000] * 4)
    time.sleep(1)
    new_pos = [1023] * 4
    logging.info(new_pos)
    emioapi.setGoalPosition(new_pos)
    # pos = (3.14,3.14,3.14)
    # Beams.setGoalPosition(LengthToPulse(pos))

    emioapi.printStatus()
    time.sleep(1)
    emioapi.printStatus()
    new_pos = [3073] * 4
    logging.info(new_pos)
    emioapi.setGoalPosition(new_pos)
    time.sleep(1)
    emioapi.printStatus()
    emioapi.setGoalPosition(initial_pos_pulse)
    time.sleep(1)
    emioapi.printStatus()


if __name__ == "__main__":
    print("Ctrl-C to Stop")

    try:
        emioapi.openAndConfig()
        main()
    except:
        print("problem detected")
    finally:
        emioapi.close()
