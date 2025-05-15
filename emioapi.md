<a id="emioapi.emioapi"></a>

# emioapi.emioapi

<a id="emioapi.emioapi.EmioAPI"></a>

## EmioAPI

```python
class EmioAPI()
```

Class to control emio motors. 
It is essentially divided into two objects:
- The `motors` object (`EmioMotors` class), which is used to control the motors.
- The `camera` object (`EmioCamera` class), which is used to control the camera.

The EmioAPI class is the main class that combines both classes and provides a simple interface to control the emio device.
It also provides static utility methods to list the emio devices connected to the computer.

Motors:
    > The motors are controlled in position mode. The class is thread-safe and can be used in a multi-threaded environment.
    > All the data sent to the motors are list of *4 values* for the *4 motors* of the emio device. The order in the list corresponds to the motor ID's in the emio device.
    > Motor 0 is the first motor in the list, motor 1 is the second motor, etc.
    > You can open a connection directly to the motors using the `open` method of the `motors` object.
    > 
    > :::warning 
    > 
    > Emio motors are clamped between 0 and PI radians (0 and 180 degrees). If you input a value outside this range, the motor will not move.
    > 
    > :::

Camera:
    > The camera is controlled in a separate process. The camera is used to track objects and compute the point cloud.
    > The camera parameters are stored in a config file. If the config file is not found, default values are used.
    > The camera can be configured to show the frames, track objects, and compute the point cloud.
    > You can open a connection directly to the camera using the `open` method of the `camera` object.

<a id="emioapi.emioapi.EmioAPI.motors"></a>

### motors

The emio motors object

<a id="emioapi.emioapi.EmioAPI.camera"></a>

### camera

The emio camera object

<a id="emioapi.emioapi.EmioAPI.camera_parameters"></a>

### camera\_parameters

The camera parameters object

<a id="emioapi.emioapi.EmioAPI.listEmioDevices"></a>

### listEmioDevices()

```python
@staticmethod
def listEmioDevices() -> list
```

List all the emio devices connected to the computer.

**Returns**:

  A list of device names (the ports).

<a id="emioapi.emioapi.EmioAPI.listUnusedEmioDevices"></a>

### listUnusedEmioDevices()

```python
@staticmethod
def listUnusedEmioDevices() -> list
```

List all the emio devices that are not currently used by any instance of EmioAPI in this process.

**Returns**:

  A list of device names (the ports).

<a id="emioapi.emioapi.EmioAPI.listUsedEmioDevices"></a>

### listUsedEmioDevices()

```python
@staticmethod
def listUsedEmioDevices() -> list
```

List all the emio devices that are currently used by an instance of EmioAPI in this process.

**Returns**:

  A list of device names (the ports).

<a id="emioapi.emioapi.EmioAPI.connectToEmioDevice"></a>

### connectToEmioDevice(device\_name: str = None)

```python
def connectToEmioDevice(device_name: str = None) -> bool
```

Connect to the emio device with the given name.

**Arguments**:

- `device_name` - The name of the device to connect to. If None, the first device found that is not used in this process will be the chosen one.
  

**Returns**:

  True if the connection is successful, False otherwise.

<a id="emioapi.emioapi.EmioAPI.disconnect"></a>

### disconnect()

```python
def disconnect()
```

Close the connection to motors and camera.

<a id="emioapi.emioapi.EmioAPI.printStatus"></a>

### printStatus()

```python
def printStatus()
```

Print the status of the Emio device.

<a id="emioapi.emiocamera"></a>

# emioapi.emiocamera

<a id="emioapi.emiocamera.EmioCamera"></a>

## EmioCamera

```python
class EmioCamera()
```

A class to interface with the realsense camera on Emio.
This class creates a process using mulltiprocessing to handle the camera.

<a id="emioapi.emiocamera.EmioCamera.is_running"></a>

### is\_running()

```python
@property
def is_running()
```

Get the running status of the camera.

**Returns**:

- `bool` - The running status of the camera.

<a id="emioapi.emiocamera.EmioCamera.track_markers"></a>

### track\_markers()

```python
@property
def track_markers()
```

Get whether the camera is tracking objects or not.

**Returns**:

- `bool` - True if the camera is tracking the markers, else False.

<a id="emioapi.emiocamera.EmioCamera.track_markers"></a>

### track\_markers(value)

```python
@track_markers.setter
def track_markers(value)
```

Set the tracking status of the camera.

