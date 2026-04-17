# --- Confurable settings ---
fps = 30
nb_markers = 1
side = "top"  # "top" or "front"

# --- Fixed settings (DO NOT CHANGE) ---
ny = 3 * nb_markers # number of measurements
nu = 4 # number of actuators
depth = 249 # for front camera, in mm (DO NOT CHANGE)

simulink_ip   = "127.0.0.1"
simulink_port = 25000
python_port   = 25001
bind_port     = 9090
recv_timeout  = 0.1
