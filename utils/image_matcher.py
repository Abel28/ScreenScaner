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
        
    def match_image_with_threshold(self, screen_image, region_image, threshold):
        if region_image is None:
            raise ValueError("La imagen de la región es None. Asegúrate de que region_image esté correctamente cargada.")
        
        result = cv2.matchTemplate(screen_image, region_image, cv2.TM_CCOEFF_NORMED)
        
        locations = np.where(result >= threshold)
        found_points = list(zip(*locations[::-1]))

        matched_image = screen_image.copy()
        w, h = region_image.shape[1], region_image.shape[0]
        for pt in found_points:
            cv2.rectangle(matched_image, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        top_left = max_loc if max_val >= threshold else None

        return matched_image, found_points, top_left
        
    def find_all_matches(self, template, image, threshold=0.8):
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        match_locations = np.where(result >= threshold)

        matches = []
        for pt in zip(*match_locations[::-1]):
            top_left = pt
            bottom_right = (pt[0] + template.shape[1], pt[1] + template.shape[0])
            matches.append((top_left, bottom_right))
        
        return matches
