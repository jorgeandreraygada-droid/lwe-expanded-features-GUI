from tkinter import Frame, Entry, Button, Label


class DirectoryControls:
    """Gestiona los controles de selección de directorio"""
    
    def __init__(self, parent):
        self.frame = Frame(parent, bg="#0a0e27", bd=2, relief="solid", highlightthickness=2, highlightcolor="#004466", highlightbackground="#004466")
        
        # Label
        Label(self.frame, text="DIR ", bg="#0a0e27", fg="#ffffff", font=("Arial", 10, "bold")).grid(column=0, row=0, padx=5, pady=5)
        
        # Entry readonly
        self.entry = Entry(self.frame, state="readonly", bg="#1a2f4d", fg="#000000", insertbackground="#004466", font=("Courier", 9))
        self.entry.grid(column=1, row=0, padx=5, pady=5)
        
        # Botones
        self.pick_button = Button(self.frame, text="PICK DIR", bg="#004466", fg="#ffffff", font=("Arial", 9, "bold"), activebackground="#0066aa", activeforeground="#ff3333", bd=2, relief="raised", cursor="hand2")
        self.pick_button.grid(column=1, row=1, padx=5, pady=5)
        
        self.explore_button = Button(self.frame, text="EXPLORE", bg="#004466", fg="#ffffff", font=("Arial", 9, "bold"), activebackground="#0066aa", activeforeground="#ff3333", bd=2, relief="raised", cursor="hand2")
        self.explore_button.grid(column=0, row=1, padx=5, pady=5)
        
        self.execute_button = Button(self.frame, text="EXECUTE", bg="#004466", fg="#ffffff", font=("Arial", 9, "bold"), activebackground="#0066aa", activeforeground="#ff3333", bd=2, relief="raised", cursor="hand2")
        self.execute_button.grid(column=0, row=2, padx=5, pady=5)
        
        self.stop_button = Button(self.frame, text="STOP", bg="#661111", fg="#ffffff", font=("Arial", 9, "bold"), activebackground="#881111", activeforeground="#ff3333", bd=2, relief="raised", cursor="hand2")
        self.stop_button.grid(column=0, row=6, padx=5, pady=10)
    
    def set_directory(self, path):
        """Actualiza el directorio mostrado"""
        self.entry.config(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, path)
        self.entry.config(state="readonly")
    
    def grid(self, **kwargs):
        """Posiciona el frame en la ventana"""
        self.frame.grid(**kwargs)