**Arguments**:

- `value` - bool: The new tracking status.

<a id="emioapi.emiocamera.EmioCamera.compute_point_cloud"></a>

### compute\_point\_cloud()

```python
@property
def compute_point_cloud()
```

Get whether the camera is computing the point cloud or not.

**Returns**:

- `bool` - True if the camera is computing the point cloud, else False.

<a id="emioapi.emiocamera.EmioCamera.compute_point_cloud"></a>

### compute\_point\_cloud(value)

```python
@compute_point_cloud.setter
def compute_point_cloud(value)
```

Set the point cloud computation status of the camera.

**Arguments**:

- `value` - bool: The new point cloud computation status.

<a id="emioapi.emiocamera.EmioCamera.show_frames"></a>

### show\_frames()

```python
@property
def show_frames()
```

Get the show status of the camera.

**Returns**:

- `bool` - The show status of the camera.

<a id="emioapi.emiocamera.EmioCamera.show_frames"></a>

### show\_frames(value)

```python
@show_frames.setter
def show_frames(value)
```

Set the show status of the camera.

**Arguments**:

- `value` - bool: The new show status.

<a id="emioapi.emiocamera.EmioCamera.parameters"></a>

### parameters()

```python
@property
def parameters()
```

Get the camera parameters.

**Returns**:

- `dict` - The camera parameters.

<a id="emioapi.emiocamera.EmioCamera.parameters"></a>

### parameters(value)

```python
@parameters.setter
def parameters(value)
```

Set the camera tracking parameters:
- hue_h: int: The upper hue value.
- hue_l: int: The lower hue value.
- sat_h: int: The upper saturation value.
- sat_l: int: The lower saturation value.
- value_h: int: The upper value value.
- value_l: int: The lower value value.
- erosion_size: int: The size of the erosion kernel.
- area: int: The minimum area of the detected objects.

:::warning
- The camera parameters are not saved to a file. You need to save them manually.
- The paramters are set when opening the camera. To change the parameters programatically, you need to close the camera and open it again with the wanted parameters.
:::

**Arguments**:

- `value` - dict: The new camera parameters.

<a id="emioapi.emiocamera.EmioCamera.trackers_pos"></a>

### trackers\_pos()

```python
@property
def trackers_pos()
```

Get the positions of the trackers.

**Returns**:

- `list` - The positions of the trackers as a list of lists.

<a id="emioapi.emiocamera.EmioCamera.point_cloud"></a>

### point\_cloud()

```python
@property
def point_cloud()
```

Get the point cloud data.

**Returns**:

  The point cloud data as a numpy array.

<a id="emioapi.emiocamera.EmioCamera.hsv_frame"></a>

### hsv\_frame()

```python
@property
def hsv_frame()
```

Get the HSV frame.

**Returns**:

  The HSV frame as a numpy array.

<a id="emioapi.emiocamera.EmioCamera.mask_frame"></a>

### mask\_frame()

```python
@property
def mask_frame()
```

Get the mask frame.

**Returns**:

  The mask frame as a numpy array.

<a id="emioapi.emiocamera.EmioCamera.open"></a>

### open()

```python
def open() -> bool
```

Initialize and open the camera in another process.
This function creates a new process to handle the camera and starts it.

<a id="emioapi.emiocamera.EmioCamera.close"></a>

### close()

```python
def close()
```

Close the camera and terminate the process. Sets the running status to False.

<a id="emioapi.emiomotors"></a>

# emioapi.emiomotors

<a id="emioapi.emiomotors.EmioMotors"></a>

## EmioMotors

```python
class EmioMotors()
```

Class to control emio motors. 
The class is designed to be used with the emio device.
The motors are controlled in position mode. The class is thread-safe and can be used in a multi-threaded environment.

<a id="emioapi.emiomotors.EmioMotors.lengthToPulse"></a>

### lengthToPulse(displacement: list)

```python
def lengthToPulse(displacement: list)
```

Convert length (mm) to pulse using the conversion factor `lengthToPulse`.

**Arguments**:

- `displacement` - list of length values in mm for each motor.
  

**Returns**:

  A list of pulse values for each motor.

<a id="emioapi.emiomotors.EmioMotors.pulseToLength"></a>

### pulseToLength(pulse: list)

```python
def pulseToLength(pulse: list)
```

Convert pulse to length (mm) using the conversion factor `lengthToPulse`.

**Arguments**:

- `pulse` - list of pulse integer values for each motor.
  

