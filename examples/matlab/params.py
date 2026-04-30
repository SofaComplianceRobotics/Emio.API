import numpy as np

# --- Configurable settings ---
fps = 30
nb_markers = 1
side = "plan"  # "top", "front"
sort = "y"  # "y" or "z", only for front camera

# UDP settings
remote_ip    = "127.0.0.1"
remote_port  = 25000
local_port   = 25001
bind_port    = 9090
recv_timeout = 0.1

# --- Fixed settings (DO NOT CHANGE) ---
nu = 4 # number of actuators

# camera settings
depth = 249 # for front camera, 
plane_d = 5
plane_n = np.array([1,0,0])
front2top_offset = np.array([-2.2, 195.8, -254])
