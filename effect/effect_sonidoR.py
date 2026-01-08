# effect/effect_sonidoR.py
import os
import sys
import pygame
import random
import time

# === METADATOS ===
NOMBRE = "sonidoR"
VERSION = "1.0"

# Inicializar pygame una vez
pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.mixer.init()

# === FUNCIÓN PRINCIPAL ===
def ejecutar(duracion_ms=None, volumen=100):
    ruta_sonidos = "song"
    if not os.path.exists(ruta_sonidos):
        return {"error": "Carpeta 'song/' no encontrada."}

    archivos = []
    for f in os.listdir(ruta_sonidos):
        if f.endswith('.mp3'):
            partes = f.split('_', 1)
            if partes and partes[0].isdigit():
                archivos.append(f)

    if not archivos:
        return {"error": "No hay sonidos en formato '{n}_nombre.mp3' en 'song/'."}

    sonido = random.choice(archivos)
    ruta_completa = os.path.join(ruta_sonidos, sonido)

    try:
        pygame.mixer.music.load(ruta_completa)
        # 👇 APLICAR VOLUMEN (0-100 → 0.0-1.0)
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volumen / 100.0)))
        pygame.mixer.music.play()
        
        if duracion_ms is not None and duracion_ms > 0:
            time.sleep(duracion_ms / 1000.0)
            pygame.mixer.music.stop()
        else:
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        return {"mensaje": f"Efecto '{NOMBRE}' v{VERSION} ejecutado."}
    except Exception as e:
        return {"error": f"Error al reproducir '{sonido}': {str(e)}"}
    
# === FUNCIÓN PARA REPRODUCIR SONIDO ESPECÍFICO ===
def ejecutar_especifico(nombre_archivo, duracion_ms=None, volumen=100):
    """Reproduce un archivo MP3 específico desde song/."""
    ruta_sonidos = "song"
    ruta_completa = os.path.join(ruta_sonidos, f"{nombre_archivo}.mp3")
    
    if not os.path.exists(ruta_completa):
        return {"error": f"Archivo '{nombre_archivo}.mp3' no encontrado en 'song/'."}

    try:
        pygame.mixer.music.load(ruta_completa)
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volumen / 100.0)))
        pygame.mixer.music.play()
        
        if duracion_ms is not None and duracion_ms > 0:
            time.sleep(duracion_ms / 1000.0)
            pygame.mixer.music.stop()
        else:
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        return {"mensaje": f"Sonido '{nombre_archivo}' reproducido."}
    except Exception as e:
        return {"error": f"Error al reproducir '{nombre_archivo}.mp3': {str(e)}"}