from gui.main_menu import MainMenu
import os
import pytesseract
import tkinter as tk
from tkinter import messagebox
import sys


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

tesseract_path = resource_path("tesseract/tesseract.exe")
tessdata_path = resource_path("tesseract/tessdata")

if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    os.environ["TESSDATA_PREFIX"] = tessdata_path
    print("Tesseract configurado correctamente.")
else:
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning(
        "Tesseract no encontrado",
        f"No se encontró Tesseract en la ruta esperada:\n{tesseract_path}\n\n"
        "Por favor, asegúrate de que está instalado."
    )
    exit()


if __name__ == "__main__":
    app = MainMenu()
    app.run()