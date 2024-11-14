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
import pytesseract
from screeninfo import get_monitors

class ScreenshootView:
    def __init__(self, root: tk.Tk, notebook: Notebook):
        self.frame = tk.Frame(notebook)
        self.root = root
        notebook.add(self.frame, text="Capturar Monitor")

        self.image = None
        self.selector = None
        self.update_id = None

        self.recognized_text = ""

        self.db = DBHandler()
        self.screen_capture = ScreenCapture()

        self.selected_monitor = tk.StringVar(value="1")

        self.setup_tab_ui()

    def setup_tab_ui(self):
        screen_options_frame = tk.Frame(self.frame)
        screen_options_frame.pack(fill="x", pady=10)

        tk.Label(screen_options_frame, text="Seleccione Monitor:").pack(side="left", padx=5)
        monitor_menu = ttk.OptionMenu(screen_options_frame, self.selected_monitor, "1", *[str(i + 1) for i in range(len(get_monitors()))])
        monitor_menu.pack(side="left", padx=5)

        capture_button = ttk.Button(screen_options_frame, text="Capturar y Mostrar Monitor", command=self.show_screenshot)
        capture_button.pack(side="left", padx=5)

        fullscreen_button = ttk.Button(screen_options_frame, text="Abrir en Pantalla Completa", command=self.show_fullscreen_screenshot)
        fullscreen_button.pack(side="left", padx=5)

        display_frame = tk.Frame(self.frame)
        display_frame.pack(fill="both", expand=True)
        
        if not hasattr(self, 'regions_frame'):
            self.regions_frame = tk.Frame(self.frame)
            self.regions_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas_frame = tk.Frame(display_frame, borderwidth=1, relief="sunken")
        self.canvas_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.canvas_frame, width=500, height=500)
        self.scroll_x = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll_x.pack(side="bottom", fill="x")
        self.scroll_y.pack(side="right", fill="y")

        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        right_panel = tk.Frame(display_frame, width=250)
        right_panel.pack(side="right", fill="y", padx=10, pady=10)

        self.text_display = tk.Text(right_panel, wrap="word", width=40, height=20)
        self.text_display.pack(fill="both", expand=True)
        self.text_display.insert("1.0", "Seleccione un área para reconocer texto...")
        self.text_display.config(state="disabled")

        save_button = ttk.Button(right_panel, text="Guardar Imagen", command=self.save_region)
        save_button.pack(fill="x", pady=(10, 5))

        view_button = ttk.Button(right_panel, text="Ver Regiones", command=self.show_saved_regions)
        view_button.pack(fill="x", pady=5)

        recognize_text_button = ttk.Button(right_panel, text="Reconocer Texto en Área Seleccionada", command=self.recognize_text_in_selected_area)
        recognize_text_button.pack(fill="x", pady=5)

        self.canvas.bind("<Enter>", self._bind_mouse_scroll)
        self.canvas.bind("<Leave>", self._unbind_mouse_scroll)
        
    def show_fullscreen_screenshot(self):
        monitor_index = int(self.selected_monitor.get()) - 1
        if self.image is None:
            messagebox.showerror("Error", "No hay captura de pantalla para mostrar.")
            return

        self.fullscreen_window = tk.Toplevel(self.root)
        self.fullscreen_window.attributes("-fullscreen", True)

        self.image, _ = self.screen_capture.capture_monitor(monitor_index)
        image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        tk_image = ImageTk.PhotoImage(pil_image)

        fullscreen_canvas = tk.Canvas(self.fullscreen_window)
        fullscreen_canvas.pack(fill="both", expand=True)
        fullscreen_canvas.create_image(0, 0, anchor="nw", image=tk_image)
        fullscreen_canvas.image = tk_image

        self.fullscreen_selector = RegionSelector(fullscreen_canvas, self.image, self.update_text_display)

        close_button = ttk.Button(self.fullscreen_window, text="Cerrar", command=self.fullscreen_window.destroy)
        close_button.place(x=20, y=20)
        close_button.place_forget()

        save_button = ttk.Button(self.fullscreen_window, text="Guardar Imagen", command=self.save_and_close_fullscreen)
        save_button.place(x=20, y=60)
        save_button.place_forget()

        def toggle_buttons(event=None):
            if close_button.winfo_ismapped():
                close_button.place_forget()
                save_button.place_forget()
            else:
                close_button.place(x=20, y=20)
                save_button.place(x=20, y=60)

        self.fullscreen_window.bind("<Escape>", toggle_buttons)
        fullscreen_canvas.bind("<Button-3>", toggle_buttons)
        
        
    def save_and_close_fullscreen(self):
        if self.fullscreen_selector and self.fullscreen_selector.selected_regions:
            self.selector = self.fullscreen_selector
            self.fullscreen_window.destroy()
            self.save_region()  

    def show_screenshot(self):
        self.screen_capture = ScreenCapture()
        monitor_index = int(self.selected_monitor.get()) - 1
        try:
            self.image, _ = self.screen_capture.capture_monitor(monitor_index)
            if self.image is not None:
                image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(image_rgb)
                tk_image = ImageTk.PhotoImage(pil_image)
                self.canvas.create_image(0, 0, anchor="nw", image=tk_image)
                self.canvas.image = tk_image
                self.canvas.config(scrollregion=self.canvas.bbox("all"))

                self.selector = RegionSelector(self.canvas, self.image, self.update_text_display)
            else:
                messagebox.showerror("Error", "No se pudo capturar la imagen del monitor seleccionado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo capturar el monitor seleccionado: {e}")


        self.coord_label = tk.Label(self.canvas, text="", bg="black", fg="white", font=("Arial", 10))
        self.coord_label.place(x=10, y=10)

        def update_coordinates(event):
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.coord_label.config(text=f"X: {x}, Y: {y}")

        self.canvas.bind("<Motion>", update_coordinates)

    def save_region(self):
        if self.selector and self.selector.selected_regions:
            x1, y1, x2, y2 = self.selector.selected_regions[-1]

            filename = simpledialog.askstring("Guardar Región", "Ingrese el nombre del archivo para guardar la región:")

            if filename:
                filename = f"{filename}.png" if not filename.endswith(".png") else filename
                
                if self.db.check_region_exists(filename):
                    messagebox.showwarning("Advertencia", "Ya existe una imagen con este nombre. Por favor, elija otro nombre.")
                    return

                threshold, region_image = self.get_threshold_and_matches()
                if threshold is None or region_image is None:
                    return

                monitor_index = int(self.selected_monitor.get()) - 1
                self.select_click_offset(filename, x1, y1, x2, y2, region_image, threshold)
            else:
                messagebox.showwarning("Advertencia", "No se ingresó un nombre de archivo. Operación de guardado cancelada.")
        else:
            messagebox.showerror("Error", "No hay una región seleccionada para guardar.")

    def show_saved_regions(self):
        for widget in self.regions_frame.winfo_children():
            widget.destroy()

        def expand_window(event):
            self.root.geometry("800x800")

        search_frame = tk.Frame(self.regions_frame)
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="Buscar:").pack(side="left", padx=(5, 2))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(2, 5))
        search_entry.bind("<KeyRelease>", lambda event: self.update_filtered_regions())
        search_entry.bind("<FocusIn>", expand_window)

        canvas = tk.Canvas(self.regions_frame)
        scroll_y = tk.Scrollbar(self.regions_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.bind("<Enter>", self._bind_mouse_scroll)
        canvas.bind("<Leave>", self._unbind_mouse_scroll)

        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.scrollable_frame = scrollable_frame
        self.image_references = []

        self.update_filtered_regions()
        
    def update_filtered_regions(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        search_text = self.search_var.get().lower()
        self.image_references = []

        for region in self.db.get_all_regions():
            region_name = region[1].lower()
            if search_text in region_name:
                region_frame = tk.Frame(self.scrollable_frame, bg="white", relief="groove", bd=2)
                region_frame.pack(pady=10, padx=10, fill="x")

                label = tk.Label(region_frame, text=region[1], font=("Arial", 10, "bold"), bg="white")
                label.pack(anchor="w", padx=10, pady=5)

                image_data = region[7]

                if image_data:
                    pil_img = Image.open(io.BytesIO(image_data))
                    original_width, original_height = pil_img.size
                    max_size = 100
                    aspect_ratio = original_width / original_height

                    if original_width > original_height:
                        new_width = max_size
                        new_height = int(max_size / aspect_ratio)
                    else:
                        new_height = max_size
                        new_width = int(max_size * aspect_ratio)

                    pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                    img = ImageTk.PhotoImage(pil_img)

                    image_label = tk.Label(region_frame, image=img, bg="white")
                    image_label.pack(pady=5)
                    self.image_references.append(img)

                options_frame = tk.Frame(region_frame, bg="white")
                options_frame.pack(fill="x", pady=5)

                click_button = ttk.Button(options_frame, text="Click", command=lambda fn=region[1]: self.handle_click(fn))
                click_button.pack(side="left", padx=5, pady=5)

                click_and_fill_button = ttk.Button(options_frame, text="Click y Escribir", command=lambda fn=region[1]: self.handle_click_and_type(fn))
                click_and_fill_button.pack(side="left", padx=5, pady=5)

                click_download = ttk.Button(options_frame, text="Guardar Imagen", command=lambda fn=region[1]: self.download_image(fn))
                click_download.pack(side="left", padx=5, pady=5)

                click_delete = ttk.Button(options_frame, text="Eliminar", command=lambda fn=region[1]: self.delete_region(fn))
                click_delete.pack(side="left", padx=5, pady=5)

                detect_button = ttk.Button(options_frame, text="Detectar", command=lambda fn=region[1]: self.detect_all_matches_with_threshold(fn))
                detect_button.pack(side="left", padx=5, pady=5)

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

        region_coords = self.selector.selected_regions[-1]
        region_image = self.screen_capture.get_region_image(region_coords)

        def schedule_display_update(threshold):
            if self.update_id is not None:
                threshold_window.after_cancel(self.update_id)

            self.update_id = threshold_window.after(200, lambda: display_image_with_matches(threshold))

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

        threshold_slider.config(command=lambda value: schedule_display_update(float(value)))

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

        def schedule_update_matches(threshold):
            if self.update_id is not None:
                detect_window.after_cancel(self.update_id)


            self.update_id = detect_window.after(200, lambda: update_matches(threshold))

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
                                    label="Threshold de Coincidencia", command=lambda value: schedule_update_matches(float(value)))
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

                self.db.insert_region(
                    filename, x1, y1, x2, y2, image_data=image_data, threshold=threshold,
                    click_offset=(click_offset["x"], click_offset["y"])
                )

                offset_window.destroy()
                offset_window.after(500, lambda: messagebox.showinfo("Guardado", f"Región y punto de clic guardados exitosamente en la base de datos como {filename}"))
            else:
                messagebox.showwarning("Advertencia", "Por favor, seleccione un punto de clic antes de confirmar.")

        confirm_button = tk.Button(offset_window, text="Confirmar Punto de Clic", command=confirm_click_offset)
        confirm_button.pack(pady=10)

    def _bind_mouse_scroll(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

    def _unbind_mouse_scroll(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def recognize_text_in_selected_area(self):
        if self.selected_region:
            x1, y1, x2, y2 = self.selected_regions[-1]
            selected_region = self.image[y1:y2, x1:x2]

            if selected_region.size == 0:
                print("La región seleccionada está vacía.")
                return

            try:
                gray_region = cv2.cvtColor(selected_region, cv2.COLOR_BGR2GRAY)
                recognized_text = pytesseract.image_to_string(gray_region)
                self.update_text_callback(recognized_text)
            except cv2.error as e:
                print(f"Error al convertir a escala de grises: {e}")
            
    def recognize_text_in_region(self):
        if self.selected_regions:
            x1, y1, x2, y2 = self.selected_regions[-1]
            selected_region = self.image[y1:y2, x1:x2]

            if selected_region.size == 0:
                print("La región seleccionada está vacía.")
                return

            try:
                gray_region = cv2.cvtColor(selected_region, cv2.COLOR_BGR2GRAY)
                recognized_text = pytesseract.image_to_string(gray_region)
                self.update_text_callback(recognized_text)
            except cv2.error as e:
                print(f"Error al convertir a escala de grises: {e}")

    def show_text_confirmation(self, x1, y1, x2, y2, selected_region):
        confirmation_window = tk.Toplevel(self.root)
        confirmation_window.title("Confirmar Texto Reconocido")

        coords_text = f"({x1}, {y1}, {x2-x1}, {y2-y1})"
        coords_label = tk.Label(confirmation_window, text=coords_text)
        coords_label.pack(pady=5)

        copy_button = ttk.Button(confirmation_window, text="Copiar Coordenadas", command=lambda: self.copy_to_clipboard(coords_text))
        copy_button.pack(pady=5)

        text_box = tk.Text(confirmation_window, wrap="word", width=50, height=10)
        text_box.insert("1.0", self.recognized_text)
        text_box.config(state="disabled")
        text_box.pack(pady=10)

        save_button = ttk.Button(confirmation_window, text="Guardar", command=lambda: self.save_text_and_region(x1, y1, x2, y2, selected_region, confirmation_window))
        save_button.pack(side="left", padx=10)

        cancel_button = ttk.Button(confirmation_window, text="Cancelar", command=confirmation_window.destroy)
        cancel_button.pack(side="right", padx=10)

    def copy_to_clipboard(self, text):
        """Copia el texto al portapapeles del sistema."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copiado", "Coordenadas copiadas al portapapeles.")

    def save_text_and_region(self, x1, y1, x2, y2, selected_region, confirmation_window):
        filename = simpledialog.askstring("Guardar Región", "Ingrese el nombre del archivo para guardar la región:")
        if filename:
            filename = f"{filename}.png" if not filename.endswith(".png") else filename
            _, buffer = cv2.imencode('.png', selected_region)
            image_data = buffer.tobytes()
            threshold = 0.8

            self.db.insert_region_with_recognition(filename, x1, y1, x2, y2, image_data, threshold, self.recognized_text)

            messagebox.showinfo("Guardado", f"Región guardada exitosamente como '{filename}'")
            confirmation_window.destroy()
        else:
            messagebox.showwarning("Advertencia", "No se ingresó un nombre de archivo. Operación de guardado cancelada.")

    def update_text_display(self, text):
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", tk.END)
        if text.strip():
            self.text_display.insert("1.0", text)
        else:
            self.text_display.insert("1.0", "No hay texto reconocible en la región seleccionada.")
        self.text_display.config(state="disabled")