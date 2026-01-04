# effect/effect_boom.py
import os
import sys
import tkinter as tk
from PIL import Image, ImageTk
import random
import ctypes

# === METADATOS ===
NOMBRE = "boom"
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
        return {"error": "boom = \"value invalid, minim is =>1\""}
        
    ruta_iconos = "icon"
    if not os.path.exists(ruta_iconos):
        return {"error": "Carpeta 'icon/' no encontrada."}
        
    archivos = [f for f in os.listdir(ruta_iconos) 
                if f.endswith('.png') and f.split('.')[0].isdigit()]
    if not archivos:
        return {"error": "No hay íconos en 'icon/'."}

    root = crear_ventana_base()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{sw}x{sh}+0+0")

    canvas = tk.Canvas(root, width=sw, height=sh, bg=COLOR_FONDO, highlightthickness=0, bd=0)
    canvas.pack()

    imgs_tk = []
    for f in archivos:
        img = Image.open(os.path.join(ruta_iconos, f)).resize((32, 32), Image.LANCZOS)
        imgs_tk.append(ImageTk.PhotoImage(img))

    particulas = []
    def animar():
        if len(particulas) < 100:
            for _ in range(10):
                pdx, pdy = random.uniform(-15, 15), random.uniform(-15, 15)
                img_tk = random.choice(imgs_tk)
                obj = canvas.create_image(sw//2, sh//2, image=img_tk)
                particulas.append({'id': obj, 'x': sw//2, 'y': sh//2, 'dx': pdx, 'dy': pdy})
        for p in particulas[:]:
            p['x'] += p['dx']
            p['y'] += p['dy']
            canvas.coords(p['id'], p['x'], p['y'])
        root.after(20, animar)

    animar()
    root.after(duracion_ms, root.destroy)
    root.mainloop()
    return {"mensaje": f"Efecto '{NOMBRE}' v{VERSION} ejecutado."}