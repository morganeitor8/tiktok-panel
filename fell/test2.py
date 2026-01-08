# prueba_chat.py
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

client = TikTokLiveClient("@name")  # ← Cambia por un live activo y grande

@client.on(CommentEvent)
async def on_comment(event):
    print(f"💬 [PRUEBA] {event.user.unique_id}: {event.comment}")

print("Iniciando prueba de chat...")
client.run()