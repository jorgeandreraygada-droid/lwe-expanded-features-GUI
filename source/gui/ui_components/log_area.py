from tkinter import Frame, Entry, Button, Label, BooleanVar, Checkbutton, Text, Canvas, ttk


class LogArea:
    """Gestiona el área de logs de la aplicación"""
    
    def __init__(self, parent):
        self.frame = Frame(parent, bg="#0a0e27", bd=2, relief="solid", highlightthickness=2, highlightcolor="#004466", highlightbackground="#004466")
        
        self.text_widget = Text(
            self.frame,
            height=12,
            bg="#0f1729",
            fg="#00ff00",
            insertbackground="#00d4ff",
            wrap="word",
            bd=0,
            font=("Courier", 9)
        )
        self.text_widget.pack(fill="both", expand=True, padx=2, pady=2)
    
    def log(self, message):
        """Añade un mensaje al log"""
        self.text_widget.insert("end", message + "\n")
        self.text_widget.see("end")
    
    def clear(self):
        """Limpia el log"""
        self.text_widget.delete("1.0", "end")
    
    def grid(self, **kwargs):
        """Posiciona el frame en la ventana"""
        self.frame.grid(**kwargs)
    
    def grid_remove(self):
        """Oculta el frame sin quitarlo del layout"""
        self.frame.grid_remove()
    
    def grid_show(self):
        """Muestra el frame nuevamente"""
        self.frame.grid()


class DirectoryControls:
    """Gestiona los controles de selección de directorio"""
    
    def __init__(self, parent):
        self.frame = Frame(parent)
        
        # Label
        Label(self.frame, text="DIR ").grid(column=0, row=0)
        
        # Entry readonly
        self.entry = Entry(self.frame, state="readonly")
        self.entry.grid(column=1, row=0)
        
        # Botones
        self.pick_button = Button(self.frame, text="PICK DIR")
        self.pick_button.grid(column=1, row=1)
        
        self.explore_button = Button(self.frame, text="EXPLORE")
        self.explore_button.grid(column=0, row=1)
        
        self.execute_button = Button(self.frame, text="EXECUTE")
        self.execute_button.grid(column=0, row=2)
        
        self.stop_button = Button(self.frame, text="STOP")
        self.stop_button.grid(column=0, row=6, pady=5)
    
    def set_directory(self, path):
        """Actualiza el directorio mostrado"""
        self.entry.config(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, path)
        self.entry.config(state="readonly")
    
    def grid(self, **kwargs):
        """Posiciona el frame en la ventana"""
        self.frame.grid(**kwargs)


class FlagsPanel:
    """Gestiona el panel de flags y opciones"""
    
    def __init__(self, parent):
        self.frame = Frame(parent)
        
        # Variables booleanas
        self.window_mode = BooleanVar()
        self.above_flag = BooleanVar()
        self.random_mode = BooleanVar()
        
        # Checkboxes
        self.window_checkbox = Checkbutton(
            self.frame,
            text="window mode",
            variable=self.window_mode
        )
        self.window_checkbox.grid(column=0, row=0)
        
        self.above_checkbox = Checkbutton(
            self.frame,
            text="remove above prio",
            variable=self.above_flag
        )
        self.above_checkbox.grid(column=0, row=1)
        
        self.random_checkbox = Checkbutton(
            self.frame,
            text="random mode",
            variable=self.random_mode
        )
        self.random_checkbox.grid(column=0, row=2)
        
        # Botón back
        self.back_button = Button(self.frame, text="<= BACK")
        self.back_button.grid(column=0, row=3, pady=(10, 0))
        
        # Botón clear log
        self.clear_log_button = Button(self.frame, text="CLEAR LOG")
        self.clear_log_button.grid(column=0, row=4, pady=5)
        
        # Área para widgets dinámicos (timer)
        self.dynamic_widgets = []
    
    def add_timer_controls(self, on_submit):
        """Añade controles de timer para modo random"""
        self.clear_dynamic_widgets()
        
        label = Label(self.frame, text="TIMER (s)")
        entry = Entry(self.frame, width=5, justify="center")
        submit_button = Button(self.frame, text="SUBMIT")
        
        label.grid(column=1, row=0)
        entry.grid(column=1, row=1)
        submit_button.grid(column=1, row=2)
        
        self.dynamic_widgets.extend([label, entry, submit_button])
        
        # Configurar callback con acceso al entry
        submit_button.config(command=lambda: on_submit(entry.get()))
        
        return entry  # Para poder hacer focus si se desea
    
    def clear_dynamic_widgets(self):
        """Elimina los widgets dinámicos"""
        for widget in self.dynamic_widgets:
            widget.destroy()
        self.dynamic_widgets.clear()
    
    def grid(self, **kwargs):
        """Posiciona el frame en la ventana"""
        self.frame.grid(**kwargs)


class GalleryCanvas:
    """Gestiona el canvas de la galería con scrollbar"""
    
    def __init__(self, parent):
        self.container = Frame(parent)
        
        # Canvas
        self.canvas = Canvas(self.container, width=800, height=600, bg="#222")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.container,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Frame interno
        self.inner_frame = Frame(self.canvas, bg="#222")
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
    
    def update_scroll_region(self, event=None):
        """Actualiza la región de scroll"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def bind_scroll_events(self, on_mousewheel):
        """Configura los eventos de scroll"""
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        self.canvas.bind_all("<Button-4>", on_mousewheel)
        self.canvas.bind_all("<Button-5>", on_mousewheel)
    
    def grid(self, **kwargs):
        """Posiciona el container en la ventana"""
        self.container.grid(**kwargs)