from tkinter import Frame, Label, BooleanVar, Checkbutton, Scale, HORIZONTAL


class SoundPanel:
    """Gestiona el panel de configuración de sonido"""
    
    def __init__(self, parent):
        self.frame = Frame(
            parent, 
            bg="#0a0e27", 
            bd=2, 
            relief="solid",
            highlightthickness=2, 
            highlightcolor="#440044", 
            highlightbackground="#440044"
        )
        
        # Título del panel
        title_label = Label(
            self.frame,
            text="🔊 SOUND",
            bg="#0a0e27",
            fg="#FFFFFF",
            font=("Arial", 10, "bold")
        )
        title_label.grid(column=0, row=0, columnspan=2, pady=(5, 10), sticky="w", padx=5)
        
        # Variables booleanas
        self.silent = BooleanVar()
        self.noautomute = BooleanVar()
        self.no_audio_processing = BooleanVar()
        
        # Variable de volumen (0-100)
        self.volume_value = 50  # Valor por defecto
        
        # Checkbox: Silent
        self.silent_checkbox = Checkbutton(
            self.frame,
            text="Silent (mute all)",
            variable=self.silent,
            bg="#0a0e27",
            fg="#FFFFFF",
            font=("Arial", 9),
            activebackground="#0a0e27",
            activeforeground="#ff3333",
            selectcolor="#0a0e27"
        )
        self.silent_checkbox.grid(column=0, row=1, columnspan=2, padx=5, pady=3, sticky="w")
        
        
        """VOLUME PANEL
        VOLUME PANEL NOT WORKING. REFER TO CLOSED ISSUE ON THE TOPIC"""
        # Label de volumen
        """volume_label = Label(
            self.frame,
            text="Volume:",
            bg="#0a0e27",
            fg="#FFFFFF",
            font=("Arial", 9)
        )
        volume_label.grid(column=0, row=2, padx=5, pady=(5, 0), sticky="w")
        
        # Label que muestra el valor del volumen
        self.volume_display = Label(
            self.frame,
            text="50",
            bg="#0a0e27",
            fg="#00ff00",
            font=("Courier", 9, "bold"),
            width=3
        )
        self.volume_display.grid(column=1, row=2, padx=5, pady=(5, 0), sticky="e")
        
        # Slider de volumen
        self.volume_slider = Scale(
            self.frame,
            from_=0,
            to=100,
            orient=HORIZONTAL,
            bg="#0a0e27",
            fg="#FFFFFF",
            troughcolor="#1a2f4d",
            activebackground="#0066aa",
            highlightthickness=0,
            showvalue=0,  # No mostrar valor en el slider (usamos label separado)
            length=150,
            width=15,
            command=self._on_volume_change
        )
        self.volume_slider.set(50)  # Valor inicial
        self.volume_slider.grid(column=0, row=3, columnspan=2, padx=5, pady=(0, 5), sticky="ew")"""
        
        # Checkbox: No Auto Mute
        self.noautomute_checkbox = Checkbutton(
            self.frame,
            text="No auto mute",
            variable=self.noautomute,
            bg="#0a0e27",
            fg="#FFFFFF",
            font=("Arial", 9),
            activebackground="#0a0e27",
            activeforeground="#ff3333",
            selectcolor="#0a0e27"
        )
        self.noautomute_checkbox.grid(column=0, row=4, columnspan=2, padx=5, pady=3, sticky="w")
        
        # Checkbox: No Audio Processing
        self.no_audio_processing_checkbox = Checkbutton(
            self.frame,
            text="No audio processing",
            variable=self.no_audio_processing,
            bg="#0a0e27",
            fg="#FFFFFF",
            font=("Arial", 9),
            activebackground="#0a0e27",
            activeforeground="#ff3333",
            selectcolor="#0a0e27"
        )
        self.no_audio_processing_checkbox.grid(column=0, row=5, columnspan=2, padx=5, pady=(3, 10), sticky="w")
    
    
    #VOLUME PANEL NOT WORKING. REFER TO CLOSED ISSUE
    # def _on_volume_change(self, value):
        """Actualiza el display cuando cambia el slider"""
    #    self.volume_value = int(float(value))
    #    self.volume_display.config(text=str(self.volume_value))
    
    # def get_volume(self):
        """Obtiene el valor actual del volumen"""
    #    return self.volume_value
    
    # def set_volume(self, value):
        """Establece el valor del volumen"""
    #    try:
    #        vol = int(value)
    #        if 0 <= vol <= 100:
    #            self.volume_slider.set(vol)
    #            self.volume_value = vol
    #            self.volume_display.config(text=str(vol))
    #    except (ValueError, TypeError):
    #        pass
    
    def grid(self, **kwargs):
        """Posiciona el frame en la ventana"""
        self.frame.grid(**kwargs)