# inspect_tiktoklive.py
try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive import events
    import inspect
    import sys

    print("✅ TikTokLive instalado correctamente.")
    print(f"📌 Versión del SDK: {getattr(TikTokLiveClient, '__version__', 'Desconocida')}")
    print("\n🔍 Eventos disponibles en `TikTokLive.events`:\n")

    # Listar todos los eventos (clases que terminan en 'Event')
    eventos = [
        name for name, obj in inspect.getmembers(events)
        if inspect.isclass(obj) and name.endswith('Event')
    ]

    if eventos:
        for evento in sorted(eventos):
            print(f"  - {evento}")
    else:
        print("  ❌ No se encontraron eventos.")

    print("\n🛠️ Métodos principales de TikTokLiveClient:\n")
    metodos = [
        name for name in dir(TikTokLiveClient)
        if not name.startswith('_') and callable(getattr(TikTokLiveClient, name))
    ]
    for metodo in sorted(metodos):
        print(f"  - {metodo}")

except ImportError:
    print("❌ La librería 'TikTokLive' no está instalada.")
    print("👉 Ejecuta: pip install TikTokLive")
except Exception as e:
    print(f"⚠️ Error al inspeccionar TikTokLive: {e}")