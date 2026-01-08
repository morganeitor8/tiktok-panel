# effect/effect_videoR.py
import os
import sys
import tkinter as tk
import random
import ctypes
import time

# === METADATOS ===
NOMBRE = "videoR"
VERSION = "1.4"

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

# === FUNCIÓN PARA REPRODUCIR VIDEO ESPECÍFICO ===
def ejecutar_especifico(nombre_archivo, duracion_ms=None, volumen=100):
    """
    Reproduce un archivo MP4 específico desde video/.
    
    Args:
        nombre_archivo (str): Nombre del archivo sin extensión (ej. 'intro')
        duracion_ms (int, opcional): Duración en milisegundos.
            - Si es None o <= 0: reproduce hasta el final.
            - Si es > 0: corta tras ese tiempo (solo si el video dura más).
        volumen (int, opcional): Volumen del audio (0-100). Por defecto: 100.
    """
    try:
        import vlc
    except ImportError:
        return {"error": "Efecto 'videoR' requiere 'python-vlc'. Ejecuta: pip install python-vlc"}

    # Validar volumen
    volumen = max(0, min(100, int(volumen) if volumen is not None else 100))

    ruta_videos = "video"
    ruta_completa = os.path.join(ruta_videos, f"{nombre_archivo}.mp4")
    
    if not os.path.exists(ruta_completa):
        return {"error": f"Archivo '{nombre_archivo}.mp4' no encontrado en 'video/'."}

    root = crear_ventana_base()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    ALTURA, ANCHO = 256, 341  # Relación 4:3
    x = random.randint(0, max(0, sw - ANCHO))
    y = random.randint(0, max(0, sh - ALTURA))
    root.geometry(f"{ANCHO}x{ALTURA}+{x}+{y}")

    # Inicializar VLC
    try:
        instance = vlc.Instance("--no-xlib", "--quiet")
        player = instance.media_player_new()
        player.set_hwnd(root.winfo_id())
        
        media = instance.media_new(os.path.abspath(ruta_completa))
        player.set_media(media)
        player.audio_set_volume(volumen)
    except Exception as e:
        return {"error": f"Error al inicializar VLC: {str(e)}"}

    duracion_usada = duracion_ms
    inicio_real = None
    timer_activo = True
    
    def cerrar_ventana():
        nonlocal timer_activo
        if timer_activo:
            timer_activo = False
            try:
                player.stop()
                player.release()
                instance.release()
            except:
                pass
            root.destroy()

    def gestionar_reproduccion():
        nonlocal inicio_real, duracion_usada, timer_activo
        
        if not timer_activo:
            return
            
        try:
            estado = player.get_state()
            tiempo_actual = player.get_time()
            
            if inicio_real is None and tiempo_actual > 0:
                inicio_real = time.time()
            
            if estado in (vlc.State.Ended, vlc.State.Error):
                cerrar_ventana()
                return
                
            if duracion_usada is not None and duracion_usada > 0:
                if inicio_real is not None:
                    tiempo_transcurrido = (time.time() - inicio_real) * 1000
                    if tiempo_transcurrido >= duracion_usada:
                        cerrar_ventana()
                        return
            
            root.after(50, gestionar_reproduccion)
            
        except Exception:
            cerrar_ventana()

    player.play()
    root.after(100, gestionar_reproduccion)
    root.protocol("WM_DELETE_WINDOW", cerrar_ventana)
    root.mainloop()
    
    return {"mensaje": f"Video '{nombre_archivo}' reproducido."}

# === FUNCIÓN PRINCIPAL (ALEATORIA) ===
def ejecutar(duracion_ms=None, volumen=100):
    """
    Ejecuta un video aleatorio con audio.
    
    Args:
        duracion_ms (int, opcional): Duración en milisegundos.
            - Si es None o <= 0: reproduce hasta el final.
            - Si es > 0: corta tras ese tiempo (solo si el video dura más).
        volumen (int, opcional): Volumen del audio (0-100). Por defecto: 100.
    """
    ruta_videos = "video"
    if not os.path.exists(ruta_videos):
        return {"error": "Carpeta 'video/' no encontrada."}

    archivos = []
    for f in os.listdir(ruta_videos):
        if f.endswith('.mp4'):
            partes = f.split('_', 1)
            if partes and partes[0].isdigit():
                archivos.append(f)

    if not archivos:
        return {"error": "No hay videos en formato '{n}_nombre.mp4' en 'video/'."}

    video = random.choice(archivos)
    nombre_sin_ext = os.path.splitext(video)[0]
    
    # Reutilizar la función específica
    return ejecutar_especifico(nombre_sin_ext, duracion_ms, volumen)