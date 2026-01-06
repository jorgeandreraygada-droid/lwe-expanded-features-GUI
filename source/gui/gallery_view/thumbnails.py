from tkinter import Frame, Label
from gui.groups import is_favorite


class ThumbnailFactory:
    """Factory para crear diferentes tipos de thumbnails"""
    
    def __init__(self, inner_frame, config):
        self.inner_frame = inner_frame
        self.config = config
    
    def create_group_thumbnail(self, index, row, col, group_id, name, count, on_click, on_right_click=None):
        """Crea un thumbnail de grupo/carpeta"""
        frame = Frame(self.inner_frame, bg="#0f1729", bd=2, relief="solid", highlightthickness=2, highlightcolor="#004466", highlightbackground="#004466", padx=20, pady=20)
        frame.grid(row=row, column=col, padx=10, pady=10)
        
        icon = Label(frame, text="📁", font=("Arial", 36), bg="#0f1729", fg="#00ffff")
        icon.pack()
        
        Label(frame, text=f"{name}", fg="#FFFFFF", bg="#0f1729", font=("Arial", 12, "bold")).pack(pady=(5, 0))
        Label(frame, text=f"{count} items", fg="#FFFFFF", bg="#0f1729", font=("Arial", 9)).pack()
        
        # Eventos
        frame.bind("<Button-1>", lambda e: on_click(group_id))
        icon.bind("<Button-1>", lambda e: on_click(group_id))
        
        if on_right_click and group_id not in ("__ALL__", "__FAVORITES__"):
            frame.bind("<Button-3>", lambda e: on_right_click(e, group_id))
            icon.bind("<Button-3>", lambda e: on_right_click(e, group_id))
        
        return frame
    
    def create_new_group_thumbnail(self, index, row, col, on_click):
        """Crea el thumbnail '+' para crear nuevo grupo"""
        frame = Frame(self.inner_frame, bg="#0f1729", bd=2, relief="solid", highlightthickness=2, highlightcolor="#5F1166", highlightbackground="#5F1166", padx=20, pady=20)
        frame.grid(row=row, column=col, padx=10, pady=10)
        
        icon = Label(frame, text="+", font=("Arial", 40, "bold"), bg="#0f1729", fg="#5F1166")
        icon.pack()
        
        Label(frame, text="New group", fg="#FFFFFF", bg="#0f1729", font=("Arial", 12)).pack(pady=(5, 0))
        
        # Eventos
        frame.bind("<Button-1>", lambda e: on_click())
        icon.bind("<Button-1>", lambda e: on_click())
        
        return frame
    
    def create_wallpaper_thumbnail(self, index, row, col, wallpaper_id, img, 
                                   current_wallpaper, on_double_click, on_right_click, on_click=None):
        """Crea un thumbnail de wallpaper"""
        border_color = "#004466" if wallpaper_id == current_wallpaper else "#004466"
        
        thumb_frame = Frame(self.inner_frame, bg=border_color, bd=3, relief="solid", padx=5, pady=5)
        thumb_frame.grid(row=row, column=col)
        
        label_img = Label(thumb_frame, image=img, bg="#0f1729")
        label_img.pack()
        
        # Eventos
        if on_click:
            label_img.bind("<Button-1>", lambda e: on_click(wallpaper_id))
        label_img.bind("<Double-Button-1>", lambda e: on_double_click(wallpaper_id))
        label_img.bind("<Button-3>", lambda e: on_right_click(e, wallpaper_id))
        
        Label(thumb_frame, text=wallpaper_id, fg="#FFFFFF", bg="#004466", font=("Courier", 8)).pack()
        
        # Estrella de favorito (esquina superior izquierda)
        if is_favorite(self.config, wallpaper_id):
            star = Label(thumb_frame, text="★", fg="#ffff00", bg=border_color, font=("Arial", 16))
            star.place(x=2, y=2)
            star.lift()
        
        return thumb_frame