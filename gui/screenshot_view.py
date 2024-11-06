import tkinter as tk
from tkinter.ttk import Notebook
import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import ttk
from database.db_handler import DBHandler
from tkinter import ttk, messagebox, simpledialog, filedialog
from utils.click_handler import ClickHandler
from screenshot.selector import RegionSelector
from screenshot.capture import ScreenCapture
import io
from utils.image_matcher import ImageMatcher
import os


class ScreenshootView:
    def __init__(self, root: tk.Tk, notebook: Notebook):
        self.frame = tk.Frame(notebook)
        self.root = root
        notebook.add(self.frame, text="Ejecución en Cadena")

        self.db = DBHandler()
        self.screen_capture = ScreenCapture()

        self.selected_monitor = tk.StringVar(value="1")

        self.setup_tab_ui()

    def setup_tab_ui(self):

        ttk.Label(self.frame, text="Seleccione Monitor").pack(pady=10)
        monitor_menu = ttk.OptionMenu(self.frame, self.selected_monitor, "1", *[str(i + 1) for i in range(len(self.screen_capture.get_monitors()))])
        monitor_menu.pack(pady=1)

        capture_button = ttk.Button(self.frame, text="Capturar y Mostrar Monitor", command=self.show_screenshot)
        capture_button.pack(pady=10)

        self.canvas_frame = tk.Frame(self.frame)
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame)
        self.scroll_x = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        self.scroll_x.pack(side="bottom", fill="x")
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.regions_frame = tk.Frame(self.frame)
        self.regions_frame.pack(fill="both", expand=True)

        save_button = ttk.Button(self.frame, text="Guardar Imagen", command=self.save_region)
        save_button.pack(pady=5)
        view_button = ttk.Button(self.frame, text="Ver Regiones", command=self.show_saved_regions)
        view_button.pack(pady=5)

    def show_screenshot(self):
        monitor_index = int(self.selected_monitor.get()) - 1
        try:
            image, monitor_info = self.screen_capture.capture_monitor(monitor_index)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo capturar el monitor seleccionado: {e}")
            return

        self.root.geometry(f"{monitor_info['width']}x{monitor_info['height']}")
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        tk_image = ImageTk.PhotoImage(pil_image)

        self.canvas.create_image(0, 0, anchor="nw", image=tk_image)
        self.canvas.image = tk_image
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.selector = RegionSelector(self.canvas)
        self.image = image

        self.coord_label = tk.Label(self.canvas, text="", bg="black", fg="white", font=("Arial", 10))
        self.coord_label.place(x=10, y=10)

        def update_coordinates(event):
            x = event.x
            y = event.y
            self.coord_label.config(text=f"X: {x}, Y: {y}")

        self.canvas.bind("<Motion>", update_coordinates)

    def save_region(self):
        if self.selector.selected_regions:
            x1, y1, x2, y2 = self.selector.selected_regions[-1]

            filename = simpledialog.askstring("Guardar Región", "Ingrese el nombre del archivo para guardar la región:")

            if filename:
                threshold, region_image = self.get_threshold_and_matches()
                if threshold is None or region_image is None:
                    return

                filename = f"{filename}.png" if not filename.endswith(".png") else filename

                self.select_click_offset(filename, x1, y1, x2, y2, region_image, threshold)
            else:
                messagebox.showwarning("Advertencia", "No se ingresó un nombre de archivo. Operación de guardado cancelada.")
        else:
            messagebox.showerror("Error", "No hay una región seleccionada para guardar.")

    def show_saved_regions(self):
        for widget in self.regions_frame.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(self.regions_frame)
        scroll_y = tk.Scrollbar(self.regions_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.image_references = []

        for region in self.db.get_all_regions():
            region_frame = tk.Frame(scrollable_frame)
            region_frame.pack(pady=5, fill="x")

            label = tk.Label(region_frame, text=region[1])
            label.pack()

            image_data = region[7]

            if image_data:
                pil_img = Image.open(io.BytesIO(image_data))
                img = ImageTk.PhotoImage(pil_img)
                image_label = tk.Label(region_frame, image=img)
                image_label.pack()

                self.image_references.append(img)

            options_frame = tk.Frame(region_frame)
            options_frame.pack()

            click_button = ttk.Button(options_frame, text="Click", command=lambda fn=region[1]: self.handle_click(fn))
            click_button.pack(side="left", padx=5)

            click_and_fill_button = ttk.Button(options_frame, text="Click y Escribir", command=lambda fn=region[1]: self.handle_click_and_type(fn))
            click_and_fill_button.pack(side="left", padx=5)

            click_download = ttk.Button(options_frame, text="Guardar Imagen", command=lambda fn=region[1]: self.download_image(fn))
            click_download.pack(side="left", padx=5)

            click_delete = ttk.Button(options_frame, text="Eliminar", command=lambda fn=region[1]: self.delete_region(fn))
            click_delete.pack(side="left", padx=5)

            detect_button = ttk.Button(options_frame, text="Detectar", command=lambda fn=region[1]: self.detect_all_matches_with_threshold(fn))
            detect_button.pack(side="left", padx=5)

    def get_threshold_and_matches(self):
        """Muestra una ventana con un slider para ajustar el threshold y visualizar coincidencias en la captura de pantalla completa."""
        threshold_window = tk.Toplevel(self.root)
        threshold_window.title("Seleccionar Threshold")
        threshold_window.geometry("1000x1000")
        
        threshold_var = tk.DoubleVar(value=0.8)  
        tk.Label(threshold_window, text="Seleccione el threshold de coincidencia:").pack(pady=10)
        threshold_slider = tk.Scale(threshold_window, from_=0.5, to=1.0, resolution=0.01, orient="horizontal", variable=threshold_var)
        threshold_slider.pack()

        image_frame = tk.Frame(threshold_window)
        image_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(image_frame, width=780, height=500)
        scroll_x = tk.Scrollbar(image_frame, orient="horizontal", command=canvas.xview)
        scroll_y = tk.Scrollbar(image_frame, orient="vertical", command=canvas.yview)
        
        canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        monitor_index = int(self.selected_monitor.get()) - 1
        screen_image, _ = self.screen_capture.capture_monitor(monitor_index)

        def display_image_with_matches(threshold):
            matcher = ImageMatcher(monitor_index)
            matched_image, found_points, _ = matcher.match_image_with_threshold(screen_image, region_image, threshold)
            
            matched_image_rgb = cv2.cvtColor(matched_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(matched_image_rgb)
            tk_image = ImageTk.PhotoImage(pil_image)
            
            canvas.create_image(0, 0, anchor="nw", image=tk_image)
            canvas.image = tk_image
            canvas.config(scrollregion=canvas.bbox("all"))

            count_label.config(text=f"Coincidencias encontradas: {len(found_points)}")

        region_image = self.screen_capture.get_region_image(self.selector.selected_regions[-1])

        threshold_slider.config(command=lambda value: display_image_with_matches(float(value)))

        count_label = tk.Label(threshold_window, text="Coincidencias encontradas: 0")
        count_label.pack()

        confirm = tk.Button(threshold_window, text="Confirmar", command=threshold_window.destroy)
        confirm.pack(pady=10)

        threshold_window.transient(self.root)
        threshold_window.grab_set()
        self.root.wait_window(threshold_window)

        return threshold_var.get(), region_image
    
    def handle_click(self, filename):
        image_data, offset_x, offset_y = self.db.get_image_data(filename)
        
        if image_data:
            image_array = np.frombuffer(image_data, np.uint8)
            region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if region_image is not None:
                clicker = ClickHandler(int(self.selected_monitor.get()) - 1)
                found = clicker.click_on_match(region_image, offset_x=offset_x, offset_y=offset_y)

                if found:
                    messagebox.showinfo("Resultado", "Coincidencia encontrada y clic realizado.")
                else:
                    messagebox.showwarning("Resultado", "No se encontraron coincidencias en pantalla para realizar el clic.")
            else:
                messagebox.showerror("Error", "No se pudo decodificar la imagen de la región.")
        else:
            messagebox.showerror("Error", f"No se encontró la imagen en la base de datos para el archivo: {filename}")


    def handle_click_and_type(self, filename):
        image_data, offset_x, offset_y = self.db.get_image_data(filename)
        if image_data:
            image_array = np.frombuffer(image_data, np.uint8)
            region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if region_image is not None:
                text = simpledialog.askstring("Texto a Escribir", "Ingrese el texto que desea escribir:")
                if text:
                    clicker = ClickHandler(int(self.selected_monitor.get()) - 1)
                    success = clicker.click_and_type(region_image, text, offset_x=offset_x, offset_y=offset_y)

                    if success:
                        messagebox.showinfo("Resultado", "Coincidencia encontrada, clic realizado y texto escrito.")
                    else:
                        messagebox.showinfo("Resultado", "No se encontraron coincidencias.")
                else:
                    messagebox.showwarning("Advertencia", "No se ingresó texto para escribir.")
            else:
                messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")

    def download_image(self, filename):
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if save_path:
            try:
                image_data = self.db.get_image_data(filename)

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

    def delete_region(self, filename):
        confirm = messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar la región {filename}?")
        
        if confirm:
            try:
                if os.path.exists(filename):
                    os.remove(filename)

                self.db.delete_region(filename)

                self.show_saved_regions()
                messagebox.showinfo("Eliminado", f"La región {filename} se ha eliminado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar la región {filename}: {e}")

    def detect_all_matches_with_threshold(self, filename):
        image_data, saved_threshold = self.db.get_image_data_and_threshold(filename)
        if image_data:
            image_array = np.frombuffer(image_data, np.uint8)
            region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if region_image is None:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")
            return

        monitor_index = int(self.selected_monitor.get()) - 1
        try:
            screenshot, monitor_info = self.screen_capture.capture_monitor(monitor_index)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo capturar el monitor seleccionado: {e}")
            return

        detect_window = tk.Toplevel(self.root)
        detect_window.title("Detectar Coincidencias")
        detect_window.geometry("1000x1000")

        canvas = tk.Canvas(detect_window, width=800, height=550)
        scroll_x = tk.Scrollbar(detect_window, orient="horizontal", command=canvas.xview)
        scroll_y = tk.Scrollbar(detect_window, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        canvas.pack(side="top", fill="both", expand=True)
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right", fill="y")

        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(screenshot_rgb)
        tk_image = ImageTk.PhotoImage(pil_image)

        match_count_label = tk.Label(detect_window, text="Coincidencias encontradas: 0")
        match_count_label.pack()

        def update_matches(threshold):
            match_image = screenshot.copy()
            matcher = ImageMatcher(monitor_index)
            all_matches = matcher.find_all_matches(region_image, match_image, float(threshold))

            for (top_left, bottom_right) in all_matches:
                cv2.rectangle(match_image, top_left, bottom_right, (0, 255, 0), 3)

            match_image_rgb = cv2.cvtColor(match_image, cv2.COLOR_BGR2RGB)
            pil_match_image = Image.fromarray(match_image_rgb)
            tk_match_image = ImageTk.PhotoImage(pil_match_image)

            canvas.create_image(0, 0, anchor="nw", image=tk_match_image)
            canvas.image = tk_match_image
            canvas.config(scrollregion=canvas.bbox("all"))

            match_count_label.config(text=f"Coincidencias encontradas: {len(all_matches)}")

        threshold_slider = tk.Scale(detect_window, from_=0.5, to=1.0, resolution=0.01, orient="horizontal",
                                    label="Threshold de Coincidencia", command=update_matches)
        threshold_slider.set(saved_threshold if saved_threshold is not None else 0.8)
        threshold_slider.pack(side="bottom", fill="x")

        def save_threshold():
            new_threshold = threshold_slider.get()
            self.db.update_threshold(filename, new_threshold)
            messagebox.showinfo("Threshold Guardado", f"El threshold ha sido actualizado a {new_threshold}.")

        save_button = tk.Button(detect_window, text="Guardar Threshold", command=save_threshold)
        save_button.pack(side="bottom", pady=10)

        update_matches(threshold_slider.get())

    def select_click_offset(self, filename, x1, y1, x2, y2, region_image, threshold):
        """
        Muestra la región seleccionada y permite al usuario seleccionar el punto de clic.
        """
        offset_window = tk.Toplevel(self.root)
        offset_window.title("Seleccionar Punto de Clic")
        offset_window.geometry("400x400")

        region_rgb = cv2.cvtColor(region_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(region_rgb)
        tk_image = ImageTk.PhotoImage(pil_image)

        canvas = tk.Canvas(offset_window, width=pil_image.width, height=pil_image.height)
        canvas.create_image(0, 0, anchor="nw", image=tk_image)
        canvas.image = tk_image

        canvas.pack()

        click_offset = {"x": None, "y": None}

        def on_click(event):
            click_offset["x"] = event.x
            click_offset["y"] = event.y

            canvas.delete("click_marker")
            canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="red", tags="click_marker")

        canvas.bind("<Button-1>", on_click)

        def confirm_click_offset():
            if click_offset["x"] is not None and click_offset["y"] is not None:
                _, buffer = cv2.imencode('.png', region_image)
                image_data = buffer.tobytes()

                self.db.insert_region(filename, x1, y1, x2, y2, image_data=image_data, threshold=threshold,
                                    click_offset=(click_offset["x"], click_offset["y"]))
                messagebox.showinfo("Guardado", f"Región y punto de clic guardados exitosamente en la base de datos como {filename}")
                offset_window.destroy()
            else:
                messagebox.showwarning("Advertencia", "Por favor, seleccione un punto de clic antes de confirmar.")

        confirm_button = tk.Button(offset_window, text="Confirmar Punto de Clic", command=confirm_click_offset)
        confirm_button.pack(pady=10)