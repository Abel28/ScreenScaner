import tkinter as tk
from tkinter.ttk import Notebook
import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import ttk
from database.steps_db_handler import DBHandler as StepDBHandler
from tkinter import ttk, messagebox, simpledialog, filedialog
from utils.click_handler import ClickHandler
from screenshot.selector import RegionSelector
from screenshot.capture import ScreenCapture
import io
from utils.image_matcher import ImageMatcher
import os


class StepsView:
    def __init__(self, root: tk.Tk, notebook: Notebook):
        self.frame = tk.Frame(notebook)
        self.root = root
        notebook.add(self.frame, text="Pasos")

        self.db = StepDBHandler()
        self.screen_capture = ScreenCapture()
        self.selected_id = tk.StringVar(self.frame)

        self.setup_tab_ui()

    def setup_tab_ui(self):

        self.steps_frame = tk.Frame(self.frame)
        self.steps_frame.pack(fill="both", expand=True)

        self.load_ids()

        if self.ids:
            self.selected_id.set(self.ids[0])
            self.display_entry_data(self.ids[0])

        tk.Label(self.steps_frame, text="Pasos").pack()
        self.id_menu = tk.OptionMenu(self.frame, self.selected_id, *self.ids, command=self.display_entry_data)
        self.id_menu.pack(pady=10)

        ttk.Button(self.steps_frame, text="Crear", command=self.open_entry_window).pack(pady=10)

        self.data_display = tk.Text(self.frame, width=50, height=15)
        self.data_display.pack(pady=10)

        

    def load_ids(self):
        self.ids = self.db.get_all_ids()
        if self.ids:
            self.selected_id.set(self.ids[0])

    def open_entry_window(self):
        self.entry_window = tk.Toplevel(self.frame)
        self.entry_window.title("Ventana de Entrada")

        tk.Label(self.entry_window, text="ID:").grid(row=0, column=0, padx=5, pady=5)
        self.id_entry = tk.Entry(self.entry_window)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.entry_window, text="Requisitos:").grid(row=1, column=0, padx=5, pady=5)
        self.requisitos_frame = tk.Frame(self.entry_window)
        self.requisitos_frame.grid(row=1, column=1, padx=5, pady=5)
        self.requisitos_entries = []
        self.add_requisito_button = tk.Button(self.entry_window, text="Agregar Requisito", command=self.add_requisito)
        self.add_requisito_button.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        tk.Label(self.entry_window, text="Given-When-Then:").grid(row=3, column=0, padx=5, pady=5)
        self.given_when_then_frame = tk.Frame(self.entry_window)
        self.given_when_then_frame.grid(row=3, column=1, padx=5, pady=5)
        
        self.add_given_button = tk.Button(self.entry_window, text="Agregar Given", command=lambda: self.add_gwt_entry("Given"))
        self.add_given_button.grid(row=4, column=1, padx=5, pady=2, sticky="w")
        self.add_when_button = tk.Button(self.entry_window, text="Agregar When", command=lambda: self.add_gwt_entry("When"))
        self.add_when_button.grid(row=5, column=1, padx=5, pady=2, sticky="w")
        self.add_then_button = tk.Button(self.entry_window, text="Agregar Then", command=lambda: self.add_gwt_entry("Then"))
        self.add_then_button.grid(row=6, column=1, padx=5, pady=2, sticky="w")

        self.given_when_then_entries = {"Given": [], "When": [], "Then": []}

        self.save_button = tk.Button(self.entry_window, text="Guardar", command=self.save_entry)
        self.save_button.grid(row=7, column=1, pady=10)

    def add_requisito(self):
        requisito_frame = tk.Frame(self.requisitos_frame)
        requisito_entry = tk.Entry(requisito_frame)
        requisito_entry.pack(side="left", pady=2)
        delete_button = tk.Button(requisito_frame, text="Eliminar", command=lambda: self.delete_entry(requisito_frame, self.requisitos_entries, requisito_entry))
        delete_button.pack(side="left", padx=5)
        requisito_frame.pack(anchor="w")
        self.requisitos_entries.append(requisito_entry)

    def add_gwt_entry(self, gwt_type):
        gwt_frame = tk.Frame(self.given_when_then_frame)
        tk.Label(gwt_frame, text=f"{gwt_type}:").pack(side="left")
        gwt_entry = tk.Entry(gwt_frame)
        gwt_entry.pack(side="left", padx=5, pady=2)
        delete_button = tk.Button(gwt_frame, text="Eliminar", command=lambda: self.delete_entry(gwt_frame, self.given_when_then_entries[gwt_type], gwt_entry))
        delete_button.pack(side="left", padx=5)
        gwt_frame.pack(anchor="w")
        self.given_when_then_entries[gwt_type].append(gwt_entry)

    def delete_entry(self, frame, entry_list, entry):
        frame.pack_forget()
        frame.destroy()
        entry_list.remove(entry)

    def save_entry(self):
        entry_id = self.db.insert_entry()
        
        for req_entry in self.requisitos_entries:
            self.db.insert_requisito(entry_id, req_entry.get())

        for gwt_type, entries in self.given_when_then_entries.items():
            for entry in entries:
                self.db.insert_gwt(entry_id, gwt_type, entry.get())

        print("Datos guardados en la base de datos")
        
        self.entry_window.destroy()

        self.load_ids()
        self.update_option_menu()
        self.selected_id.set(entry_id)
        
        self.display_entry_data(entry_id)

    def update_option_menu(self):
        self.id_menu["menu"].delete(0, "end")
        for id_value in self.ids:
            self.id_menu["menu"].add_command(label=id_value, command=lambda value=id_value: self.selected_id.set(value))
        self.selected_id.trace("w", lambda *args: self.display_entry_data(self.selected_id.get()))

    def display_entry_data(self, selected_id):
        requisitos, gwt_data = self.db.get_entry_data(selected_id)
        
        self.data_display.delete(1.0, tk.END)
        
        self.data_display.insert(tk.END, f"ID: {selected_id}\n")
        self.data_display.insert(tk.END, "Requisitos:\n")
        for req in requisitos:
            self.data_display.insert(tk.END, f"- {req}\n")
        
        self.data_display.insert(tk.END, "\nGiven-When-Then:\n")
        for gwt_type, description in gwt_data:
            self.data_display.insert(tk.END, f"{gwt_type}: {description}\n")

    def on_close(self):
        self.db.close()
        self.root.destroy()