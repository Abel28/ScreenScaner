from tkinter import ttk

class Styles:
    def __init__(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.set_button_style()
        self.set_label_style()
        self.set_entry_style()
        self.set_optionmenu_style()
        self.set_frame_style()
    
    def set_button_style(self, bg="#34495E", fg="white", font=("Helvetica", 12)):
        """Estilo para botones."""
        self.style.configure(
            "Custom.TButton",
            background=bg,
            foreground=fg,
            font=font,
            padding=5,
            relief="flat"
        )
        self.style.map(
            "Custom.TButton",
            background=[("active", "#5D6D7E")],
            relief=[("pressed", "sunken")]
        )

    def set_label_style(self, fg="white", font=("Helvetica", 10)):
        """Estilo para etiquetas (Label)."""
        self.style.configure(
            "Custom.TLabel",
            foreground=fg,
            font=font
        )

    def set_entry_style(self, bg="#2C3E50", fg="white", font=("Helvetica", 12)):
        """Estilo para campos de entrada (Entry)."""
        self.style.configure(
            "Custom.TEntry",
            fieldbackground=bg,
            foreground=fg,
            font=font,
            padding=5
        )

    def set_optionmenu_style(self, bg="#34495E", fg="white", active_bg="#5D6D7E", font=("Helvetica", 12)):
        """Estilo para OptionMenu."""
        self.style.configure(
            "Custom.TMenubutton",
            background=bg,
            foreground=fg,
            font=font,
            padding=5,
            relief="flat"
        )
        self.style.map(
            "Custom.TMenubutton",
            background=[("active", active_bg)],
            relief=[("pressed", "sunken")]
        )

    def set_frame_style(self, bg="#2C3E50"):
        """Estilo para Frame."""
        self.style.configure(
            "Custom.TFrame",
            background=bg
        )

    def set_canvas_style(self, canvas, bg="#2C3E50", borderwidth=2, relief="flat"):
        """Método para aplicar estilo a Canvas."""
        canvas.configure(
            bg=bg,
            borderwidth=borderwidth,
            relief=relief
        )

    def apply_style(self, widget, style_name):
        """Método para aplicar un estilo a un widget dado."""
        if isinstance(widget, (ttk.Button, ttk.Label, ttk.Entry, ttk.Frame, ttk.OptionMenu)):
            widget.configure(style=style_name)