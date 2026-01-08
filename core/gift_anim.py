# core/gift_anim.py
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
    
# === SUPRIMIR MENSAJE DE PYGAME ===
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

def descubrir_efectos():
    """Descubre efectos en effect/ + canciones en song/."""
    efectos = {}
    
    # 1. Efectos desde effect/
    carpeta_effect = os.path.join(RAIZ, "effect")
    if os.path.exists(carpeta_effect):
        for archivo in os.listdir(carpeta_effect):
            if archivo.startswith("effect_") and archivo.endswith(".py"):
                nombre_modulo = archivo[:-3]
                try:
                    modulo = __import__(f"effect.{nombre_modulo}", fromlist=[''])
                    if hasattr(modulo, 'NOMBRE') and hasattr(modulo, 'ejecutar'):
                        efectos[modulo.NOMBRE] = modulo
                except Exception as e:
                    print(f"❌ Error al cargar '{archivo}': {e}", file=sys.stderr)
    
    # 2. Canciones desde song/ (efectos dinámicos)
    carpeta_song = os.path.join(RAIZ, "song")
    if os.path.exists(carpeta_song):
        for archivo in os.listdir(carpeta_song):
            if archivo.endswith('.mp3'):
                nombre = os.path.splitext(archivo)[0]  # sin extensión
                if nombre not in efectos:  # Evitar colisiones
                    efectos[nombre] = "SONIDO_ESPECIFICO"
    
        # 3. Videos específicos desde video/ 👈 NUEVO
    carpeta_video = os.path.join(RAIZ, "video")
    if os.path.exists(carpeta_video):
        for archivo in os.listdir(carpeta_video):
            if archivo.endswith('.mp4'):
                partes = archivo.split('_', 1)
                if partes and partes[0].isdigit():
                    nombre = os.path.splitext(archivo)[0]  # sin .mp4
                    efectos[nombre] = "VIDEO_ESPECIFICO"
    
    return efectos

# === MODO: listar efectos ===
if len(sys.argv) == 2 and sys.argv[1] == "--list-effects":
    efectos = descubrir_efectos()
    for nombre in sorted(efectos.keys()):
        print(nombre)
    sys.exit(0)

# === EJECUCIÓN ===
def main():
    if len(sys.argv) < 2:
        print("Uso: python gift_anim.py <efecto> [duracion_seg] [volumen%]", file=sys.stderr)
        sys.exit(1)

    tipo = sys.argv[1]
    duracion_seg = int(sys.argv[2]) if len(sys.argv) > 2 else 0  # 0 = completo
    volumen = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    duracion_ms = duracion_seg * 1000

    efectos = descubrir_efectos()
    if tipo not in efectos:
        print(f"⚠️ Efecto '{tipo}' no encontrado.", file=sys.stderr)
        sys.exit(1)

    try:
        if efectos[tipo] == "SONIDO_ESPECIFICO":
            # Reproducir sonido específico
            from effect import effect_sonidoR
            resultado = effect_sonidoR.ejecutar_especifico(tipo, duracion_ms, volumen)
        elif efectos[tipo] == "VIDEO_ESPECIFICO":  # 👈 NUEVO
            from effect import effect_videoR
            resultado = effect_videoR.ejecutar_especifico(tipo, duracion_ms, volumen)
        else:
            # Efecto normal
            resultado = efectos[tipo].ejecutar(duracion_ms, volumen)
        
        if resultado and "error" in resultado:
            print(f"❌ {resultado['error']}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado en '{tipo}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()