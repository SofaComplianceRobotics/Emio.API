# Emio API

Emio API is a simple and easy-to-use API for controling the Emio robot.

## Installation
To install the Emio API, you can use pip:

```bash
python -m pip install emioapi
```

## Usage
The Emio API provides a single instance of the `Emio` class, which can be used to control the Emio robot. The API provides methods for controlling the robot's motors, sensors, and other features.
You can look at the [example.py](example.py) file for a simple example of how to use the API.

Simple example thaht sets the angles of the motors to 0 radians, waits for 1 second, and then prints the status of the robot:
```python
from emioapi import emio

# Open a port to the Emio robot and configure it
emio.openAndConfig()

emio.angles = [0] * 4  # Set the angles of the motors to 0 radians
time.sleep(1)  # Wait for 1 second
emio.printStatus() # Print the status of the robot
emio.close()  # Close the port to the Emio robot
```

## For Developers
To generate the documentation in a docs folder, you can use the following command:

```bash
python -m pydoc-markdown
```