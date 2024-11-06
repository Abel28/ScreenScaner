import pyautogui
import cv2
from screenshot.capture import ScreenCapture
from utils.image_matcher import ImageMatcher
from tkinter import messagebox
import time

class ClickHandler:
    def __init__(self, monitor_index, timeout=5):
        self.monitor_index = monitor_index
        self.screen_capture = ScreenCapture()
        self.timeout = timeout

    def click_on_match(self, region_image, offset_x=0, offset_y=0):
        matcher = ImageMatcher(self.monitor_index)
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            matched_image, found, top_left = matcher.match_image(region_image)

            if found:
                monitor_info = self.screen_capture.get_monitors()[self.monitor_index]
                click_x = monitor_info["left"] + top_left[0] + offset_x
                click_y = monitor_info["top"] + top_left[1] + offset_y

                pyautogui.click(click_x, click_y)
                return True, (click_x, click_y)

            time.sleep(0.1)
        
        messagebox.showerror("Timeout Error", f"No se encontró coincidencia en {self.timeout} segundos.")
        return False, None

    def click_and_type(self, region_image, text, offset_x=0, offset_y=0):
        found, click_position = self.click_on_match(region_image, offset_x, offset_y)
        
        if found and click_position:
            pyautogui.sleep(0.5)
            pyautogui.write(text, interval=0.1)
            return True
        return False