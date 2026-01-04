import tkinter as tk
from tkinter import ttk
import threading
import time
import os
import pygame
import json
from gtts import gTTS
from queue import Queue
from content_tiktok import TikTokScraper
import subprocess
import sys
import traceback  # 👈 IMPORTANTE: faltaba esta importación

# ===== MANEJADOR DE ERRORES GLOBAL =====
def manejar_error_global(exc_type, exc_value, exc_traceback):
    """Registra errores y muestra ventana de crash."""
    # Registrar en log.txt
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n{time.ctime()}\n{error_msg}\n{'='*50}\n")
    
    # Mostrar ventana de crash
    try:
        crash_win = tk.Tk()
        crash_win.title("💥 CRASH")
        crash_win.geometry("500x200")
        crash_win.resizable(False, False)
        crash_win.eval('tk::PlaceWindow . center')
        
        msg = f"Oops... el programa tuvo un error\n\n{str(exc_value)}\n\nError guardado en log.txt"
        ttk.Label(crash_win, text=msg, wraplength=480, justify="center").pack(pady=20)
        ttk.Button(crash_win, text="Aceptar y cerrar", command=lambda: os._exit(1)).pack(pady=10)
        crash_win.mainloop()
    except:
        print("CRASH FATAL:")
        print(error_msg)
        input("Presiona Enter para salir...")
        os._exit(1)

sys.excepthook = manejar_error_global

class MainPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Live Bot - Pro")
        self.root.geometry("600x530")

        self.queue = Queue()
        self.is_running = False
        self.config_file = "core/profile/config.json"

        # ---------------- CONFIG ----------------
        self.config_data = {
            "usuario_tiktok": "tu_usuario",
            "delay": 1.5,
            "skip_delay_priority": True,
            "msg_follow": "Gracias {user} por seguirme",
            "msg_gift": "{user} envió {cant} {gift}",
            "voice_chat": True,
            "voice_follow": True,
            "voice_gift": True,
            "filters_enabled": True,
            "filtros": [],
            "eventos": ["Doughnut"],
            "reconnect_interval": 5,
            "reconnect_attempts": 10,
            "volume_tts": 100,      # Volumen para TTS
            "volume_effects": 100   # Volumen para efectos
        }

        self.load_config()

        # ---------------- FLAGS ----------------
        self.voice_chat = tk.BooleanVar(value=self.config_data["voice_chat"])
        self.voice_follow = tk.BooleanVar(value=self.config_data["voice_follow"])
        self.voice_gift = tk.BooleanVar(value=self.config_data["voice_gift"])
        self.filters_enabled = tk.BooleanVar(value=self.config_data["filters_enabled"])

        # ---------------- FILTROS ----------------
        self.filtros_slots = []
        self.filtros_disponibles = self.detectar_filtros()

        pygame.mixer.init()
        self.setup_ui()
        self.cargar_filtros()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.voice_processor, daemon=True).start()

    # ======================================================
    # UI CON SCROLL DINÁMICO
    # ======================================================
    
    def setup_ui(self):
        # Frame contenedor principal
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # Notebook sin scroll global (cada pestaña se gestiona sola si es necesario)
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Crear pestañas
        self.create_tabs()

    def create_tabs(self):
        # Usar frames con scroll solo si el contenido es alto
        self.tab_control = self.create_scrollable_tab("Control")
        self.tab_config = self.create_scrollable_tab("Config")
        self.tab_filtros = self.create_scrollable_tab("Filtros")
        self.tab_info = self.create_scrollable_tab("Info")

        self.notebook.add(self.tab_control, text="Control")
        self.notebook.add(self.tab_config, text="Config")
        self.notebook.add(self.tab_filtros, text="Filtros")
        self.notebook.add(self.tab_info, text="Info")

        self.setup_control_tab()
        self.setup_config_tab()
        self.setup_filtros_tab()
        self.setup_info_tab()

    def create_scrollable_tab(self, name):
        """Crea un frame que añade scrollbar solo si es necesario."""
        frame = ttk.Frame(self.notebook)
        return frame

    def setup_control_tab(self):
        parent = self.tab_control
        parent.config(padding="20")

        ttk.Label(parent, text="Usuario de TikTok:").pack(anchor="w")
        self.ent_user = ttk.Entry(parent, width=50)
        self.ent_user.insert(0, self.config_data["usuario_tiktok"])
        self.ent_user.pack(pady=5)

        self.btn_toggle = ttk.Button(
            parent, text="Iniciar Live", command=self.toggle_bot
        )
        self.btn_toggle.pack(pady=10)

        self.log_txt = tk.Text(
            parent, height=10, width=60,
            state='disabled', font=("Segoe UI", 9)
        )
        self.log_txt.pack(pady=10, fill="x")

    def setup_config_tab(self):
        parent = self.tab_config
        parent.config(padding="20")

        # Delay
        ttk.Label(parent, text="Delay (seg):").grid(row=0, column=0, sticky="w", pady=2)
        self.delay_val = tk.DoubleVar(value=self.config_data["delay"])
        ttk.Spinbox(
            parent, from_=0, to=10, increment=0.5, width=8,
            textvariable=self.delay_val
        ).grid(row=0, column=1, pady=2)

        # Prioridad
        self.skip_delay = tk.BooleanVar(value=self.config_data["skip_delay_priority"])
        ttk.Checkbutton(
            parent, text="Prioridad Regalos / Follows", variable=self.skip_delay
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)

        # Mensajes
        ttk.Label(parent, text="Msg Follow:").grid(row=2, column=0, sticky="w", pady=2)
        self.ent_msg_follow = ttk.Entry(parent, width=40)
        self.ent_msg_follow.insert(0, self.config_data["msg_follow"])
        self.ent_msg_follow.grid(row=3, column=0, columnspan=2, pady=2)

        ttk.Label(parent, text="Msg Gift:").grid(row=4, column=0, sticky="w", pady=2)
        self.ent_msg_gift = ttk.Entry(parent, width=40)
        self.ent_msg_gift.insert(0, self.config_data["msg_gift"])
        self.ent_msg_gift.grid(row=5, column=0, columnspan=2, pady=2)

        ttk.Separator(parent, orient="horizontal").grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=10
        )

        # Opciones de voz
        ttk.Checkbutton(parent, text="🔊 Leer CHAT", variable=self.voice_chat).grid(row=7, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, text="🔊 Leer FOLLOW", variable=self.voice_follow).grid(row=8, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, text="🔊 Leer GIFT", variable=self.voice_gift).grid(row=9, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, text="🎬 Activar FILTROS", variable=self.filters_enabled).grid(row=10, column=0, sticky="w", pady=2)

        # Reconexión
        ttk.Separator(parent, orient="horizontal").grid(
            row=11, column=0, columnspan=2, sticky="ew", pady=10
        )
        ttk.Label(parent, text="Reconexión (seg):").grid(row=12, column=0, sticky="w", pady=2)
        self.reconnect_interval = tk.IntVar(value=self.config_data["reconnect_interval"])
        ttk.Spinbox(
            parent, from_=1, to=60, width=8,
            textvariable=self.reconnect_interval
        ).grid(row=12, column=1, pady=2)

        ttk.Label(parent, text="Intentos máximos:").grid(row=13, column=0, sticky="w", pady=2)
        self.reconnect_attempts = tk.IntVar(value=self.config_data["reconnect_attempts"])
        ttk.Spinbox(
            parent, from_=1, to=100, width=8,
            textvariable=self.reconnect_attempts
        ).grid(row=13, column=1, pady=2)

        # 👇 VOLUMENES SEPARADOS
        ttk.Separator(parent, orient="horizontal").grid(
            row=14, column=0, columnspan=2, sticky="ew", pady=10
        )
        ttk.Label(parent, text="Volumen TTS (%):").grid(row=15, column=0, sticky="w", pady=2)
        self.volume_tts_val = tk.IntVar(value=self.config_data["volume_tts"])
        ttk.Spinbox(
            parent, from_=0, to=100, width=6, textvariable=self.volume_tts_val
        ).grid(row=15, column=1, pady=2, sticky="w")
        self.volume_tts_slider = ttk.Scale(
            parent, from_=0, to=100, orient="horizontal",
            variable=self.volume_tts_val, length=150
        )
        self.volume_tts_slider.grid(row=16, column=1, pady=2, sticky="w")

        ttk.Label(parent, text="Volumen efectos (%):").grid(row=17, column=0, sticky="w", pady=2)
        self.volume_effects_val = tk.IntVar(value=self.config_data["volume_effects"])
        ttk.Spinbox(
            parent, from_=0, to=100, width=6, textvariable=self.volume_effects_val
        ).grid(row=17, column=1, pady=2, sticky="w")
        self.volume_effects_slider = ttk.Scale(
            parent, from_=0, to=100, orient="horizontal",
            variable=self.volume_effects_val, length=150
        )
        self.volume_effects_slider.grid(row=18, column=1, pady=2, sticky="w")

    def setup_filtros_tab(self):
        parent = self.tab_filtros
        parent.config(padding="10")

        self.btn_add_filtro = ttk.Button(
            parent, text="[ + ] Agregar Filtro",
            command=self.agregar_filtro_slot
        )
        self.btn_add_filtro.pack(anchor="w", pady=5)

        # Frame con scroll solo si es necesario
        self.canvas_filtros = tk.Canvas(parent, highlightthickness=0)
        self.scrollbar_filtros = ttk.Scrollbar(parent, orient="vertical", command=self.canvas_filtros.yview)
        self.frame_filtros = ttk.Frame(self.canvas_filtros)

        self.frame_filtros.bind(
            "<Configure>",
            lambda e: self.canvas_filtros.configure(scrollregion=self.canvas_filtros.bbox("all"))
        )

        self.canvas_filtros.create_window((0, 0), window=self.frame_filtros, anchor="nw")
        self.canvas_filtros.configure(yscrollcommand=self.scrollbar_filtros.set)

        # Empaquetar y gestionar visibilidad del scroll
        self.canvas_filtros.pack(side="left", fill="both", expand=True)
        self.scrollbar_filtros.pack(side="right", fill="y")

        # Evento para mostrar/ocultar scrollbar
        self.frame_filtros.bind("<Configure>", self.toggle_scroll_filtros)

        if not self.filtros_disponibles:
            ttk.Label(
                parent,
                text="⚠️ No se encontraron efectos en gift_anim.py",
                foreground="red"
            ).pack(pady=5)

    def toggle_scroll_filtros(self, event=None):
        """Muestra la scrollbar solo si el contenido se desborda."""
        canvas_height = self.canvas_filtros.winfo_height()
        frame_height = self.frame_filtros.winfo_reqheight()
        
        if frame_height > canvas_height:
            self.scrollbar_filtros.pack(side="right", fill="y")
        else:
            self.scrollbar_filtros.pack_forget()

    def setup_info_tab(self):
        parent = self.tab_info
        parent.config(padding="20")

        # Título principal
        title = ttk.Label(
            parent,
            text="ℹ️ TikTok Live Bot - Pro",
            font=("Segoe UI", 14, "bold"),
            foreground="#2c3e50"
        )
        title.pack(anchor="w", pady=(0, 15))

        # Crear un frame para el contenido con mejor espaciado
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill="x")

        # Estilo para secciones
        def add_section(title, body):
            section = ttk.Frame(content_frame)
            section.pack(fill="x", pady=(0, 12))
            
            ttk.Label(
                section, 
                text=title, 
                font=("Segoe UI", 11, "bold"),
                foreground="#3498db"
            ).pack(anchor="w")
            
            ttk.Label(
                section, 
                text=body, 
                font=("Segoe UI", 10),
                wraplength=500,
                justify="left"
            ).pack(anchor="w", pady=(5, 0))

        # Secciones mejoradas
        add_section(
            "• Control",
            "Inicia/detiene el bot y muestra logs en tiempo real. "
            "Si el bot se desconecta, intentará reconectar automáticamente."
        )
        
        add_section(
            "• Configuración",
            "Ajusta mensajes de bienvenida, volumen de efectos, y "
            "prioridad de eventos. Usa 'delay' para controlar la velocidad de lectura."
        )
        
        add_section(
            "• Filtros",
            "Asigna efectos a eventos específicos:\n"
            "  - 📏 Duración: DVD/Boom requieren ≥1s; SonidoR/VideoR usan 0 para reproducir completo.\n"
            "  - 🔊 Volumen: Controla el audio de efectos (0-100%).\n"
            "  - 🎁 Regalos: Los nuevos se registran automáticamente en 'Eventos'."
        )
        
        add_section(
            "• Eventos Dinámicos",
            "Cuando recibes un regalo nuevo (ej. 'Capybara'), se añade automáticamente "
            "a la lista de eventos. Así puedes asignarle un efecto sin reiniciar el bot."
        )
        
        # Consejo destacado
        tip_frame = ttk.Frame(content_frame)
        tip_frame.pack(fill="x", pady=(15, 0))
        
        ttk.Label(
            tip_frame,
            text="💡 Consejo Profesional",
            font=("Segoe UI", 11, "bold"),
            foreground="#e74c3c"
        ).pack(anchor="w")
        
        ttk.Label(
            tip_frame,
            text="Usa duración '0' solo para efectos que deben durar lo natural "
            "del contenido (sonidos o videos completos). Para regalos múltiples, "
            "el efecto se repetirá automáticamente según la cantidad enviada.",
            font=("Segoe UI", 10),
            wraplength=500,
            justify="left"
        ).pack(anchor="w", pady=(5, 0))

    # ======================================================
    # RESTO DEL CÓDIGO (IGUAL, PERO CON AJUSTES MENORES)
    # ======================================================

    def registrar_evento_gift(self, nombre_gift):
        if not nombre_gift or nombre_gift in ("follow", "all-gift"):
            return
        if nombre_gift not in self.config_data["eventos"]:
            self.config_data["eventos"].append(nombre_gift)
            self.config_data["eventos"].sort()
            self.guardar_configuracion_actual()
            print(f"🆕 Nuevo regalo registrado: {nombre_gift}")

    def deshabilitar_configuracion(self):
        self.ent_user.config(state="disabled")
        for child in self.tab_config.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Checkbutton, ttk.Scale)):
                try:
                    child.config(state="disabled")
                except tk.TclError:
                    pass
        self.btn_add_filtro.config(state="disabled")
        for frame in self.frame_filtros.winfo_children():
            if isinstance(frame, ttk.Frame):
                for widget in frame.winfo_children():
                    if isinstance(widget, (ttk.Combobox, ttk.Entry)):
                        widget.config(state="disabled")

    def habilitar_configuracion(self):
        self.ent_user.config(state="normal")
        for child in self.tab_config.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Checkbutton, ttk.Scale)):
                try:
                    child.config(state="normal")
                except tk.TclError:
                    pass
        self.btn_add_filtro.config(state="normal")
        for frame in self.frame_filtros.winfo_children():
            if isinstance(frame, ttk.Frame):
                for widget in frame.winfo_children():
                    if isinstance(widget, (ttk.Combobox, ttk.Entry)):
                        widget.config(state="normal")

    def detectar_filtros(self):
        if not os.path.exists("core/gift_anim.py"):
            return []
        try:
            result = subprocess.run(
                [sys.executable, "core/gift_anim.py", "--list-effects"],
                capture_output=True, text=True, timeout=10  # 10 segundos
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().splitlines() 
                       if line.strip() and not line.startswith("pygame")]
        except Exception as e:
            pass  # El error global lo capturará si es grave
        return []

    def agregar_filtro_slot(self, ev_val="follow", filtro_val=None, duracion_val="5"):
        if not self.filtros_disponibles:
            return

        fila = ttk.Frame(self.frame_filtros)
        fila.pack(fill="x", pady=2)

        evento = tk.StringVar(value=ev_val)
        filtro = tk.StringVar(value=filtro_val or self.filtros_disponibles[0])
        duracion = tk.StringVar(value=duracion_val)

        valores_eventos = ["follow", "all-gift"] + self.config_data["eventos"]

        ttk.Combobox(
            fila, values=valores_eventos,
            width=12, textvariable=evento, state="readonly"
        ).pack(side="left", padx=2)

        ttk.Label(fila, text="hacer").pack(side="left")

        ttk.Combobox(
            fila, values=self.filtros_disponibles,
            width=10, textvariable=filtro, state="readonly"
        ).pack(side="left", padx=2)

        ttk.Label(fila, text="durante").pack(side="left")

        dur_entry = ttk.Entry(fila, width=4, textvariable=duracion)
        dur_entry.pack(side="left")
        ttk.Label(fila, text="s").pack(side="left")

        slot_ref = {
            "evento": evento,
            "filtro": filtro,
            "duracion": duracion,
            "fila": fila,
            "dur_entry": dur_entry
        }
        self.filtros_slots.append(slot_ref)

        btn_eliminar = ttk.Button(
            fila, text="❌", width=3,
            command=lambda s=slot_ref: self.eliminar_filtro_slot(s)
        )
        btn_eliminar.pack(side="right", padx=(10, 0))

        # Forzar actualización del scroll
        self.root.after(10, self.toggle_scroll_filtros)

    def eliminar_filtro_slot(self, slot_a_eliminar):
        if slot_a_eliminar in self.filtros_slots:
            self.filtros_slots.remove(slot_a_eliminar)
            slot_a_eliminar["fila"].destroy()
            self.guardar_configuracion_actual()
            self.root.after(10, self.toggle_scroll_filtros)

    def validar_filtros(self):
        errores = []
        for slot in self.filtros_slots:
            filtro = slot["filtro"].get()
            duracion_str = slot["duracion"].get()
            if filtro not in self.filtros_disponibles:
                continue
            if not duracion_str.isdigit():
                errores.append(f"Duración inválida para '{filtro}': '{duracion_str}' (debe ser número)")
                continue
            duracion = int(duracion_str)
            if filtro in ("rebote", "boom") and duracion == 0:
                errores.append(f"{filtro} = \"value invalid, minim is =>1\"")
        return errores

    def mostrar_error_validacion(self, errores):
        error_win = tk.Toplevel(self.root)
        error_win.title("⚠️ Error de Validación")
        error_win.geometry("400x200")
        error_win.resizable(False, False)
        error_win.transient(self.root)
        error_win.grab_set()

        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        error_win.geometry(f"+{x}+{y}")

        mensaje = "Se declaró un conflicto:\n" + "\n".join(errores) + "\n\nPor favor consulte en 'Info'"
        ttk.Label(error_win, text=mensaje, wraplength=380, justify="center").pack(pady=20)
        ttk.Button(error_win, text="Aceptar", command=error_win.destroy).pack(pady=10)

    def mostrar_error_usuario(self, mensaje):
        error_win = tk.Toplevel(self.root)
        error_win.title("❌ Error de Usuario")
        error_win.geometry("400x150")
        error_win.resizable(False, False)
        error_win.transient(self.root)
        error_win.grab_set()

        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        error_win.geometry(f"+{x}+{y}")

        ttk.Label(
            error_win,
            text=f"🚨 {mensaje}\n\n• Verifica que el usuario exista\n• Asegúrate de que esté en vivo",
            justify="center",
            wraplength=380
        ).pack(pady=20)

        def aceptar():
            self.is_running = False
            self.btn_toggle.config(text="Iniciar Live")
            self.update_log(">>> BOT DETENIDO (usuario inválido)")
            self.habilitar_configuracion()
            error_win.destroy()

        ttk.Button(error_win, text="Aceptar", command=aceptar).pack(pady=10)

    def guardar_configuracion_actual(self):
        self.config_data.update({
            "usuario_tiktok": self.ent_user.get(),
            "delay": self.delay_val.get(),
            "skip_delay_priority": self.skip_delay.get(),
            "msg_follow": self.ent_msg_follow.get(),
            "msg_gift": self.ent_msg_gift.get(),
            "voice_chat": self.voice_chat.get(),
            "voice_follow": self.voice_follow.get(),
            "voice_gift": self.voice_gift.get(),
            "filters_enabled": self.filters_enabled.get(),
            "filtros": self.exportar_filtros(),
            "eventos": self.config_data["eventos"],
            "reconnect_interval": self.reconnect_interval.get(),
            "reconnect_attempts": self.reconnect_attempts.get(),
            "volume_tts": self.volume_tts_val.get(),
            "volume_effects": self.volume_effects_val.get()
        })
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Error al guardar configuración:", e)

    def ejecutar_filtro(self, filtro, duracion, repeticiones=1):
        if not os.path.exists("core/gift_anim.py"):
            return
        
        try:
            dur = int(duracion) if duracion.isdigit() else 15
            volumen = self.volume_effects_val.get()
            for _ in range(repeticiones):
                subprocess.Popen(
                    [sys.executable, "core/gift_anim.py", filtro, str(dur), str(volumen)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if repeticiones > 1:
                    time.sleep(0.1)
        except Exception as e:
            print("Error al ejecutar filtro:", e)
                                    
    def exportar_filtros(self):
        filtros_validos = []
        for s in self.filtros_slots:
            filtro_nombre = s["filtro"].get()
            if filtro_nombre and filtro_nombre in self.filtros_disponibles:
                filtros_validos.append({
                    "evento": s["evento"].get(),
                    "filtro": filtro_nombre,
                    "duracion": s["duracion"].get()
                })
        return filtros_validos

    def cargar_filtros(self):
        for f in self.config_data.get("filtros", []):
            filtro_val = f.get("filtro")
            if filtro_val and filtro_val in self.filtros_disponibles:
                self.agregar_filtro_slot(
                    ev_val=f.get("evento", "follow"),
                    filtro_val=filtro_val,
                    duracion_val=f.get("duracion", "5")
                )

    def voice_processor(self):
        while True:
            ev_type, user, content, vars_dict = self.queue.get()

            if not self.is_running:
                self.queue.task_done()
                continue

            try:
                texto = None
                is_priority = ev_type in ("follow", "gift")
                voice_allowed = False

                if ev_type == "comment":
                    if self.voice_chat.get():
                        texto = content.strip() if content else None
                        voice_allowed = True
                elif ev_type == "follow":
                    if self.voice_follow.get():
                        template = self.ent_msg_follow.get().strip()
                        if template:
                            texto = template.format(user=user)
                            voice_allowed = True
                elif ev_type == "gift":
                    nombre_gift = vars_dict.get("gift", "").strip()  # 👈 strip() aquí
                    cantidad = vars_dict.get("cant", 1)
                    self.registrar_evento_gift(nombre_gift)
                    if self.voice_gift.get():
                        template = self.ent_msg_gift.get().strip()
                        if template:
                            texto = template.format(
                                user=vars_dict.get("user", user),
                                gift=nombre_gift,
                                cant=cantidad
                            )
                            voice_allowed = True

                if texto or (ev_type in ("follow", "gift")):
                    log_text = f"[{ev_type.upper()}] {user}"
                    if texto:
                        log_text += f": {texto}"
                    self.root.after(0, self.update_log, log_text)

                # -------- FILTROS (siempre si están activos) --------
                if self.filters_enabled.get():
                    efectos_pendientes = []
                    for slot in self.filtros_slots:
                        ev = slot["evento"].get().strip()  # 👈 strip() aquí
                        if ev_type == "follow" and ev == "follow":
                            efectos_pendientes.append((slot["filtro"].get(), slot["duracion"].get(), 1))
                        elif ev_type == "gift":
                            nombre_regalo_evento = vars_dict.get("gift", "").strip()  # 👈 strip() aquí
                            if ev == "all-gift" or ev == nombre_regalo_evento:
                                cantidad = vars_dict.get("cant", 1)
                                efectos_pendientes.append((slot["filtro"].get(), slot["duracion"].get(), cantidad))
                    
                    if efectos_pendientes:
                        # Ejecutar efectos
                        for filtro, duracion, repeticiones in efectos_pendientes:
                            self.ejecutar_filtro(filtro, duracion, repeticiones)
                        
                        # Reproducir voz DESPUÉS de los efectos
                        if texto and voice_allowed:
                            # Esperar un tiempo razonable para que los efectos comiencen
                            time.sleep(1.0)
                            self.play_audio(texto)
                    else:
                        if texto and voice_allowed:
                            self.play_audio(texto)
                else:
                    if texto and voice_allowed:
                        self.play_audio(texto)

                debe_aplicar_delay = True
                if is_priority and self.skip_delay.get():
                    debe_aplicar_delay = False
                if debe_aplicar_delay:
                    time.sleep(self.delay_val.get())

                if self.queue.qsize() > 5:
                    priority = []
                    last_comment = None
                    while not self.queue.empty():
                        item = self.queue.get()
                        if item[0] in ("follow", "gift"):
                            priority.append(item)
                        else:
                            last_comment = item
                        self.queue.task_done()
                    for p in priority:
                        self.queue.put(p)
                    if last_comment:
                        self.queue.put(last_comment)
                        
            except Exception as e:
                print("Error en voice_processor:", e)

            self.queue.task_done()
            
    def play_audio(self, text):
        if not self.is_running:
            return
        try:
            filename = f"tts_{int(time.time() * 1000)}.mp3"
            gTTS(text=text, lang='es').save(filename)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.set_volume(self.volume_tts_val.get() / 100.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
            os.remove(filename)
        except Exception as e:
            print("Error en TTS:", e)

    def update_log(self, text):
        self.log_txt.config(state='normal')
        self.log_txt.insert(tk.END, text + "\n")
        self.log_txt.see(tk.END)
        self.log_txt.config(state='disabled')

    def toggle_bot(self):
        if not self.is_running:
            errores = self.validar_filtros()
            if errores:
                self.mostrar_error_validacion(errores)
                return

            self.is_running = True
            self.btn_toggle.config(text="Detener Live")
            self.update_log(">>> CONECTANDO AL LIVE...")
            self.deshabilitar_configuracion()

            self.scraper = TikTokScraper(
                self.ent_user.get(),
                self.add_to_queue,
                error_callback=self.mostrar_error_usuario
            )
            self.scraper.max_reintentos = self.reconnect_attempts.get()
            self.scraper.intervalo_reintento = self.reconnect_interval.get()

            self.scraper_thread = threading.Thread(target=self.scraper.run, daemon=True)
            self.scraper_thread.start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="Iniciar Live")
            self.update_log(">>> BOT DETENIDO")
            self.habilitar_configuracion()
            if hasattr(self, "scraper"):
                self.scraper.stop()
            self.clear_queue()

    def add_to_queue(self, ev_type, user, content, vars_dict=None):
        if self.is_running:
            self.queue.put((ev_type, user, content, vars_dict or {}))

    def clear_queue(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except:
                break

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Mantener compatibilidad
                self.config_data["volume_tts"] = loaded.get("volume_tts", 100)
                self.config_data["volume_effects"] = loaded.get("volume_effects", 100)
                # Actualizar el resto
                for key in loaded:
                    if key not in ["volume_tts", "volume_effects"]:
                        self.config_data[key] = loaded[key]

    def on_closing(self):
        self.config_data.update({
            "usuario_tiktok": self.ent_user.get(),
            "delay": self.delay_val.get(),
            "skip_delay_priority": self.skip_delay.get(),
            "msg_follow": self.ent_msg_follow.get(),
            "msg_gift": self.ent_msg_gift.get(),
            "voice_chat": self.voice_chat.get(),
            "voice_follow": self.voice_follow.get(),
            "voice_gift": self.voice_gift.get(),
            "filters_enabled": self.filters_enabled.get(),
            "filtros": self.exportar_filtros(),
            "eventos": self.config_data["eventos"],
            "reconnect_interval": self.reconnect_interval.get(),
            "reconnect_attempts": self.reconnect_attempts.get(),
            "volume_tts": self.volume_tts_val.get(),
            "volume_effects": self.volume_effects_val.get()
        })
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        self.root.destroy()
        
# ===== INICIALIZACIÓN SEGURA =====
CROMA = 'white'
if __name__ == "__main__":
    try:
        # Crear ventana principal (oculta)
        root = tk.Tk()
        root.withdraw()
        
        # Pantalla de carga
        loading = tk.Toplevel(root)
        loading.title("Cargando...")
        loading.overrideredirect(True)
        loading.config(bg=CROMA)  # Fondo temporal
        
        # Cargar imagen PNG con transparencia NATIVA
        from PIL import Image, ImageTk
        original_img = Image.open("loading.png")
        
        # Asegurar modo RGBA (con transparencia)
        if original_img.mode != 'RGBA':
            original_img = original_img.convert('RGBA')
        
        # Escalar a 1/3
        new_size = (original_img.width // 3, original_img.height // 3)
        scaled_img = original_img.resize(new_size, Image.LANCZOS)
        loading_img = ImageTk.PhotoImage(scaled_img)
        
        # Etiqueta con fondo transparente
        loading_label = tk.Label(
            loading, 
            image=loading_img, 
            borderwidth=0,
            highlightthickness=0,
            bg=CROMA  # Mismo que la ventana
        )
        loading_label.image = loading_img
        loading_label.pack()
        
        # Configurar ventana para transparencia REAL (Windows)
        loading.wm_attributes('-transparentcolor', CROMA)
        loading.config(bg=CROMA)
        
        # Centrar en pantalla
        screen_width = loading.winfo_screenwidth()
        screen_height = loading.winfo_screenheight()
        x = (screen_width // 2) - (scaled_img.width // 2)
        y = (screen_height // 2) - (scaled_img.height // 2)
        loading.geometry(f"{scaled_img.width}x{scaled_img.height}+{x}+{y}")
        loading.update()
        
        # Inicializar app
        app = MainPanel(root)
        loading.destroy()
        root.deiconify()
        root.mainloop()
        
    except Exception as e:
        manejar_error_global(type(e), e, e.__traceback__)
