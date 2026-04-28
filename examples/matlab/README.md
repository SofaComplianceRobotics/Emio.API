# Compliant Robotics Lab — Python/Simulink Bridge

## Dependencies

Requires modifications to `emioapi/_depthcamera.py`, `emioapi/emiocamera.py`,
and `emioapi/_positionestimation.py` for:

- Raw camera coordinate access via the `trackers_pos_image` variable
  (used in `"front"` mode, without processing noise)
- A `process_frame()` function that separates camera acquisition from data
  processing (enables event-based inter-process synchronisation).
  `update()` remains functional and calls `process_frame()` internally.
- Plane projection of marker positions to reduce camera noise
  (`"plan"` mode only, for now).

---

## Quickstart

```bash
python main.py
```

Then start the Simulink simulation. The connection is established automatically.

To stop: **Ctrl-C** or press **q** in the camera window.

---

## Configuration

The only file you need to edit is **`params.py`**:

| Parameter | Description |
|---|---|
| `fps` | Control loop frequency (Hz) |
| `nb_markers` | Number of markers tracked by the camera |
| `side` | Camera viewpoint: `"top"`, `"front"`, or `"plan"` (plane projection) |
| `sort` | Marker sorting axis: `"y"` or `"z"` |

Do not modify any other parameters.

---

## Testing Without Hardware

```bash
python test.py
```

Replaces camera and motor data with random values.
Useful for validating the Simulink model independently.

---

## File Structure

| File | Role |
|---|---|
| `main.py` | Entry point |
| `params.py` | ⚙️ Configuration — **the only file you should edit** |
| `camera.py` | Marker acquisition and processing |
| `process_motor.py` | Motor command loop |
| `udp_bridge.py` | UDP communication layer |
| `test.py` | Hardware-free test script |

---

## Simulink & MATLAB Setup

**Required toolbox:**
- Instrument Control Toolbox (for UDP blocks)

**Simulink solver settings:**

| Parameter | Value |
|---|---|
| Solver type | `Fixed-step` |
| Solver | `ode1` (or any other explicit method) |
| Fixed step size | `1/30` (matches `fps`) |
| Stop time | `inf` |

**UDP Receive block:**

| Parameter | Value |
|---|---|
| Local port | `25000` |
| Remote port | `9090` |
| Data size | `[3*nb_markers + 5, 1]` (seq + ny + nu) |
| Data type | `double` |
| Byte order | `little-endian` |
| Blocking mode | ✅ enabled |
| Timeout | `2` s (or more if Python starts slowly) |

**UDP Send block:**

| Parameter | Value |
|---|---|
| Remote port | `25001` |
| Byte order | `little-endian` |
| Blocking mode | ✅ enabled |

---

## How It Works

Python is the clock master. At each camera frame (~30 Hz):

1. Camera produces a frame → `event_frame` fires
2. `process_motors` reads motor positions and sends the previous command
3. Marker positions are written to shared memory → `event_measure` fires
4. `process_motors` sends `[seq, y..., motors_pos...]` to Simulink via UDP
5. Simulink computes the control law and replies with `[seq, u...]`
6. The new command is applied at the next tick

If Simulink stops responding, the bridge automatically re-initiates the
handshake after `MAX_RECONNECT_ATTEMPTS` consecutive timeouts — no need to
restart Python.
