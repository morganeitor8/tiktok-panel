# effect/effect_rebote.py
import os
import sys
import tkinter as tk
from PIL import Image, ImageTk
import random
import ctypes

# === METADATOS ===
NOMBRE = "rebote"
VERSION = "1.0"

# === FUNCIONES AUXILIARES ===
COLOR_FONDO = "#FF00FF"

def aplicar_estilo_fantasma(ventana):
    ventana.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(ventana.winfo_id())
    style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    style |= 0x00000020
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)

def crear_ventana_base():
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.config(bg=COLOR_FONDO)
    root.attributes("-transparentcolor", COLOR_FONDO)
    aplicar_estilo_fantasma(root)
    return root

# === FUNCIÓN PRINCIPAL ===
def ejecutar(duracion_ms=None, volumen=100):  # 👈 Añadir 'volumen' (aunque no se use)
    if duracion_ms == 0:
        return {"error": "DVD = \"value invalid, minim is =>1\""}
        
    ruta_iconos = "icon"
    if not os.path.exists(ruta_iconos):
        return {"error": "Carpeta 'icon/' no encontrada."}
        
    archivos = [f for f in os.listdir(ruta_iconos) 
                if f.endswith('.png') and f.split('.')[0].isdigit()]
    if not archivos:
        return {"error": "No hay íconos en 'icon/'."}

    root = crear_ventana_base()
    img_path = os.path.join(ruta_iconos, random.choice(archivos))
    img = Image.open(img_path).convert("RGBA").resize((256, 256), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=photo, bg=COLOR_FONDO, bd=0)
    label.image = photo
    label.pack()

    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x = random.randint(0, sw - 256)
    y = random.randint(0, sh - 256)
    dx, dy = random.choice([-7, 7]), random.choice([-7, 7])

    def mover():
        nonlocal x, y, dx, dy
        x += dx
        y += dy
        if x <= 0 or x >= sw - 256: dx *= -1
        if y <= 0 or y >= sh - 256: dy *= -1
        root.geometry(f"+{int(x)}+{int(y)}")
        root.after(16, mover)

    mover()
    root.after(duracion_ms, root.destroy)
    root.mainloop()
    return {"mensaje": f"Efecto '{NOMBRE}' v{VERSION} ejecutado."}