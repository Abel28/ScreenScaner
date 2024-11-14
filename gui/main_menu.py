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
from .steps_view import StepsView

class MainMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ScreenScanner v2.3")
        self.root.geometry("1000x700")
        self.db = DBHandler()
        self.actions_queue = []

        style = ttk.Style()
        style.theme_use('default')

        style.configure("TNotebook", background="lightblue", borderwidth=0)
        style.configure("TNotebook.Tab", background="lightgrey", padding=10, font=('Helvetica', 12, 'bold'))
        style.map("TNotebook.Tab", background=[("selected", "#006A67")])

        self._setup_ui()

    def _setup_ui(self):

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.tab1 = ScreenshootView(self.root, notebook)
        self.tab2 = ExecutionView(self.root, notebook)
        #self.tab3 = StepsView(self.root, notebook)

        notebook.bind("<<NotebookTabChanged>>", lambda event: self.on_tab_selected(event, notebook))

    def on_tab_selected(self, event, notebook):
        selected_tab = notebook.index(notebook.select())
        if selected_tab == 1:
            self.tab2.update_execution_tab()

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
