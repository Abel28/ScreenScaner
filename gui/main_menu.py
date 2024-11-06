import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
from database.db_handler import DBHandler
from screenshot.capture import ScreenCapture
from screenshot.selector import RegionSelector
from utils.image_matcher import ImageMatcher
from utils.click_handler import ClickHandler
import os
import io
import time
from .styles import Styles
import numpy as np
from .execution_view import ExecutionView
from .screenshot_view import ScreenshootView

class MainMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Detector Test tool")
        self.root.geometry("1000x1000")
        self.db = DBHandler()
        self.actions_queue = []

        self._setup_ui()

    def _setup_ui(self):

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.tab1 = ScreenshootView(self.root, notebook)

        self.tab2 = ExecutionView(self.root, notebook)

        self.tab3 = tk.Frame(notebook)
        notebook.add(self.tab3, text="Pasos")

        notebook.bind("<<NotebookTabChanged>>", lambda event: self.on_tab_selected(event, notebook))

        self.setup_steps_tab()

    def on_tab_selected(self, event, notebook):
        selected_tab = notebook.index(notebook.select())
        if selected_tab == 1:
            self.tab2.update_execution_tab()

    
    def setup_steps_tab(self):
        self.steps_frame = tk.Frame(self.tab3)
        self.steps_frame.pack(fill="both", expand=True)

        tk.Label(self.steps_frame, text="Pasos").pack()
        ttk.OptionMenu(self.steps_frame, variable=tk.StringVar()).pack()

        ttk.Button(self.steps_frame, text="Crear").pack()


    def save_regions(self):
        if self.image is not None:
            for idx, (x1, y1, x2, y2) in enumerate(self.selector.selected_regions):
                filename = f"region_{idx + 1}.png"
                region = self.image[y1:y2, x1:x2]
                cv2.imwrite(filename, region)
                self.db.insert_region(filename, x1, y1, x2, y2)
            messagebox.showinfo("Guardado", "Regiones guardadas exitosamente.")
        else:
            messagebox.showerror("Error", "No hay captura de pantalla para guardar.")
    

    def run(self):
        self.root.mainloop()
