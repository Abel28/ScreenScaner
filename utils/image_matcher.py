import cv2
import numpy as np
from screenshot.capture import ScreenCapture

class ImageMatcher:
    def __init__(self, monitor_index):
        self.screen_capture = ScreenCapture()
        self.monitor_index = monitor_index

    def match_image(self, region_image):
        screenshot, monitor_info = self.screen_capture.capture_monitor(self.monitor_index)
        
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        region_gray = cv2.cvtColor(region_image, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_gray, region_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        threshold = 0.8
        if max_val >= threshold:
            top_left = max_loc
            bottom_right = (top_left[0] + region_image.shape[1], top_left[1] + region_image.shape[0])

            cv2.rectangle(screenshot, top_left, bottom_right, (0, 255, 0), 2)

            return screenshot, True, top_left
        else:
            return screenshot, False, None
