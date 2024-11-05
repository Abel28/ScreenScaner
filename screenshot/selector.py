import cv2
from PIL import Image, ImageTk

class RegionSelector:
    def __init__(self, canvas):
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

    def save_selected_regions(self, image):
        saved_images = []
        height, width = image.shape[:2]

        for idx, (x1, y1, x2, y2) in enumerate(self.selected_regions):
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(width, x2), min(height, y2)

            if x2 > x1 and y2 > y1:
                region = image[y1:y2, x1:x2]
                filename = f"region_{idx + 1}.png"
                cv2.imwrite(filename, region)
                saved_images.append((filename, ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(region, cv2.COLOR_BGR2RGB)))))
            else:
                print(f"Región inválida o vacía: ({x1}, {y1}, {x2}, {y2}) - No se guarda.")

        return saved_images
