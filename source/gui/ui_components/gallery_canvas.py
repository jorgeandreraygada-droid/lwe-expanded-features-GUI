from tkinter import Frame, Canvas, ttk


class GalleryCanvas:
    """Gestiona el canvas de la galería con scrollbar"""
    
    def __init__(self, parent):
        self.container = Frame(parent, bg="#0a0e27", bd=3, relief="solid", highlightthickness=3, 
                               highlightcolor="#004466", highlightbackground="#004466")
        
        # Canvas (sin tamaño fijo para que se adapte al contenedor)
        self.canvas = Canvas(self.container, bg="#0f1729", bd=0, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Scrollbar (inicialmente oculto)
        self.scrollbar = ttk.Scrollbar(
            self.container,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")
        self.scrollbar.pack_forget()  # Ocultar inicialmente
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Frame interno donde se colocan los thumbnails
        self.inner_frame = Frame(self.canvas, bg="#0f1729")
        # Guardar el id de la ventana interna para poder ajustar su ancho
        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        # Ajustar el ancho del frame interno cuando el canvas cambie de tamaño
        def _on_canvas_config(event):
            try:
                self.canvas.itemconfig(self.inner_window, width=event.width)
            except Exception:
                pass
        self.canvas.bind("<Configure>", _on_canvas_config)
    
    def update_scroll_region(self, event=None):
        """Actualiza la región de scroll del canvas y muestra/oculta el scrollbar según sea necesario"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Verificar si es necesario mostrar el scrollbar
        # Si la altura del contenido es mayor que la altura del canvas, mostrar scrollbar
        try:
            canvas_height = self.canvas.winfo_height()
            content_bbox = self.canvas.bbox("all")
            if content_bbox:
                content_height = content_bbox[3] - content_bbox[1]
                if content_height > canvas_height:
                    self.scrollbar.pack(side="right", fill="y")
                else:
                    self.scrollbar.pack_forget()
        except Exception:
            pass
    
    def bind_scroll_events(self, on_mousewheel):
        """Configura los eventos de scroll (rueda del mouse)"""
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        self.canvas.bind_all("<Button-4>", on_mousewheel)  # Linux scroll up
        self.canvas.bind_all("<Button-5>", on_mousewheel)  # Linux scroll down
    
    def grid(self, **kwargs):
        """Posiciona el container en la ventana"""
        self.container.grid(**kwargs)