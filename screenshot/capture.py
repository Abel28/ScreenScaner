import mss
import numpy as np
import cv2

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()
        self.image = None

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
