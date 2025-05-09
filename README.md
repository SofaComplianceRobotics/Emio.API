# Emio API

Emio API is a simple and easy-to-use API for controling the Emio robot.

## Installation
To install the Emio API, you can use pip:

```bash
pip install emioapi
```

## Usage
The Emio API provides a single instance of the `Emio` class, which can be used to control the Emio robot. The API provides methods for controlling the robot's motors, sensors, and other features.
You can look at the [example.py](example.py) file for a simple example of how to use the API.

```python
from emioapi.emioapi import emioapi

# Open a port to the Emio robot and configure it
emioapi.openAndConfig()

emioapi.angles = [0] * 4  # Set the angles of the motors to 0 radians
time.sleep(1)  # Wait for 1 second
emioapi.printStatus() # Print the status of the robot
emioapi.close()  # Close the port to the Emio robot
```

