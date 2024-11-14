import pyautogui
import cv2
from PIL import ImageGrab
import numpy as np
from screeninfo import get_monitors

class ClickHandler:
    def __init__(self, monitor_index, timeout=5):
        self.monitor_index = monitor_index
        self.monitor = get_monitors()[monitor_index]
        self.timeout = timeout

    def click_on_match(self, region_image, offset_x=0, offset_y=0):
        left = self.monitor.x
        top = self.monitor.y
        right = left + self.monitor.width
        bottom = top + self.monitor.height

        screen_image = ImageGrab.grab(bbox=(left, top, right, bottom))
        screen_image = cv2.cvtColor(np.array(screen_image), cv2.COLOR_RGB2BGR)

        result = cv2.matchTemplate(screen_image, region_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        threshold = 0.8
        if max_val >= threshold:
            click_x = left + max_loc[0] + offset_x
            click_y = top + max_loc[1] + offset_y

            pyautogui.click(click_x, click_y)
            return True, (click_x, click_y)
        return False, None

    def click_and_type(self, region_image, text, offset_x=0, offset_y=0):
        found, click_position = self.click_on_match(region_image, offset_x, offset_y)
        
        if found and click_position:
            pyautogui.sleep(0.5)
            pyautogui.write(text, interval=0.1)
            return True
        return False