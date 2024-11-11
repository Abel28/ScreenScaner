import tkinter as tk
from tkinter.ttk import Notebook
import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import ttk
from database.db_handler import DBHandler
from tkinter import ttk, messagebox, simpledialog, filedialog
from utils.click_handler import ClickHandler
from utils.image_matcher import ImageMatcher
import time
import os

class ExecutionView:
    def __init__(self, root: tk.Tk, notebook: Notebook):
        self.frame = tk.Frame(notebook)
        self.root = root
        notebook.add(self.frame, text="Ejecución")

        self.selected_monitor = tk.StringVar(value="1")

        self.db = DBHandler()
        self.actions_queue = []

        self.setup_execution_tab()

    def setup_execution_tab(self):

        tk.Label(self.frame, text="Buscar").pack()
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(self.frame, textvariable=self.search_var)
        search_entry.pack(pady=5, fill="x")
        
        search_entry.bind("<KeyRelease>", self.update_execution_tab)
        
        self.actions_frame = tk.Frame(self.frame)
        self.actions_frame.pack(fill="both", expand=True)

        execute_button = ttk.Button(self.frame, text="Ejecutar Acciones en Cadena", command=self.execute_actions)
        execute_button.pack(pady=5)

        delete_button = ttk.Button(self.frame, text="Eliminar Acción Seleccionada", command=self.delete_action)
        delete_button.pack(pady=5)

        export_button = tk.Button(self.frame, text="Exportar Imágenes", command=self.export_images)
        export_button.pack(pady=10)

        listbox_frame = tk.Frame(self.frame)
        listbox_frame.pack(fill="both", expand=True)

        self.actions_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE)
        self.actions_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=self.actions_listbox.yview)
        scrollbar.pack(side="right", fill="y")

        self.actions_listbox.configure(yscrollcommand=scrollbar.set)

        self.load_regions_for_execution()

    def load_regions_for_execution(self):
        for region in self.db.get_all_regions():
            region_frame = tk.Frame(self.actions_frame)
            region_frame.pack(pady=5, fill="x")

            label = tk.Label(region_frame, text=region[1])
            label.pack()

            click_button = ttk.Button(region_frame, text="Click", command=lambda fn=region[1]: self.add_action("Click", fn))
            click_button.pack(side="left", padx=5)

            click_and_fill_button = ttk.Button(region_frame, text="Click y Escribir", command=lambda fn=region[1]: self.add_click_and_fill_action(fn))
            click_and_fill_button.pack(side="left", padx=5)

    def update_execution_tab(self, event=None):
        for widget in self.actions_frame.winfo_children():
            widget.destroy()

        search_text = self.search_var.get().lower()

        container = tk.Frame(self.actions_frame)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        table_frame = tk.Frame(scrollable_frame)
        table_frame.pack(fill="both", expand=True)

        tk.Label(table_frame, text="Imagen", width=20, anchor="w", borderwidth=1, relief="solid").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(table_frame, text="Nombre", width=10, anchor="w", borderwidth=1, relief="solid").grid(row=0, column=1, padx=5, pady=5)
        tk.Label(table_frame, text="Threshold", width=10, anchor="w", borderwidth=1, relief="solid").grid(row=0, column=2, padx=5, pady=5)
        tk.Label(table_frame, text="Offset (X, Y)", width=15, anchor="w", borderwidth=1, relief="solid").grid(row=0, column=3, padx=5, pady=5)
        tk.Label(table_frame, text="Opciones", width=30, anchor="w", borderwidth=1, relief="solid").grid(row=0, column=4, padx=5, pady=5)

        self.execution_image_references = []

        row_index = 1
        for region in self.db.get_all_regions():
            region_name = region[1].lower()
            if search_text in region_name:
                image_data = region[7]
                offset_x, offset_y = region[9], region[10]
                if image_data:
                    image_array = np.frombuffer(image_data, np.uint8)
                    region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                    if offset_x is not None and offset_y is not None:
                        cv2.circle(region_image, (offset_x, offset_y), radius=5, color=(0, 0, 255), thickness=-1)

                    region_image_rgb = cv2.cvtColor(region_image, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(region_image_rgb)
                    img = ImageTk.PhotoImage(pil_img)

                    image_frame = tk.Frame(table_frame, borderwidth=1, relief="solid")
                    image_frame.grid(row=row_index, column=0, padx=5, pady=5)

                    image_canvas = tk.Canvas(image_frame, width=100, height=100)
                    image_canvas.pack(side="left", fill="both", expand=True)

                    scroll_x = tk.Scrollbar(image_frame, orient="horizontal", command=image_canvas.xview)
                    scroll_x.pack(side="bottom", fill="x")
                    scroll_y = tk.Scrollbar(image_frame, orient="vertical", command=image_canvas.yview)
                    scroll_y.pack(side="right", fill="y")

                    image_canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

                    image_canvas.create_image(0, 0, anchor="nw", image=img)
                    image_canvas.config(scrollregion=image_canvas.bbox("all"))

                    self.execution_image_references.append(img)

                filename_label = tk.Label(table_frame, text=str(region[1]), anchor="w", borderwidth=1, relief="solid")
                filename_label.grid(row=row_index, column=1, padx=5, pady=5)

                threshold_label = tk.Label(table_frame, text=str(region[8]), anchor="w", borderwidth=1, relief="solid")
                threshold_label.grid(row=row_index, column=2, padx=5, pady=5)

                offset_label = tk.Label(table_frame, text=f"({offset_x}, {offset_y})", anchor="w", borderwidth=1, relief="solid")
                offset_label.grid(row=row_index, column=3, padx=5, pady=5)

                options_frame = tk.Frame(table_frame, borderwidth=1, relief="solid")
                options_frame.grid(row=row_index, column=4, padx=5, pady=5)

                modify_offset_button = ttk.Button(options_frame, text="Modificar Offset", command=lambda fn=region[1]: self.modify_offset(fn))
                modify_offset_button.pack(side="left", padx=2)

                click_button = ttk.Button(options_frame, text="Click", command=lambda fn=region[1]: self.add_action("Click", fn))
                click_button.pack(side="left", padx=2)

                click_and_fill_button = ttk.Button(options_frame, text="Click y Escribir", command=lambda fn=region[1]: self.add_click_and_fill_action(fn))
                click_and_fill_button.pack(side="left", padx=2)

                wait_image_button = ttk.Button(options_frame, text="Wait Image", command=lambda fn=region[1]: self.add_action("Wait Image", fn))
                wait_image_button.pack(side="left", padx=2)

                click_download = ttk.Button(options_frame, text="Guardar Imagen", command=lambda fn=region[1]: self.download_image(fn))
                click_download.pack(side="left", padx=2)

                row_index += 1


    def add_action(self, action_type, filename):
        self.actions_queue.append((action_type, filename, ""))
        self.actions_listbox.insert(tk.END, f"{action_type} - {filename}")

    def add_click_and_fill_action(self, filename):
        text = simpledialog.askstring("Texto a Escribir", f"Ingrese el texto para {filename}:")
        if text:
            self.actions_queue.append(("Click y Escribir", filename, text))
            self.actions_listbox.insert(tk.END, f"Click y Escribir - {filename}: '{text}'")

    def delete_action(self):
        selected_index = self.actions_listbox.curselection()
        if selected_index:
            self.actions_listbox.delete(selected_index)
            del self.actions_queue[selected_index[0]]

    def execute_actions(self):
        for action_type, filename, text in self.actions_queue:
            image_data, offset_x, offset_y = self.db.get_image_data(filename)
            if image_data:
                image_array = np.frombuffer(image_data, np.uint8)
                region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if region_image is not None:
                clicker = ClickHandler(int(self.selected_monitor.get()) - 1)

                if action_type == "Click":
                    found = clicker.click_on_match(region_image, offset_x=offset_x, offset_y=offset_y)
                    if not found:
                        messagebox.showinfo("Resultado", f"No se encontraron coincidencias para {filename}.")

                elif action_type == "Click y Escribir":
                    success = clicker.click_and_type(region_image, text, offset_x=offset_x, offset_y=offset_y)
                    if not success:
                        messagebox.showinfo("Resultado", f"No se encontraron coincidencias para {filename}.")
                
                elif action_type == "Wait Image":
                    success = self.wait_for_image(filename)
                    if not success:
                        break 

            else:
                messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")

        messagebox.showinfo("Resultado", "La ejecución finalizó sin ninguna excepción.")

    def modify_offset(self, filename):
        image_data, offset_x, offset_y = self.db.get_image_data(filename)
        if image_data:
            image_array = np.frombuffer(image_data, np.uint8)
            region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if region_image is not None:
                offset_window = tk.Toplevel(self.root)
                offset_window.title("Modificar Offset")
                offset_window.geometry("400x400")

                region_image_rgb = cv2.cvtColor(region_image, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(region_image_rgb)
                tk_image = ImageTk.PhotoImage(pil_img)

                canvas = tk.Canvas(offset_window, width=pil_img.width, height=pil_img.height)
                canvas.create_image(0, 0, anchor="nw", image=tk_image)
                canvas.image = tk_image

                canvas.pack()

                new_offset = {"x": offset_x, "y": offset_y}

                def on_click(event):
                    new_offset["x"] = event.x
                    new_offset["y"] = event.y

                    canvas.delete("click_marker")
                    canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="red", tags="click_marker")

                canvas.bind("<Button-1>", on_click)

                def save_offset():
                    self.db.update_offset(filename, new_offset["x"], new_offset["y"])
                    messagebox.showinfo("Resultado", "Offset actualizado exitosamente.")
                    offset_window.destroy()
                    self.update_execution_tab()

                save_button = tk.Button(offset_window, text="Guardar Offset", command=save_offset)
                save_button.pack(pady=10)

    def wait_for_image(self, filename, timeout=30, interval=1.0):
        start_time = time.time()

        image_data = self.db.get_image_data(filename)
        if image_data:
            image_array = np.frombuffer(image_data, np.uint8)
            region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        else:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")
            return False

        if region_image is None:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")
            return False

        matcher = ImageMatcher(int(self.selected_monitor.get()) - 1)

        while time.time() - start_time < timeout:
            matched_image, found, top_left = matcher.match_image(region_image)
            if found:
                return True

            time.sleep(interval)

        messagebox.showwarning("Wait Image", f"No se detectó la imagen '{filename}' en el tiempo límite de {timeout} segundos.")
        return False
    
    def detect_match(self, filename):
        region_image = cv2.imread(filename)
        
        if region_image is not None:
            matcher = ImageMatcher(int(self.selected_monitor.get()) - 1)
            matched_image, found, top_left = matcher.match_image(region_image)

            if found:
                matched_image_rgb = cv2.cvtColor(matched_image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(matched_image_rgb)
                tk_image = ImageTk.PhotoImage(pil_image)

                match_window = tk.Toplevel(self.root)
                match_window.title("Coincidencia Encontrada")
                match_window.geometry("600x400") 

                canvas = tk.Canvas(match_window, width=600, height=400)
                scroll_x = tk.Scrollbar(match_window, orient="horizontal", command=canvas.xview)
                scroll_y = tk.Scrollbar(match_window, orient="vertical", command=canvas.yview)

                canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

                canvas.pack(side="left", fill="both", expand=True)
                scroll_x.pack(side="bottom", fill="x")
                scroll_y.pack(side="right", fill="y")

                canvas.create_image(0, 0, anchor="nw", image=tk_image)
                canvas.image = tk_image
                canvas.config(scrollregion=canvas.bbox("all"))
            else:
                messagebox.showinfo("Resultado", "No se encontraron coincidencias.")
        else:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")

    def download_image(self, filename):
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if save_path:
            try:
                image_data = self.db.get_image_data(filename)
                if isinstance(image_data, tuple):
                    image_data = image_data[0]

                if image_data:
                    image_array = np.frombuffer(image_data, np.uint8)
                    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                    if img is not None:
                        cv2.imwrite(save_path, img)
                        messagebox.showinfo("Guardado", f"Imagen guardada exitosamente en {save_path}")
                    else:
                        messagebox.showerror("Error", "No se pudo decodificar la imagen desde los datos binarios.")
                else:
                    messagebox.showerror("Error", f"No se encontró la imagen en la base de datos para el archivo: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen: {e}")

    def export_images(self):
        base_folder_path = filedialog.askdirectory(title="Selecciona la carpeta base para guardar las imágenes")
        
        if base_folder_path:
            subfolder_name = simpledialog.askstring("Nombre de Carpeta", "Ingrese el nombre de la subcarpeta para guardar las imágenes:")
            
            if subfolder_name:
                target_folder = os.path.join(base_folder_path, subfolder_name)
                os.makedirs(target_folder, exist_ok=True)

                for action_type, filename, _ in self.actions_queue:
                    image_data, _, _ = self.db.get_image_data(filename)
                    if image_data:
                        image_array = np.frombuffer(image_data, np.uint8)
                        region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                        if region_image is not None:
                            image_path = os.path.join(target_folder, f"{filename}.png")
                            cv2.imwrite(image_path, region_image)

                messagebox.showinfo("Exportación Completa", f"Todas las imágenes han sido exportadas a la carpeta '{target_folder}'.")
            else:
                messagebox.showwarning("Exportación Cancelada", "No se ingresó un nombre de subcarpeta. La exportación fue cancelada.")
        else:
            messagebox.showwarning("Exportación Cancelada", "No se seleccionó ningún directorio. La exportación fue cancelada.")