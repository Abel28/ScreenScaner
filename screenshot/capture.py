import mss
import numpy as np
import cv2
from PIL import ImageGrab

class ScreenCapture:
    def __init__(self):
        self.image = None
        self.sct = mss.mss()
        
    def get_monitors(self):
        monitors = self.sct.monitors[1:]
        return monitors

    def capture_monitor(self, monitor_index):
        monitors = self.get_monitors()
        
        if monitor_index < 0 or monitor_index >= len(monitors):
            raise ValueError("Índice de monitor fuera de rango.")
        
        monitor = monitors[monitor_index]
        screenshot = self.sct.grab(monitor)
        
        self.image = np.array(screenshot)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGRA2BGR)

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