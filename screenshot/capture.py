from mss import mss
import numpy as np
import cv2
from PIL import ImageGrab

class ScreenCapture:
    def __init__(self):
        self.image = None
        
    def get_monitors(self):
        monitors_list = []
        with mss() as sct:
            monitors = sct.monitors
            for monitor in monitors[1:]:
                monitor_info = {
                    "left": monitor["left"],
                    "top": monitor["top"],
                    "width": monitor["width"],
                    "height": monitor["height"]
                }
                monitors_list.append(monitor_info)

        return monitors_list

    def capture_monitor(self, monitor_index):
        monitors = self.get_monitors()
        
        if monitor_index < 0 or monitor_index >= len(monitors):
            raise ValueError("Índice de monitor fuera de rango.")
        
        monitor = monitors[monitor_index]
        left, top = monitor["left"], monitor["top"]
        right = left + monitor["width"]
        bottom = top + monitor["height"]

        screen_image = ImageGrab.grab(bbox=(left, top, right, bottom))
        
        self.image = np.array(screen_image)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR)

        return self.image, monitor

    def get_region_image(self, region):
        if self.image is None:
            raise ValueError("No hay imagen capturada disponible.")
        
        x1, y1, x2, y2 = region

        height, width = self.image.shape[:2]
        if x1 < 0 or y1 < 0 or x2 > width or y2 > height or x1 >= x2 or y1 >= y2:
            raise ValueError("Región inválida o vacía. Verifica las coordenadas.")

        region_image = self.image[y1:y2, x1:x2]

        if region_image.size == 0:
            raise ValueError("La región seleccionada está vacía.")
        
        return region_image