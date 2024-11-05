from tkinter import Tk
from tkinter.filedialog import asksaveasfilename

class FileDialog:
    def save_file_dialog(self):
        Tk().withdraw()
        file_path = asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")],
                                      title="Guardar captura como", initialfile="captura.png")
        return file_path if file_path else None
