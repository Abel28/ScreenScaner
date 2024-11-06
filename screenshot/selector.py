import cv2
from PIL import Image, ImageTk
from tkinter import Canvas

class RegionSelector:
    def __init__(self, canvas: Canvas):
        self.canvas = canvas
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
        print(f"Región guardada: ({self.start_x}, {self.start_y}, {end_x}, {end_y})")