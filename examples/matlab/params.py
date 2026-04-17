import numpy as np

# --- Confurable settings ---
fps = 30
nb_markers = 1
side = "plan"  # "top", "front"
sort = "y"  # "y" or "z", only for front camera

# --- Fixed settings (DO NOT CHANGE) ---
ny = 3 * nb_markers # number of measurements
nu = 4 # number of actuators

# UDP settings
simulink_ip   = "127.0.0.1"
simulink_port = 25000
python_port   = 25001
bind_port     = 9090
recv_timeout  = 0.1

# camera settings
depth = 249 # for front camera, 
plane_d = 5
plane_n = np.array([1,0,0])
front2top_offset = np.array([-2.2, 195.8, -254])