**Returns**:

  A list of length values in mm for each motor.

<a id="emioapi.emiomotors.EmioMotors.pulseToRad"></a>

### pulseToRad(pulse: list)

```python
def pulseToRad(pulse: list)
```

Convert pulse to radians using the conversion factor `radToPulse`.

**Arguments**:

- `pulse` - list of pulse integer values for each motor.
  

**Returns**:

  A list of angles in radians for each motor.

<a id="emioapi.emiomotors.EmioMotors.pulseToDeg"></a>

### pulseToDeg(pulse: list)

```python
def pulseToDeg(pulse: list)
```

Convert pulse to degrees using the conversion factor `radToPulse`.

**Arguments**:

- `pulse` - list of pulse values for each motor.
  

**Returns**:

  A list of angles in degrees for each motor.

<a id="emioapi.emiomotors.EmioMotors.close"></a>

### close()

```python
def close()
```

Close the connection to the motors.

<a id="emioapi.emiomotors.EmioMotors.printStatus"></a>

### printStatus()

```python
def printStatus()
```

Print the current position of the motors.

<a id="emioapi.emiomotors.EmioMotors.relativePos"></a>

### relativePos(init\_pos: list, rel\_pos: list)

```python
@property
def relativePos(init_pos: list, rel_pos: list)
```

Calculate the new position of the motors based on the initial position and relative position in pulses.

**Arguments**:

- `init_pos` - list of initial pulse values for each motor.
- `rel_pos` - list of relative pulse values for each motor.
  

**Returns**:

  A list of new pulse values for each motor.

<a id="emioapi.emiomotors.EmioMotors.angles"></a>

### angles()

```python
@property
def angles()
```

Get the current angles of the motors in radians.

<a id="emioapi.emiomotors.EmioMotors.angles"></a>

### angles(angles)

```python
@angles.setter
def angles(angles)
```

Set the goal angles of the motors in radians.

<a id="emioapi.emiomotors.EmioMotors.goal_velocity"></a>

### goal\_velocity()

```python
@property
def goal_velocity()
```

Get the current velocity (rev/min) of the motors.

<a id="emioapi.emiomotors.EmioMotors.goal_velocity"></a>

### goal\_velocity(velocities)

```python
@goal_velocity.setter
def goal_velocity(velocities)
```

Set the goal velocity (rev/min) of the motors.

<a id="emioapi.emiomotors.EmioMotors.max_velocity"></a>

### max\_velocity()

```python
@property
def max_velocity()
```

Get the current velocity (rev/min) profile of the motors.

<a id="emioapi.emiomotors.EmioMotors.max_velocity"></a>

### max\_velocity(max\_vel)

```python
@max_velocity.setter
def max_velocity(max_vel)
```

Set the maximum velocities (rev/min) in position mode.

**Arguments**:

- `max_vel` - list of maximum velocities for each motor in rev/min.

<a id="emioapi.emiomotors.EmioMotors.is_connected"></a>

### is\_connected()

```python
@property
def is_connected()
```

Check if the motors are connected.

<a id="emioapi.emiomotors.EmioMotors.device_name"></a>

### device\_name()

```python
@property
def device_name()
```

Get the name of the device.

<a id="emioapi.emiomotors.EmioMotors.moving"></a>

### moving()

```python
@property
def moving()
```

Check if the motors are moving.

<a id="emioapi.emiomotors.EmioMotors.moving_status"></a>

### moving\_status()

```python
@property
def moving_status()
```

Get the moving status of the motors.

**Returns**:

  A Byte encoding different informations on the moving status like whether the desired position has been reached or not, if the profile is in progress or not, the kind of Profile used...
  See here https://emanual.robotis.com/docs/en/dxl/x/xc330-t288/[`moving`](#emioapi.emiomotors.EmioMotors.moving)-status for more details.

<a id="emioapi.emiomotors.EmioMotors.velocity"></a>

### velocity()

```python
@property
def velocity()
```

Get the current velocity (rev/min) of the motors.

<a id="emioapi.emiomotors.EmioMotors.velocity_trajectory"></a>

### velocity\_trajectory()

```python
@property
def velocity_trajectory()
```

Get the velocity (rev/min) trajectory of the motors.

<a id="emioapi.emiomotors.EmioMotors.position_trajectory"></a>

### position\_trajectory()

```python
@property
def position_trajectory()
```

Get the position (pulse) trajectory of the motors.

