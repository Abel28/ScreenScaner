import cv2
from PIL import Image, ImageTk
from tkinter import Canvas
import pytesseract

class RegionSelector:
    def __init__(self, canvas, image, update_text_callback):
        self.canvas = canvas
        self.image = image
        self.update_text_callback = update_text_callback
        self.start_x = self.start_y = self.rect = None
        self.selected_regions = []
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    def on_mouse_drag(self, event):
        cur_x, cur_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.selected_regions.append((int(self.start_x), int(self.start_y), int(end_x), int(end_y)))
        self.recognize_text_in_region()

    def recognize_text_in_region(self):
        if self.selected_regions:
            x1, y1, x2, y2 = self.selected_regions[-1]
            selected_region = self.image[y1:y2, x1:x2]

            gray_region = cv2.cvtColor(selected_region, cv2.COLOR_BGR2GRAY)

            recognized_text = pytesseract.image_to_string(gray_region)
            
            self.update_text_callback(recognized_text)