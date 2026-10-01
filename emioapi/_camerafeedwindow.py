from typing import Final, Tuple
from types import SimpleNamespace

import dearpygui.dearpygui as dpg
import cv2 as cv
import numpy as np

from emioapi._logging_config import logger


"""
    This class is used to create a camera feed window that displays the video feed from a camera.
    It runs in a separate thread and can be started and stopped using the start() and stop() methods.
    The camera feed is displayed in a window named 'mask'.
    The class uses OpenCV to create the window and display the video feed.
    The camera feed is passed to the class as a frame parameter.
"""	
class EmioAPIGUI():

    TAG_MAINWINDOW:Final[str] = "MainWindow"
    TAG_DEPTHTEX:Final[str] = "tex_depth"
    TAG_RGBTEX:Final[str] = "tex_rgb"
    TAG_HSVTEX:Final[str] = "tex_hsv"
    TAG_MASKTEX:Final[str] = "tex_mask"
    TEXWIDTH:Final[int] = 640
    TEXHEIGHT:Final[int] = 480

    _TIMEOUT_THREAD: Final[int]=5
    
    windowCount = 0

    @staticmethod
    def start_in_thread(trackbarParams={}, save_callback=None):
        from threading import Thread
        from time import time, sleep

        def _gui_worker(result: SimpleNamespace, trackbarParams={}, save_callback=None):
            result.gui_handle = EmioAPIGUI(trackbarParams=trackbarParams, save_callback=save_callback)
            logger.info(f"Starting Emio API GUI inside a thread.")
            result.gui_handle.run_loop()

        result = SimpleNamespace(gui_handle=None, gui_thread=None)
        result.gui_thread = Thread(target=_gui_worker, daemon=True, args=(result, trackbarParams, save_callback))
        result.gui_thread.start()
        startime = time()
        while not result.gui_handle:
            if time()-startime < EmioAPIGUI._TIMEOUT_THREAD:
                logger.info(f"Waiting for thread {result.gui_thread} to start")
                sleep(0.5)
            else:
                raise TimeoutError("Could not open EmioAPIGUI thread in time.")
        logger.info(f"Started Emio API GUI inside a thread {result.gui_thread}.")
        return result
        

    def __init__(self, trackbarParams={}, save_callback=None):
        import numpy as np

        self.window_id = str(EmioAPIGUI.windowCount)

        self.default_param = trackbarParams.copy()
        self.trackbarParams = trackbarParams
        self.trackbars = {}

        self.save_callback = save_callback

        try:
            if EmioAPIGUI.windowCount==0:
                dpg.create_context()
                dpg.create_viewport(title="Camera Feed", width=1150, height=700, resizable=False)
                dpg.setup_dearpygui()

            self.context_exists = True
            self.images_scale = 0.6

            # Textures for camera frames
            with dpg.texture_registry(show=False):
                blank_data = np.zeros((EmioAPIGUI.TEXWIDTH * EmioAPIGUI.TEXHEIGHT * 4,), dtype=np.float32)
                dpg.add_dynamic_texture(width=EmioAPIGUI.TEXWIDTH, height=EmioAPIGUI.TEXHEIGHT, default_value=blank_data, tag=EmioAPIGUI.TAG_RGBTEX+self.window_id)
                dpg.add_dynamic_texture(width=EmioAPIGUI.TEXWIDTH, height=EmioAPIGUI.TEXHEIGHT, default_value=blank_data, tag=EmioAPIGUI.TAG_DEPTHTEX+self.window_id)
                dpg.add_dynamic_texture(width=EmioAPIGUI.TEXWIDTH, height=EmioAPIGUI.TEXHEIGHT, default_value=blank_data, tag=EmioAPIGUI.TAG_MASKTEX+self.window_id)
                dpg.add_dynamic_texture(width=EmioAPIGUI.TEXWIDTH, height=EmioAPIGUI.TEXHEIGHT, default_value=blank_data, tag=EmioAPIGUI.TAG_HSVTEX+self.window_id)

            with dpg.window(tag=EmioAPIGUI.TAG_MAINWINDOW+self.window_id, no_title_bar=True):
                with dpg.child_window(width=300):
                    # params
                    if self.trackbarParams:
                        for key, val in self.trackbarParams.items():
                            dpg.add_text(default_value=str(key))
                            dpg.add_slider_double(tag=f"TAG_SLIDER{self.window_id}_{key}",min_value=0, max_value=255, default_value=val)
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Save Params", callback=self.save_params)
                            dpg.add_button(label="Reset Params", callback=self.reset_params)

                # frames
                width, height = self.image_size
                origin = (316, 8)
                with dpg.window(label="RGB Frame", autosize=True, pos=origin, no_move=True, no_close=True):
                    dpg.add_image(EmioAPIGUI.TAG_RGBTEX+self.window_id, width=width, height=height, label="RGB")
                with dpg.window(label="Depth Frame", autosize=True, pos=(origin[0]+width+16, origin[1]), no_close=True, no_move=True):
                    dpg.add_image(EmioAPIGUI.TAG_DEPTHTEX+self.window_id, width=width, height=height)
                with dpg.window(label="Mask Frame", autosize=True, pos=(origin[0], origin[1]+height+35), no_close=True, no_move=True):
                    dpg.add_image(EmioAPIGUI.TAG_MASKTEX+self.window_id, width=width, height=height)
                with dpg.window(label="HSV Frame", autosize=True, pos=(origin[0]+width+16, origin[1]+height+35), no_close=True, no_move=True):
                    dpg.add_image(EmioAPIGUI.TAG_HSVTEX+self.window_id, width=width, height=height)

            dpg.show_viewport()
            dpg.show_item_registry()
            dpg.set_primary_window(EmioAPIGUI.TAG_MAINWINDOW+self.window_id, True)

            EmioAPIGUI.windowCount=+1
        
        except Exception as e:
            print(e)
            raise(e)



    @property
    def image_size(self) -> Tuple[int, int]:
         return (self.images_scale * self.TEXWIDTH, self.images_scale*self.TEXHEIGHT)
    

    def run_loop(self):
        while dpg.is_dearpygui_running():
                    dpg.render_dearpygui_frame()

        if EmioAPIGUI.windowCount == 0:
            dpg.destroy_context()
            self.context_exists = False


    def set_frames(self, rgb, depth, mask, hsv):
        if rgb is not None:
            dpg.set_value(EmioAPIGUI.TAG_RGBTEX+self.window_id, np.ascontiguousarray(cv.cvtColor(rgb, cv.COLOR_BGR2RGBA), dtype=np.float32)/255)
        if depth is not None:
            dpg.set_value(EmioAPIGUI.TAG_DEPTHTEX+self.window_id, np.ascontiguousarray(cv.cvtColor(depth, cv.COLOR_BGR2RGBA), dtype=np.float32)/255)
        if mask is not None:
            dpg.set_value(EmioAPIGUI.TAG_MASKTEX+self.window_id, np.ascontiguousarray(cv.cvtColor(mask, cv.COLOR_BGR2RGBA), dtype=np.float32)/255)
        if hsv is not None:
            dpg.set_value(EmioAPIGUI.TAG_HSVTEX+self.window_id, np.ascontiguousarray(cv.cvtColor(hsv, cv.COLOR_BGR2RGBA), dtype=np.float32)/255)


    def is_running(self):
         return dpg.is_dearpygui_running() if self.context_exists else False


    def reset_params(self):
        for key, _ in self.trackbarParams.items():
            dpg.set_value(f"TAG_SLIDER{+self.window_id}_{key}", self.default_param[key])
            self.trackbarParams[key] = self.default_param[key]


    def save_params(self):
        if self.save_callback is None:
            logger.warning("Parameters not  saved. No callback given at init.")
        else:
            self.save_callback()