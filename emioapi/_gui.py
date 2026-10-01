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
    main_window = None
    gui = SimpleNamespace(gui_handle=None, gui_thread=None)

    @staticmethod
    def start_in_thread(trackbarParams={}, save_callback=None):
        from threading import Thread
        from time import time, sleep

        def _gui_worker(result: SimpleNamespace, trackbarParams={}, save_callback=None):
            result.gui_handle = EmioAPIGUI()
            logger.debug(f"Starting Emio API GUI inside a thread.")
            result.gui_handle.run_loop()

        if EmioAPIGUI.windowCount==0:
            EmioAPIGUI.gui.gui_thread = Thread(target=_gui_worker, daemon=True, args=(EmioAPIGUI.gui, trackbarParams, save_callback))
            EmioAPIGUI.gui.gui_thread.start()
            startime = time()
            while not EmioAPIGUI.gui.gui_handle:
                if time()-startime < EmioAPIGUI._TIMEOUT_THREAD:
                    logger.info(f"Waiting for thread {EmioAPIGUI.gui.gui_thread} to start")
                    sleep(0.5)
                else:
                    raise TimeoutError("Could not open EmioAPIGUI thread in time.")
            logger.debug(f"Started Emio API GUI inside a thread {EmioAPIGUI.gui.gui_thread}.")
        else:
            logger.warning(f"EmioAPIGUI thread is already running in a thread.")

        return EmioAPIGUI.gui

    @staticmethod
    def add_camera_feed(trackbarParams={}, save_callback=None):
        return EmioAPIGUI._CameraFeedWindow(trackbarParams, save_callback)
        

    def __init__(self):
        try:
            if EmioAPIGUI.windowCount==0:
                dpg.create_context()
                dpg.create_viewport(title="Camera Feed", width=1150, height=780, resizable=False)
                dpg.setup_dearpygui()
                EmioAPIGUI.main_window = dpg.add_window(tag=EmioAPIGUI.TAG_MAINWINDOW, no_title_bar=True)
                dpg.add_tab_bar(tag="TAG_TABBAR", parent=EmioAPIGUI.main_window)
                dpg.show_viewport()
                dpg.set_primary_window(EmioAPIGUI.TAG_MAINWINDOW, True)
                self.context_exists = True
        except Exception as e:
            logger.error(str(e))
            raise(e)
    

    def run_loop(self):
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        logger.debug("Closing GUI...")
        self.context_exists = False 
        dpg.destroy_context()
        logger.warning("GUI is closed but EmioAPI is still running!")


    def is_running(self):
         return dpg.is_dearpygui_running() if self.context_exists else False


    class _CameraFeedWindow():
        def __init__(self, trackbarParams={}, save_callback=None):
            self.window_id = str(EmioAPIGUI.windowCount)
            logger.debug(f"Creating CameraFeedWindow  {self.window_id}")

            self.default_param = trackbarParams.copy()
            self.trackbarParams = trackbarParams
            self.trackbars = {}

            self.images_scale = 0.6

            self.save_callback = save_callback

            # Textures for camera frames
            with dpg.texture_registry(show=False):
                blank_data = np.zeros((EmioAPIGUI.TEXWIDTH * EmioAPIGUI.TEXHEIGHT * 4,), dtype=np.float32)
                dpg.add_dynamic_texture(width=EmioAPIGUI.TEXWIDTH, height=EmioAPIGUI.TEXHEIGHT, default_value=blank_data, tag=EmioAPIGUI.TAG_RGBTEX+self.window_id)
                dpg.add_dynamic_texture(width=EmioAPIGUI.TEXWIDTH, height=EmioAPIGUI.TEXHEIGHT, default_value=blank_data, tag=EmioAPIGUI.TAG_DEPTHTEX+self.window_id)
                dpg.add_dynamic_texture(width=EmioAPIGUI.TEXWIDTH, height=EmioAPIGUI.TEXHEIGHT, default_value=blank_data, tag=EmioAPIGUI.TAG_MASKTEX+self.window_id)
                dpg.add_dynamic_texture(width=EmioAPIGUI.TEXWIDTH, height=EmioAPIGUI.TEXHEIGHT, default_value=blank_data, tag=EmioAPIGUI.TAG_HSVTEX+self.window_id)

            # with dpg.tab_bar(parent=EmioAPIGUI.main_window):
            with dpg.tab(label=f"Window {self.window_id}", parent="TAG_TABBAR"):
                with dpg.child_window(no_scroll_with_mouse=True, no_scrollbar=True):
                    # params
                    with dpg.child_window(width=300):
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
                    with dpg.child_window(label="RGB Frame", pos=origin, width=width, height=height+62):
                        dpg.add_text(default_value="RGB")
                        dpg.add_image(EmioAPIGUI.TAG_RGBTEX+self.window_id, label="RGB", width=width, height=height)
                    with dpg.child_window(label="Depth Frame", pos=(origin[0]+width+16, origin[1]), width=width, height=height+62):
                        dpg.add_text(default_value="Depth")
                        dpg.add_image(EmioAPIGUI.TAG_DEPTHTEX+self.window_id, width=width, height=height)
                    with dpg.child_window(label="Mask Frame", pos=(origin[0], origin[1]+height+35), width=width, height=height+62):
                        dpg.add_text(default_value="Mask")
                        dpg.add_image(EmioAPIGUI.TAG_MASKTEX+self.window_id, width=width, height=height)
                    with dpg.child_window(label="HSV Frame", pos=(origin[0]+width+16, origin[1]+height+35), width=width, height=height+62):
                        dpg.add_text(default_value="HSV")
                        dpg.add_image(EmioAPIGUI.TAG_HSVTEX+self.window_id, width=width, height=height)

            EmioAPIGUI.windowCount=+1


        @property
        def image_size(self) -> Tuple[int, int]:
            return (self.images_scale * EmioAPIGUI.TEXWIDTH, self.images_scale*EmioAPIGUI.TEXHEIGHT)
        

        def reset_params(self):
            for key, _ in self.trackbarParams.items():
                dpg.set_value(f"TAG_SLIDER{self.window_id}_{key}", self.default_param[key])
                self.trackbarParams[key] = self.default_param[key]


        def save_params(self):
            if self.save_callback is None:
                logger.warning("Parameters not  saved. No callback given at init.")
            else:
                self.save_callback()

        def set_frames(self, rgb, depth, mask, hsv):
                if rgb is not None:
                    dpg.set_value(EmioAPIGUI.TAG_RGBTEX+self.window_id, np.ascontiguousarray(cv.cvtColor(rgb, cv.COLOR_BGR2RGBA), dtype=np.float32)/255)
                if depth is not None:
                    dpg.set_value(EmioAPIGUI.TAG_DEPTHTEX+self.window_id, np.ascontiguousarray(cv.cvtColor(depth, cv.COLOR_BGR2RGBA), dtype=np.float32)/255)
                if mask is not None:
                    dpg.set_value(EmioAPIGUI.TAG_MASKTEX+self.window_id, np.ascontiguousarray(cv.cvtColor(mask, cv.COLOR_BGR2RGBA), dtype=np.float32)/255)
                if hsv is not None:
                    dpg.set_value(EmioAPIGUI.TAG_HSVTEX+self.window_id, np.ascontiguousarray(cv.cvtColor(hsv, cv.COLOR_BGR2RGBA), dtype=np.float32)/255)