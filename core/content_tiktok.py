# content_tiktok.py
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, GiftEvent, FollowEvent
import threading
import time
import sys


class TikTokScraper:
    def __init__(self, username, queue_callback, error_callback=None):
        self.username = username.replace("@", "").strip()
        self.queue_callback = queue_callback
        self.error_callback = error_callback  # ← Nuevo: callback para errores críticos
        self.running = True
        self.max_reintentos = 10      # Valores por defecto (se sobrescriben desde MainPanel)
        self.intervalo_reintento = 5

        # ===== BUFFER DE REGALOS =====
        self.gift_buffer = {}
        self.gift_delay = 1.5

        # ===== INICIALIZAR CLIENTE =====
        self.client = TikTokLiveClient(unique_id=self.username)
        self.client.on(CommentEvent)(self.on_comment)
        self.client.on(GiftEvent)(self.on_gift)
        self.client.on(FollowEvent)(self.on_follow)

    # ================== EVENTOS ==================
    async def on_comment(self, event: CommentEvent):
        if not self.running:
            return
        try:
            usuario = event.user.unique_id
            mensaje = event.comment
            if mensaje:
                print(f"💬 {usuario}: {mensaje}")
                self.queue_callback("comment", usuario, mensaje, {})
        except Exception:
            pass

    async def on_gift(self, event: GiftEvent):
        if not self.running:
            return
        try:
            # 👇 Estrategia de fallback mejorada para obtener el nombre real
            usuario = "Usuario"
            if hasattr(event.user, 'nickname') and event.user.nickname:
                usuario = event.user.nickname
            elif hasattr(event.user, 'unique_id') and event.user.unique_id:
                usuario = event.user.unique_id
            elif hasattr(event.user, 'display_id') and event.user.display_id:
                usuario = event.user.display_id
            
            regalo = event.gift.info.name if hasattr(event.gift, "info") else getattr(event.gift, "name", "regalo")
            cantidad = getattr(event, "repeat_count", 1)

            key = (usuario, regalo)
            if key not in self.gift_buffer:
                self.gift_buffer[key] = {"count": 0, "timer": None}

            self.gift_buffer[key]["count"] += cantidad

            old_timer = self.gift_buffer[key].get("timer")
            if old_timer and old_timer.is_alive():
                old_timer.cancel()

            new_timer = threading.Timer(
                self.gift_delay,
                self._flush_gift,
                args=(key,)
            )
            self.gift_buffer[key]["timer"] = new_timer
            new_timer.start()
        except Exception as e:
            print(f"❌ Error en gift buffer: {e}")
        
    def _flush_gift(self, key):
        if not self.running:
            return
        try:
            usuario, regalo = key
            total = self.gift_buffer[key]["count"]
            # 👇 LOG DE DEPURACIÓN
            print(f"🎁 DEBUG - Usuario: '{usuario}', Regalo: '{regalo}', Cantidad: {total}")
            self.queue_callback("gift", usuario, "", {"user": usuario, "gift": regalo, "cant": total})
            del self.gift_buffer[key]
        except Exception as e:
            print(f"❌ Error al flush gift: {e}")

    async def on_follow(self, event: FollowEvent):
        if not self.running:
            return
        try:
            usuario = getattr(event.user, "unique_id", "Seguidor")
            print(f"➕ Nuevo seguidor: {usuario}")
            self.queue_callback("follow", usuario, "", {"user": usuario})
        except Exception:
            pass

    # ================== RUN CON RECONEXIÓN ==================
    def run(self):
        intentos = 0
        while self.running and intentos <= self.max_reintentos:
            if intentos > 0:
                print(f"🔄 Reintentando conexión ({intentos}/{self.max_reintentos})...")
                time.sleep(self.intervalo_reintento)
                
            try:
                self.client.run()
                break
            except Exception as e:
                error_msg = str(e).lower()
                # 👇 Detectar por palabras clave en el mensaje
                if any(keyword in error_msg for keyword in [
                    "user not found",
                    "useroffline",
                    "live not found",
                    "invalid user",
                    "not exist"
                ]):
                    mensaje_usuario = "El usuario no existe o no está en vivo."
                    print(f"❌ {mensaje_usuario}")
                    if self.error_callback:
                        self.error_callback(mensaje_usuario)
                    break
                else:
                    print(f"⚠️ Error de conexión: {e}. Reintentando en {self.intervalo_reintento}s...")
                    intentos += 1
                    
        if intentos > self.max_reintentos:
            print("💀 Máximos reintentos de conexión alcanzados.")

    # ================== STOP ==================
    def stop(self):
        self.running = False
        # Cancelar timers
        for data in self.gift_buffer.values():
            timer = data.get("timer")
            if timer and timer.is_alive():
                timer.cancel()
        self.gift_buffer.clear()
        print("🔌 Conexión con TikTokLive detenida.")