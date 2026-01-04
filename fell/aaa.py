from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent

# --- CONFIGURACIÓN ---
# Reemplaza con el nombre del usuario que está en LIVE
USUARIO_TIKTOK = "name" 

client = TikTokLiveClient(unique_id=USUARIO_TIKTOK)

@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"✅ ¡Éxito! Conectado al chat de: {event.unique_id}")
    print("-" * 30)

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    try:
        # Intentamos obtener el nombre de usuario de la forma estándar
        # Si falla por el error de 'nickName', saltará al bloque 'except'
        usuario = event.user.nickname
        mensaje = event.comment
        print(f"💬 {usuario}: {mensaje}")
        
    except Exception:
        # Si la librería falla al procesar el objeto 'user',
        # extraemos el mensaje directamente para que no se cierre el programa
        print(f"💬 [Usuario Desconocido]: {event.comment}")

@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent):
    print("-" * 30)
    print("❌ Se ha perdido la conexión con el LIVE.")

if __name__ == "__main__":
    try:
        print(f"Intentando conectar a {USUARIO_TIKTOK}...")
        client.run()
    except Exception as e:
        print(f"Hubo un error al iniciar el script: {e}")