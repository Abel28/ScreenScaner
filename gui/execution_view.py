import tkinter as tk
from tkinter.ttk import Notebook
import cv2
import numpy as np
from PIL import Image, ImageTk
from database.db_handler import DBHandler
from tkinter import ttk, messagebox, simpledialog, filedialog
from utils.click_handler import ClickHandler
from utils.image_matcher import ImageMatcher
import time
import os
from .screenshot_view import ScreenCapture
from screeninfo import get_monitors

from tkinter import ttk, Menu


class ExecutionView:
    def __init__(self, root: tk.Tk, notebook: Notebook):
        self.frame = tk.Frame(notebook)
        self.root = root
        notebook.add(self.frame, text="Ejecución")

        self.selected_monitor = tk.StringVar(value="1")
        self.screen_capture = ScreenCapture()

        self.db = DBHandler()
        self.actions_queue = []

        self.update_id = None

        self.setup_execution_tab()

    def setup_execution_tab(self):
        top_frame = tk.Frame(self.frame, pady=10)
        top_frame.pack(fill="x")

        if not hasattr(self, "actions_frame"):
            self.actions_frame = tk.Frame(self.frame)
        self.actions_frame.pack(fill="both", expand=True)

        import_button = tk.Button(
            top_frame, text="Importar Imagen", command=self.import_image
        )
        import_button.pack(side="left", padx=10)

        tk.Label(top_frame, text="Buscar:").pack(side="left", padx=(10, 5))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(top_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
        search_entry.bind("<KeyRelease>", self.update_execution_tab)

        actions_frame = tk.Frame(self.frame, pady=10)
        actions_frame.pack(fill="x")

        execute_button = ttk.Button(
            actions_frame,
            text="Ejecutar Acciones en Cadena",
            command=self.execute_actions,
        )
        execute_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        delete_button = ttk.Button(
            actions_frame,
            text="Eliminar Acción Seleccionada",
            command=self.delete_action,
        )
        delete_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        export_button = ttk.Button(
            actions_frame, text="Exportar Imágenes", command=self.export_images
        )
        export_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        actions_frame.grid_columnconfigure(2, weight=1)

        listbox_frame = tk.Frame(self.frame, pady=10)
        listbox_frame.pack(fill="both", expand=True)

        self.actions_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE)
        self.actions_listbox.pack(
            side="left", fill="both", expand=True, padx=(10, 0), pady=5
        )

        scrollbar = tk.Scrollbar(
            listbox_frame, orient="vertical", command=self.actions_listbox.yview
        )
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=5)

        self.actions_listbox.configure(yscrollcommand=scrollbar.set)
        self.update_execution_tab()

    def import_image(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                image = cv2.imread(file_path)
                if image is None:
                    messagebox.showerror(
                        "Error", "No se pudo cargar la imagen seleccionada."
                    )
                    return

                base_filename = os.path.basename(file_path)
                filename = os.path.splitext(base_filename)[0]
                ext = os.path.splitext(base_filename)[1]

                filename = self.get_unique_filename(filename, ext)

                self.db.insert_region_from_import(filename=filename, image=image)

                self.update_execution_tab()

                messagebox.showinfo(
                    "Importación exitosa",
                    f"La imagen '{filename}{ext}' ha sido importada exitosamente y guardada en la base de datos.",
                )

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo importar la imagen: {e}")

    def get_unique_filename(self, filename, ext):
        """Devuelve un nombre de archivo único agregando un sufijo si ya existe."""
        original_filename = filename
        suffix = 1

        while self.db.check_region_exists(f"{filename}{ext}"):
            filename = f"{original_filename}_{suffix}"
            suffix += 1

        return f"{filename}{ext}"

    def load_regions_for_execution(self):
        for widget in self.actions_frame.winfo_children():
            widget.destroy()

        regions_container = tk.Frame(self.actions_frame)
        regions_container.pack(fill="both", expand=True)

        for region in self.db.get_all_regions():
            region_frame = tk.Frame(
                regions_container, pady=5, padx=10, relief="solid", borderwidth=1
            )
            region_frame.pack(fill="x", pady=5)

            label = tk.Label(region_frame, text=region[1], anchor="w")
            label.pack(side="left", padx=(10, 5))

            click_button = ttk.Button(
                region_frame,
                text="Click",
                command=lambda fn=region[1]: self.add_action("Click", fn),
            )
            click_button.pack(side="left", padx=5)

            click_and_fill_button = ttk.Button(
                region_frame,
                text="Click y Escribir",
                command=lambda fn=region[1]: self.add_click_and_fill_action(fn),
            )
            click_and_fill_button.pack(side="left", padx=5)

        self.actions_frame.update_idletasks()

    def update_execution_tab(self, event=None):
        for widget in self.actions_frame.winfo_children():
            widget.destroy()

        search_text = self.search_var.get().lower()

        container = tk.Frame(self.actions_frame)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#f4f4f4")
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f4f4f4")

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        container.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(0, weight=1)

        headers = ["Imagen", "Nombre", "Threshold", "Offset (X, Y)", "Opciones"]
        header_frame = tk.Frame(scrollable_frame, bg="#d9d9d9", relief="raised", bd=1)
        header_frame.pack(fill="x", pady=(0, 5))

        for idx, header in enumerate(headers):
            tk.Label(
                header_frame,
                text=header,
                anchor="center",
                bg="#d9d9d9",
                font=("Arial", 10, "bold"),
            ).grid(row=0, column=idx, padx=5, pady=5, sticky="nsew")

        for idx in range(len(headers)):
            header_frame.grid_columnconfigure(idx, weight=1)

        self.options_menu = None

        self.execution_image_references = []
        row_index = 1
        for region in self.db.get_all_regions():
            region_name = region[1].lower()
            if search_text in region_name:
                image_data = region[7]
                offset_x, offset_y = region[9], region[10]

                row_frame = tk.Frame(
                    scrollable_frame, bg="white", relief="groove", bd=1
                )
                row_frame.pack(fill="x", expand=True, pady=2)

                for idx in range(len(headers)):
                    row_frame.grid_columnconfigure(idx, weight=1)

                if image_data:
                    image_array = np.frombuffer(image_data, np.uint8)
                    region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                    if offset_x is not None and offset_y is not None:
                        cv2.circle(
                            region_image,
                            (offset_x, offset_y),
                            radius=5,
                            color=(0, 0, 255),
                            thickness=-1,
                        )

                    region_image_rgb = cv2.cvtColor(region_image, cv2.COLOR_BGR2RGB)
                    max_size = 100
                    target_size = 60
                    original_width, original_height = (
                        region_image_rgb.shape[1],
                        region_image_rgb.shape[0],
                    )
                    aspect_ratio = original_width / original_height

                    if original_width > original_height:
                        new_width = max_size
                        new_height = int(max_size / aspect_ratio)
                    else:
                        new_height = max_size
                        new_width = int(max_size * aspect_ratio)

                    pil_img = Image.fromarray(region_image_rgb).resize(
                        (new_width, new_height), Image.LANCZOS
                    )
                    img = ImageTk.PhotoImage(pil_img)

                    image_label = tk.Label(row_frame, image=img, bg="white")
                    image_label.grid(
                        row=row_index, column=0, padx=5, pady=5, sticky="nsew"
                    )
                    self.execution_image_references.append(img)

                filename_label = tk.Label(
                    row_frame,
                    text=str(region[1]),
                    bg="white",
                    anchor="w",
                    font=("Arial", 9),
                )
                filename_label.grid(
                    row=row_index, column=1, padx=5, pady=5, sticky="nsew"
                )

                threshold_label = tk.Label(
                    row_frame,
                    text=str(region[8]),
                    bg="white",
                    anchor="w",
                    font=("Arial", 9),
                )
                threshold_label.grid(
                    row=row_index, column=2, padx=5, pady=5, sticky="nsew"
                )

                offset_label = tk.Label(
                    row_frame,
                    text=f"({offset_x}, {offset_y})",
                    bg="white",
                    anchor="w",
                    font=("Arial", 9),
                )
                offset_label.grid(
                    row=row_index, column=3, padx=5, pady=5, sticky="nsew"
                )

                options_button = ttk.Button(row_frame, text="Opciones")
                options_button.grid(
                    row=row_index, column=4, padx=5, pady=5, sticky="nsew"
                )

                options_menu = Menu(self.root, tearoff=0)
                options_menu.add_command(
                    label="Modificar Offset",
                    command=lambda fn=region[1]: self.modify_offset(fn),
                )
                options_menu.add_command(
                    label="Detectar",
                    command=lambda fn=region[1]: self.detect_all_matches_with_threshold(
                        fn
                    ),
                )
                options_menu.add_command(
                    label="Click",
                    command=lambda fn=region[1]: self.add_action("Click", fn),
                )
                options_menu.add_command(
                    label="Click y Escribir",
                    command=lambda fn=region[1]: self.add_click_and_fill_action(fn),
                )
                options_menu.add_command(
                    label="Wait Image",
                    command=lambda fn=region[1]: self.add_action("Wait Image", fn),
                )
                options_menu.add_command(
                    label="Guardar Imagen",
                    command=lambda fn=region[1]: self.download_image(fn),
                )

                def show_options_menu(event, menu=options_menu):
                    if self.options_menu:
                        self.options_menu.unpost()

                    menu.post(event.x_root, event.y_root)
                    self.options_menu = menu

                    self.root.bind("<Button-1>", close_options_menu)

                def close_options_menu(event=None):
                    if self.options_menu:
                        self.options_menu.unpost()
                        self.options_menu = None
                    self.root.unbind("<Button-1>")

                options_button.bind("<Button-1>", show_options_menu)

                row_index += 1

    def detect_all_matches_with_threshold(self, filename):
        image_data, saved_threshold = self.db.get_image_data_and_threshold(filename)
        if image_data:
            image_array = np.frombuffer(image_data, np.uint8)
            region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if region_image is None:
            messagebox.showerror(
                "Error", f"No se pudo cargar la imagen de la región: {filename}"
            )
            return

        detect_window = tk.Toplevel(self.root)
        detect_window.title("Detectar Coincidencias")
        detect_window.geometry("800x600")

        monitor_label = tk.Label(detect_window, text="Seleccione Monitor:")
        monitor_label.pack(pady=10)

        monitors = self.screen_capture.get_monitors()
        monitor_options = [f"Monitor {i + 1}" for i in range(len(monitors))]
        selected_monitor = tk.StringVar(
            value=monitor_options[0] if monitor_options else "Monitor 1"
        )

        monitor_menu = ttk.OptionMenu(
            detect_window,
            selected_monitor,
            "1",
            *[str(i + 1) for i in range(len(monitor_options))],
        )
        monitor_menu.pack(pady=5)

        container = tk.Frame(detect_window)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, width=750, height=400)
        canvas.pack(side="left", fill="both", expand=True)

        scroll_x = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        scroll_x.pack(side="bottom", fill="x")
        scroll_y = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_y.pack(side="right", fill="y")
        canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        match_count_label = tk.Label(detect_window, text="Coincidencias encontradas: 0")
        match_count_label.pack(pady=10)

        def schedule_update_matches(threshold):
            if self.update_id is not None:
                detect_window.after_cancel(self.update_id)
            self.update_id = detect_window.after(200, lambda: update_matches(threshold))

        def update_matches(threshold):
            try:
                monitor_index = int(selected_monitor.get().split()[-1]) - 1
                screenshot, monitor_info = self.screen_capture.capture_monitor(
                    monitor_index
                )
            except Exception as e:
                messagebox.showerror(
                    "Error", f"No se pudo capturar el monitor seleccionado: {e}"
                )
                return

            match_image = screenshot.copy()
            matcher = ImageMatcher(monitor_index)
            all_matches = matcher.find_all_matches(
                region_image, match_image, float(threshold)
            )

            for top_left, bottom_right in all_matches:
                cv2.rectangle(match_image, top_left, bottom_right, (0, 255, 0), 3)

            match_image_rgb = cv2.cvtColor(match_image, cv2.COLOR_BGR2RGB)
            pil_match_image = Image.fromarray(match_image_rgb)
            tk_match_image = ImageTk.PhotoImage(pil_match_image)

            canvas.create_image(0, 0, anchor="nw", image=tk_match_image)
            canvas.image = tk_match_image
            canvas.config(scrollregion=canvas.bbox("all"))

            match_count_label.config(
                text=f"Coincidencias encontradas: {len(all_matches)}"
            )

        threshold_slider = tk.Scale(
            detect_window,
            from_=0.5,
            to=1.0,
            resolution=0.01,
            orient="horizontal",
            label="Threshold de Coincidencia",
            command=lambda value: schedule_update_matches(float(value)),
        )
        threshold_slider.set(saved_threshold if saved_threshold is not None else 0.9)
        threshold_slider.pack(side="bottom", fill="x")

        update_matches(threshold_slider.get())

    def add_action(self, action_type, filename):
        self.actions_queue.append((action_type, filename, ""))
        self.actions_listbox.insert(tk.END, f"{action_type} - {filename}")

    def add_click_and_fill_action(self, filename):
        text = simpledialog.askstring(
            "Texto a Escribir", f"Ingrese el texto para {filename}:"
        )
        if text:
            self.actions_queue.append(("Click y Escribir", filename, text))
            self.actions_listbox.insert(
                tk.END, f"Click y Escribir - {filename}: '{text}'"
            )

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
                    found = clicker.click_on_match(
                        region_image, offset_x=offset_x, offset_y=offset_y
                    )
                    if not found:
                        messagebox.showinfo(
                            "Resultado",
                            f"No se encontraron coincidencias para {filename}.",
                        )

                elif action_type == "Click y Escribir":
                    success = clicker.click_and_type(
                        region_image, text, offset_x=offset_x, offset_y=offset_y
                    )
                    if not success:
                        messagebox.showinfo(
                            "Resultado",
                            f"No se encontraron coincidencias para {filename}.",
                        )

                elif action_type == "Wait Image":
                    success = self.wait_for_image(filename)
                    if not success:
                        break

            else:
                messagebox.showerror(
                    "Error", f"No se pudo cargar la imagen de la región: {filename}"
                )

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

                canvas = tk.Canvas(
                    offset_window, width=pil_img.width, height=pil_img.height
                )
                canvas.create_image(0, 0, anchor="nw", image=tk_image)
                canvas.image = tk_image

                canvas.pack()

                new_offset = {"x": offset_x, "y": offset_y}

                def on_click(event):
                    new_offset["x"] = event.x
                    new_offset["y"] = event.y

                    canvas.delete("click_marker")
                    canvas.create_oval(
                        event.x - 3,
                        event.y - 3,
                        event.x + 3,
                        event.y + 3,
                        fill="red",
                        tags="click_marker",
                    )

                canvas.bind("<Button-1>", on_click)

                def save_offset():
                    self.db.update_offset(filename, new_offset["x"], new_offset["y"])
                    messagebox.showinfo("Resultado", "Offset actualizado exitosamente.")
                    offset_window.destroy()
                    self.update_execution_tab()

                save_button = tk.Button(
                    offset_window, text="Guardar Offset", command=save_offset
                )
                save_button.pack(pady=10)

    def wait_for_image(self, filename, timeout=30, interval=1.0):
        start_time = time.time()

        image_data = self.db.get_image_data(filename)
        if image_data:
            image_array = np.frombuffer(image_data, np.uint8)
            region_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        else:
            messagebox.showerror(
                "Error", f"No se pudo cargar la imagen de la región: {filename}"
            )
            return False

        if region_image is None:
            messagebox.showerror(
                "Error", f"No se pudo cargar la imagen de la región: {filename}"
            )
            return False

        matcher = ImageMatcher(int(self.selected_monitor.get()) - 1)

        while time.time() - start_time < timeout:
            matched_image, found, top_left = matcher.match_image(region_image)
            if found:
                return True

            time.sleep(interval)

        messagebox.showwarning(
            "Wait Image",
            f"No se detectó la imagen '{filename}' en el tiempo límite de {timeout} segundos.",
        )
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
                scroll_x = tk.Scrollbar(
                    match_window, orient="horizontal", command=canvas.xview
                )
                scroll_y = tk.Scrollbar(
                    match_window, orient="vertical", command=canvas.yview
                )

                canvas.configure(
                    xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set
                )

                canvas.pack(side="left", fill="both", expand=True)
                scroll_x.pack(side="bottom", fill="x")
                scroll_y.pack(side="right", fill="y")

                canvas.create_image(0, 0, anchor="nw", image=tk_image)
                canvas.image = tk_image
                canvas.config(scrollregion=canvas.bbox("all"))
            else:
                messagebox.showinfo("Resultado", "No se encontraron coincidencias.")
        else:
            messagebox.showerror(
                "Error", f"No se pudo cargar la imagen de la región: {filename}"
            )

    def download_image(self, filename):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
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
                        messagebox.showinfo(
                            "Guardado", f"Imagen guardada exitosamente en {save_path}"
                        )
                    else:
                        messagebox.showerror(
                            "Error",
                            "No se pudo decodificar la imagen desde los datos binarios.",
                        )
                else:
                    messagebox.showerror(
                        "Error",
                        f"No se encontró la imagen en la base de datos para el archivo: {filename}",
                    )
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen: {e}")

    def export_images(self):
        base_folder_path = filedialog.askdirectory(
            title="Selecciona la carpeta base para guardar las imágenes"
        )

        if base_folder_path:
            subfolder_name = simpledialog.askstring(
                "Nombre de Carpeta",
                "Ingrese el nombre de la subcarpeta para guardar las imágenes:",
            )

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

                messagebox.showinfo(
                    "Exportación Completa",
                    f"Todas las imágenes han sido exportadas a la carpeta '{target_folder}'.",
                )
            else:
                messagebox.showwarning(
                    "Exportación Cancelada",
                    "No se ingresó un nombre de subcarpeta. La exportación fue cancelada.",
                )
        else:
            messagebox.showwarning(
                "Exportación Cancelada",
                "No se seleccionó ningún directorio. La exportación fue cancelada.",
            )

    def delete_region(self, filename):
        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar la región {filename}?",
        )

        if confirm:
            try:
                if os.path.exists(filename):
                    os.remove(filename)

                self.db.delete_region(filename)

                self.update_execution_tab()
                messagebox.showinfo(
                    "Eliminado", f"La región {filename} se ha eliminado correctamente."
                )
            except Exception as e:
                messagebox.showerror(
                    "Error", f"No se pudo eliminar la región {filename}: {e}"
                )
