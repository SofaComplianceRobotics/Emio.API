import threading

import cv2
from cv2_enumerate_cameras import enumerate_cameras
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

# dpg.create_context()
# dpg.create_viewport(title='Custom Title', width=600, height=600)

# demo.show_demo()

# dpg.setup_dearpygui()
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()


from emioapi._gui import EmioAPIGUI

# for camera_info in enumerate_cameras():
#     print(f"Index: {camera_info.index}, Name: {camera_info.name}, Path: {camera_info.path}")

# Initialisation de la caméra (0 = caméra par défaut)
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if not ret:
    print("Erreur : Impossible d'accéder à la caméra 0.")
    exit()

cap1 = cv2.VideoCapture(1)
ret1, frame1 = cap1.read()
if not ret1:
    print("Erreur : Impossible d'accéder à la caméra 1.")
    exit()

# Récupération des dimensions de la capture caméra
height, width, _ = frame.shape

running = True
gui = None
lock = threading.Lock()
mockparams = {
    "a": 10,
    "b": 128
}


def update_camera():
    global emiogui, gui
    import numpy as np
    ret, frame = cap.read()
    ret1, frame1 = cap1.read()
    if ret:
        emiogui.set_frames(frame, frame, frame, frame)
    if ret1:
    # blank_data = np.random.randint(0, 255, size=(EmioAPIGUI.TEXWIDTH, EmioAPIGUI.TEXHEIGHT, 3), dtype=np.uint8) # Uncomment if not extra camera
        emiogui1.set_frames(frame1, frame1, frame1, frame1)

gui = EmioAPIGUI.start_in_thread()
emiogui = EmioAPIGUI.add_camera_feed(trackbarParams=mockparams, save_callback=lambda: print("Saved params"))
emiogui1 = EmioAPIGUI.add_camera_feed(trackbarParams=mockparams, save_callback=lambda: print("Saved params"))

while running :
    update_camera()

print("out of while")

cap.release()
