import pyautogui
import cv2
from screenshot.capture import ScreenCapture
from utils.image_matcher import ImageMatcher

class ClickHandler:
    def __init__(self, monitor_index):
        self.monitor_index = monitor_index
        self.screen_capture = ScreenCapture()

    def click_on_match(self, region_image):
        matcher = ImageMatcher(self.monitor_index)
        matched_image, found, top_left = matcher.match_image(region_image)

        if found:
            monitor_info = self.screen_capture.get_monitors()[self.monitor_index]
            click_x = monitor_info["left"] + top_left[0] + region_image.shape[1] // 2
            click_y = monitor_info["top"] + top_left[1] + region_image.shape[0] // 2

            pyautogui.click(click_x, click_y)
            return True, (click_x, click_y)

        return False, None


    def click_and_type(self, region_image, text):
        found, click_position = self.click_on_match(region_image)

        if found and click_position:
            pyautogui.sleep(0.5)
            pyautogui.write(text, interval=0.1)
            return True
        return False
