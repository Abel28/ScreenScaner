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

    def get_region_image(self, region_coords):
        """
        Recorta y devuelve la imagen de una región específica de la captura de pantalla.
        
        Args:
            region_coords (tuple): Coordenadas de la región en el formato (x1, y1, x2, y2).
        
        Returns:
            region_image: Imagen de la región especificada.
        """
        if self.image is None:
            raise ValueError("No se ha capturado ninguna pantalla. Llama a capture_monitor primero.")

        x1, y1, x2, y2 = region_coords

        height, width = self.image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)

        if x2 > x1 and y2 > y1:
            region_image = self.image[y1:y2, x1:x2]
            return region_image
        else:
            raise ValueError("Región inválida o vacía. Verifica las coordenadas.")