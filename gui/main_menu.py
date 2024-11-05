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
import time
from .styles import Styles

class MainMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Detector Test tool")
        self.root.geometry("1000x600")
        self.db = DBHandler()
        self.actions_queue = []
        self.styles = Styles()


        self.screen_capture = ScreenCapture()
        self.selected_monitor = tk.StringVar(value="1")

        self._setup_ui()

    def _setup_ui(self):

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.tab1 = tk.Frame(notebook)
        notebook.add(self.tab1, text="Seleccionar y Ver Regiones")

        self.tab2 = tk.Frame(notebook)
        notebook.add(self.tab2, text="Ejecución en Cadena")

        notebook.bind("<<NotebookTabChanged>>", lambda event: self.on_tab_selected(event, notebook))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(self.tab2, textvariable=self.search_var)
        search_entry.pack(pady=5, fill="x")
        search_entry.bind("<KeyRelease>", self.update_execution_tab)

        ttk.Label(self.tab1, text="Seleccione Monitor").pack(pady=10)

        monitor_menu = ttk.OptionMenu(self.tab1, self.selected_monitor, "1", *[str(i + 1) for i in range(len(self.screen_capture.get_monitors()))])
        monitor_menu.pack(pady=1)

        capture_button = ttk.Button(self.tab1, text="Capturar y Mostrar Monitor", command=self.show_screenshot)
        self.styles.apply_style(capture_button, "Custom.TButton")
        capture_button.pack(pady=10)

        self.canvas_frame = tk.Frame(self.tab1)
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame)
        self.scroll_x = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        self.scroll_x.pack(side="bottom", fill="x")
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.regions_frame = tk.Frame(self.tab1)
        self.styles.apply_style(self.regions_frame, "Custom.TFrame")
        self.regions_frame.pack(fill="both", expand=True)

        save_button = ttk.Button(self.tab1, text="Guardar Imagen", command=self.save_region)
        save_button.pack(pady=5)
        view_button = ttk.Button(self.tab1, text="Ver Regiones", command=self.show_saved_regions)
        view_button.pack(pady=5)

        self.setup_execution_tab()

    def on_tab_selected(self, event, notebook):
        selected_tab = notebook.index(notebook.select())
        if selected_tab == 1:
            self.update_execution_tab()


    def setup_execution_tab(self):
        self.actions_frame = tk.Frame(self.tab2)
        self.actions_frame.pack(fill="both", expand=True)

        execute_button = ttk.Button(self.tab2, text="Ejecutar Acciones en Cadena", command=self.execute_actions)
        execute_button.pack(pady=5)

        delete_button = ttk.Button(self.tab2, text="Eliminar Acción Seleccionada", command=self.delete_action)
        delete_button.pack(pady=5)

        self.actions_listbox = tk.Listbox(self.tab2, selectmode=tk.SINGLE)
        self.actions_listbox.pack(fill="both", expand=True)

        self.load_regions_for_execution()

    def load_regions_for_execution(self):
        for region in self.db.get_all_regions():
            region_frame = tk.Frame(self.actions_frame)
            region_frame.pack(pady=5, fill="x")

            label = tk.Label(region_frame, text=region[1])
            label.pack()

            click_button = ttk.Button(region_frame, text="Click", command=lambda fn=region[1]: self.add_action("Click", fn))
            click_button.pack(side="left", padx=5)

            click_and_fill_button = ttk.Button(region_frame, text="Click y Llenar", command=lambda fn=region[1]: self.add_click_and_fill_action(fn))
            click_and_fill_button.pack(side="left", padx=5)

    def add_action(self, action_type, filename):
        self.actions_queue.append((action_type, filename, ""))
        self.actions_listbox.insert(tk.END, f"{action_type} - {filename}")

    def add_click_and_fill_action(self, filename):
        text = simpledialog.askstring("Texto a Escribir", f"Ingrese el texto para {filename}:")
        if text:
            self.actions_queue.append(("Click y Llenar", filename, text))
            self.actions_listbox.insert(tk.END, f"Click y Llenar - {filename}: '{text}'")

    def delete_action(self):
        selected_index = self.actions_listbox.curselection()
        if selected_index:
            self.actions_listbox.delete(selected_index)
            del self.actions_queue[selected_index[0]]

    def execute_actions(self):
        for action_type, filename, text in self.actions_queue:
            region_image = cv2.imread(filename)

            if region_image is not None:
                clicker = ClickHandler(int(self.selected_monitor.get()) - 1)

                if action_type == "Click":
                    found = clicker.click_on_match(region_image)
                    if not found:
                        messagebox.showinfo("Resultado", f"No se encontraron coincidencias para {filename}.")

                elif action_type == "Click y Llenar":
                    success = clicker.click_and_type(region_image, text)
                    if not success:
                        messagebox.showinfo("Resultado", f"No se encontraron coincidencias para {filename}.")
                
                elif action_type == "Wait Image":
                    success = self.wait_for_image(filename)
                    if not success:
                        break 

            else:
                messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")



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

            pil_img = Image.open(region[1])
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

            click_delete = ttk.Button(options_frame, text="Click y Llenar", command=lambda fn=region[1]: self.delete_region(fn))
            click_delete.pack(side="left", padx=5)

            detect_button = ttk.Button(options_frame, text="Detectar", command=lambda fn=region[1]: self.detect_all_matches_with_threshold(fn))
            detect_button.pack(side="left", padx=5)

            detect_button = ttk.Button(options_frame, text="Eliminar", command=lambda fn=region[1]: self.delete_region(fn))
            detect_button.pack(side="left", padx=5)


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
                img = cv2.imread(filename)
                cv2.imwrite(save_path, img)
                messagebox.showinfo("Guardado", f"Imagen guardada exitosamente en {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen: {e}")



    def handle_click(self, filename):
        # Leer la imagen de la región
        region_image = cv2.imread(filename)
        
        if region_image is not None:
            # Crear una instancia de ClickHandler y buscar coincidencias
            clicker = ClickHandler(int(self.selected_monitor.get()) - 1)
            found = clicker.click_on_match(region_image)

            if found:
                messagebox.showinfo("Resultado", "Coincidencia encontrada y clic realizado.")
            else:
                messagebox.showwarning("Resultado", "No se encontraron coincidencias en pantalla para realizar el clic.")
        else:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")


    def handle_click_and_type(self, filename):
        region_image = cv2.imread(filename)
        
        if region_image is not None:
            text = simpledialog.askstring("Texto a Escribir", "Ingrese el texto que desea escribir:")
            if text:
                clicker = ClickHandler(int(self.selected_monitor.get()) - 1)
                success = clicker.click_and_type(region_image, text)

                if success:
                    messagebox.showinfo("Resultado", "Coincidencia encontrada, clic realizado y texto escrito.")
                else:
                    messagebox.showinfo("Resultado", "No se encontraron coincidencias.")
            else:
                messagebox.showwarning("Advertencia", "No se ingresó texto para escribir.")
        else:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")

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

    def save_region(self):
        if self.selector.selected_regions:
            x1, y1, x2, y2 = self.selector.selected_regions[-1]

            filename = simpledialog.askstring("Guardar Región", "Ingrese el nombre del archivo para guardar la región:")

            if filename:
                filename = f"img/{filename}.png" if not filename.endswith(".png") else filename

                region = self.image[y1:y2, x1:x2]

                cv2.imwrite(filename, region)
                messagebox.showinfo("Guardado", f"Región guardada exitosamente como {filename}")

                self.db.insert_region(filename, x1, y1, x2, y2)
            else:
                messagebox.showwarning("Advertencia", "No se ingresó un nombre de archivo. Operación de guardado cancelada.")
        else:
            messagebox.showerror("Error", "No hay una región seleccionada para guardar.")


    def update_execution_tab(self, event=None):

        for widget in self.actions_frame.winfo_children():
            widget.destroy()

        search_text = self.search_var.get().lower()

        canvas = tk.Canvas(self.actions_frame)
        scroll_y = tk.Scrollbar(self.actions_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.execution_image_references = []

        for region in self.db.get_all_regions():
            region_name = region[1].lower()
            if search_text in region_name:
                region_frame = tk.Frame(scrollable_frame)
                region_frame.pack(pady=5, fill="x")

                pil_img = Image.open(region[1])
                img = ImageTk.PhotoImage(pil_img)
                image_label = tk.Label(region_frame, image=img)
                image_label.pack(side="left", padx=5)

                self.execution_image_references.append(img)

                options_frame = tk.Frame(region_frame)
                options_frame.pack(side="left")

                label = tk.Label(options_frame, text=region[1])
                label.pack()

                click_button = ttk.Button(options_frame, text="Click", command=lambda fn=region[1]: self.add_action("Click", fn))
                click_button.pack(side="left", padx=5)

                click_and_fill_button = ttk.Button(options_frame, text="Click y Llenar", command=lambda fn=region[1]: self.add_click_and_fill_action(fn))
                click_and_fill_button.pack(side="left", padx=5)

                wait_image_button = ttk.Button(options_frame, text="Wait Image", command=lambda fn=region[1]: self.add_action("Wait Image", fn))
                wait_image_button.pack(side="left", padx=5)


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

    

    def wait_for_image(self, filename, timeout=30, interval=1.0):
        start_time = time.time()

        region_image = cv2.imread(filename)
        if region_image is None:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")
            return False
        
        matcher = ImageMatcher(int(self.selected_monitor.get()) - 1)
        while time.time() - start_time < timeout:
            matched_image, found, top_left = matcher.match_image(region_image)
            if found:
                return True
            time.sleep(interval)

        messagebox.showwarning("Wait Image", f"No se detectó la imagen {filename} en el tiempo límite.")
        return False
    
    def detect_match_in_screenshot(self, filename):
        # Leer la imagen de la región seleccionada
        region_image = cv2.imread(filename)
        
        if region_image is not None:
            # Capturar la pantalla del monitor seleccionado
            monitor_index = int(self.selected_monitor.get()) - 1
            try:
                screenshot, monitor_info = self.screen_capture.capture_monitor(monitor_index)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo capturar el monitor seleccionado: {e}")
                return

            # Crear una instancia de ImageMatcher para buscar la coincidencia
            matcher = ImageMatcher(monitor_index)
            matched_image, found, top_left = matcher.match_image(region_image)

            if found:
                # Dibujar un rectángulo alrededor de la coincidencia
                bottom_right = (top_left[0] + region_image.shape[1], top_left[1] + region_image.shape[0])
                cv2.rectangle(matched_image, top_left, bottom_right, (0, 255, 0), 3)

                # Convertir la imagen de OpenCV a un formato compatible con tkinter (PIL)
                matched_image_rgb = cv2.cvtColor(matched_image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(matched_image_rgb)
                tk_image = ImageTk.PhotoImage(pil_image)

                # Crear una ventana de tkinter para mostrar la coincidencia
                match_window = tk.Toplevel(self.root)
                match_window.title("Coincidencia Detectada")
                match_window.geometry("600x400")  # Tamaño fijo de la ventana

                # Crear un canvas con barras de desplazamiento para mostrar la coincidencia
                canvas = tk.Canvas(match_window, width=600, height=400)
                scroll_x = tk.Scrollbar(match_window, orient="horizontal", command=canvas.xview)
                scroll_y = tk.Scrollbar(match_window, orient="vertical", command=canvas.yview)

                canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

                # Posicionar canvas y barras de desplazamiento en la ventana
                canvas.pack(side="left", fill="both", expand=True)
                scroll_x.pack(side="bottom", fill="x")
                scroll_y.pack(side="right", fill="y")

                # Agregar la imagen al canvas y configurar el área desplazable
                canvas.create_image(0, 0, anchor="nw", image=tk_image)
                canvas.image = tk_image  # Mantener una referencia a la imagen
                canvas.config(scrollregion=canvas.bbox("all"))
            else:
                messagebox.showwarning("Detectar", "No se encontró ninguna coincidencia en la captura actual.")
        else:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")

    def detect_all_matches_with_threshold(self, filename):
        region_image = cv2.imread(filename)
        
        if region_image is None:
            messagebox.showerror("Error", f"No se pudo cargar la imagen de la región: {filename}")
            return

        monitor_index = int(self.selected_monitor.get()) - 1
        try:
            screenshot, monitor_info = self.screen_capture.capture_monitor(monitor_index)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo capturar el monitor seleccionado: {e}")
            return

        # Crear una ventana de tkinter para mostrar las coincidencias y el slider de umbral
        detect_window = tk.Toplevel(self.root)
        detect_window.title("Detectar Coincidencias")
        detect_window.geometry("800x600")

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

        threshold_slider = tk.Scale(detect_window, from_=0.5, to=1.0, resolution=0.01, orient="horizontal", label="Threshold de Coincidencia", command=update_matches)
        threshold_slider.set(0.8)
        threshold_slider.pack(side="bottom", fill="x")

        update_matches(threshold_slider.get())



    def run(self):
        self.root.mainloop()
