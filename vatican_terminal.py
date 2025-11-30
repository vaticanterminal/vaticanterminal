from scene import Scene
from pyglet.text import Label
from pyglet import shapes
import os
import random
from media_manager import MediaManager
import pyglet

# -----------------------
# CONFIGURACIÓN DE FUENTE
# -----------------------

FONT_FILE = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "fonts",
    "Glass_TTY_VT220.ttf",
)

FONT_NAME = "Glass TTY VT220"

COLOR_PRESETS = {
    "red": (255, 40, 40, 255),
    "green": (0, 255, 140, 255),
    "amber": (255, 170, 60, 255),
    "white": (230, 230, 230, 255),
    "purple": (200, 120, 255, 255),
}

SCREEN_MARGIN = 80  # margen interno del CRT


class VaticanTerminal(Scene):
    """
    Daemonum Index terminal:
    - phase 'splash'  : ASCII + *Index* + Press ENTER
    - phase 'menu'    : lista de casos + sinopsis
    - phase 'dossier' : dossier interactivo Lancaster Hill
    """

    def __init__(self, engine):
        super().__init__(engine)

        # Labels principales
        self.title_label = None
        self.index_label = None
        self.menu_labels = []
        self.synopsis_label = None
        self.dossier_console_label = None

        self.color_key = "red"
        self.font_name = "Courier New"

        self.media = MediaManager()

        # Boot CRT
        self.boot_sequence_played = False
        self.boot_active = False
        self.boot_timer = 0.0
        self.text_alpha = 0
        self.boot_noise_active = False

        # Overlay
        self.overlay_opacity = 0.0
        self.overlay_color = (0.0, 0.0, 0.0)

        # Glitch transición
        self.case_transition_active = False
        self.glitch_labels = []

        # Fases internas
        self.phase = "splash"
        self.selected_index = 0

        # Animación ASCII
        self.full_title = ""
        self.title_reveal_chars = 0
        self.title_reveal_speed = 120.0

        # Mascota de la terminal (diablito)
        self.pet_sprite = None
        try:
            img_path = r"C:\Users\Usuario\Desktop\IncorruptaModular\assets\images\Terminal pet.png"
            pet_img = pyglet.image.load(img_path)
            self.pet_sprite = pyglet.sprite.Sprite(pet_img)
        except Exception as e:
            print("[PET] No se pudo cargar Terminal pet:", e)
            self.pet_sprite = None

        # Casos
        self.cases = [
            {
                "title": "Lancaster Hill — Boarding School (Incorrupta)",
                "scene": "case_lancaster",
                "synopsis": (
                    "Catholic boarding school for girls. One minor confined "
                    "with prolonged fever, nocturnal agitation and conflicting "
                    "reports from staff about what happens in her room at night."
                ),
            },
            {
                "title": "[RESTRICTED FILE]",
                "scene": "case_locked",
                "synopsis": (
                    "Content sealed. Access denied in this build of the Archivum."
                ),
            },
        ]

        # ESTADO DEL DOSSIER
        self.dossier_lines = []          # buffer completo de texto
        self.dossier_pending_lines = []  # para animación
        self.dossier_animation_scheduled = False
        self.dossier_current_input = ""
        self.dossier_prompt = r"C:\✝\Daemonum Index\Cases\Lancaster Hill\Dossier>"
        self.dossier_max_lines = 14      # líneas visibles encima del prompt
        self.dossier_buffer_limit = 256  # máximo de líneas guardadas en buffer
        self.dossier_cursor_visible = True
        self.dossier_scroll_offset = 0   # 0 = al final; >0 = arriba

        # Reconstrucción
        self._labels_dirty = True
        self._crt_last_size = (0, 0)

    def _get_screen_bounds(self, w, h):
        """
        Devuelve un área visible central para contenido ASCII o texto,
        respetando los márgenes oscuros del estilo de monitor retro.
        """
        margin_w = int(w * 0.15)
        margin_h = int(h * 0.12)

        x = margin_w
        y = margin_h
        iw = w - margin_w * 2
        ih = h - margin_h * 2

        return x, y, iw, ih


    # ---------------- TEXTOS BASE ----------------

    def _title_text(self) -> str:
        return (
            "▓█████▄ ▄▄▄     ▓█████ ███▄ ▄███▓▒█████  ███▄    █ █    ██ ███▄ ▄███▓\n"
            "▒██▀ ██▒████▄   ▓█   ▀▓██▒▀█▀ ██▒██▒  ██▒██ ▀█   █ ██  ▓██▓██▒▀█▀ ██▒\n"
            "░██   █▒██  ▀█▄ ▒███  ▓██    ▓██▒██░  ██▓██  ▀█ ██▓██  ▒██▓██    ▓██░\n"
            "░▓█▄   ░██▄▄▄▄██▒▓█  ▄▒██    ▒██▒██   ██▓██▒  ▐▌██▓▓█  ░██▒██    ▒██ \n"
            "░▒████▓ ▓█   ▓██░▒████▒██▒   ░██░ ████▓▒▒██░   ▓██▒▒█████▓▒██▒   ░██▒\n"
            " ▒▒▓  ▒ ▒▒   ▓▒█░░ ▒░ ░ ▒░   ░  ░ ▒░▒░▒░░ ▒░   ▒ ▒░▒▓▒ ▒ ▒░ ▒░   ░  ░\n"
            " ░ ▒  ▒  ▒   ▒▒ ░░ ░  ░  ░      ░ ░ ▒ ▒░░ ░░   ░ ▒░░▒░ ░ ░░  ░      ░\n"
            " ░ ░  ░  ░   ▒     ░  ░      ░  ░ ░ ░ ▒    ░   ░ ░ ░░░ ░ ░░      ░   \n"
            "   ░         ░  ░  ░  ░      ░      ░ ░          ░   ░           ░   \n"
            " ░                                                                   \n"
        )

    def _splash_message(self) -> str:
        return "Press ENTER to access the Daemonum Index case files..."

    # ---------------- AUDIO ----------------

    def _play_sfx(self, key: str):
        try:
            if hasattr(self.media, "play_sfx"):
                self.media.play_sfx(key)
        except Exception as e:
            print(f"[AUDIO] Error playing sfx '{key}':", e)

    # ---------------- FUENTE ----------------

    def _load_custom_font(self):
        if os.path.exists(FONT_FILE):
            try:
                pyglet.font.add_file(FONT_FILE)
                self.font_name = FONT_NAME
                print("[FONT] VT220 cargada (Terminal).")
                self._labels_dirty = True
            except Exception as e:
                print("[FONT] Error VT220 (Terminal):", e)
        else:
            print("[FONT] No se encontró VT220 (Terminal):", FONT_FILE)

    # ---------------- CICLO DE VIDA ----------------

    def on_enter(self, **kwargs):
        self._load_custom_font()
        self.phase = "splash"
        self.selected_index = 0

        self.full_title = self._title_text()
        self.title_reveal_chars = 0

        self._reset_dossier_state()

        if not self.boot_sequence_played:
            self.boot_sequence_played = True
            self._start_boot()
        else:
            self.boot_active = False
            self.boot_timer = 0.0
            self.overlay_opacity = 0.0
            self.text_alpha = 255
            self.boot_noise_active = False
        
        self.color_key = "red"
        self._labels_dirty = True

    def on_exit(self):
        try:
            pyglet.clock.unschedule(self._dossier_toggle_cursor)
        except Exception:
            pass

    def _start_boot(self):
        self.boot_active = True
        self.boot_timer = 0.0
        self.overlay_color = (0.9, 1.0, 0.9)
        self.overlay_opacity = 1.0
        self.text_alpha = 0
        self.boot_noise_active = False
        self._play_sfx("boot")

    # ---------------- GEOMETRÍA CRT ----------------

    def _get_screen_bounds(self, w, h):
        w2 = w - SCREEN_MARGIN * 2
        h2 = h - SCREEN_MARGIN * 2
        if w2 / h2 > 4 / 3:
            ih = h2
            iw = int(ih * 4 / 3)
        else:
            iw = w2
            ih = int(w2 * 3 / 4)
        x = (w - iw) // 2
        y = (h - ih) // 2
        return x, y, iw, ih

        # ---------------- LABELS ----------------

    def _make_labels(self):
        if not self.engine or not self.engine.window:
            return

        w = self.engine.window.width
        h = self.engine.window.height
        size = (w, h)

        # Si nada cambió y ya tenemos labels, no recalcular
        if (
            not self._labels_dirty
            and self.title_label is not None
            and size == self._crt_last_size
        ):
            return

        self._crt_last_size = size
        self._labels_dirty = False

        x, y, iw, ih = self._get_screen_bounds(w, h)

        # Zonas verticales
        title_y = y + int(ih * 0.87)
        index_y = y + int(ih * 0.60)
        menu_base_y = y + int(ih * 0.50)
        dossier_console_y = y + int(ih * 0.47)

        # ---- Título ASCII (Daemonum Index) ----
        title_text = self._title_text()
        self.title_label = Label(
            title_text,
            x=x + 80,
            y=title_y,
            width=iw - 160,
            multiline=True,
            font_name="Courier New",
            font_size=10,
            color=COLOR_PRESETS[self.color_key],
        )

        # ---- *Index* centrado (rojo neón) ----
        self.index_label = Label(
            "⛧Index⛧",
            x=x + iw // 2,
            y=index_y,
            anchor_x="center",
            font_name=self.font_name,
            font_size=16,
            color=(255, 40, 40, 255),  # rojo neón intenso
        )

        # Reset de otros labels
        self.menu_labels = []
        self.synopsis_label = None
        self.dossier_console_label = None
        self.glitch_labels = []

        # ---- PANTALLA SPLASH ----
        if self.phase == "splash":
            # Texto de “Press ENTER…” alineado a la izquierda
            self.synopsis_label = Label(
                self._splash_message(),
                x=x + 40,
                y=y + 40,
                width=iw - 80,
                multiline=True,
                font_name=self.font_name,
                font_size=14,
                anchor_x="left",
                color=(255, 40, 40, 255),  # rojo neón
            )
            return

        # ---- MENÚ DE CASOS ----
        if self.phase == "menu":
            base_y = menu_base_y
            line_height = 24

            # Lista de casos (labels de menú)
            for idx, case in enumerate(self.cases):
                prefix = "> " if idx == self.selected_index else "  "
                text = f"{prefix}{case['title']}"
                lbl = Label(
                    text,
                    x=x + 40,
                    y=base_y - idx * line_height,
                    width=iw - 80,
                    multiline=False,
                    font_name=self.font_name,
                    font_size=14,
                    color=COLOR_PRESETS[self.color_key],
                )
                self.menu_labels.append((idx, lbl))

            # Sinopsis del caso seleccionado + ayuda
            selected_case = self.cases[self.selected_index]
            synopsis_text = (
                selected_case["synopsis"]
                + "\n\nUse UP/DOWN to select a case. Press ENTER to open."
            )

            self.synopsis_label = Label(
                synopsis_text,
                x=x + 40,
                y=y + 40,
                width=iw - 80,
                multiline=True,
                font_name=self.font_name,
                font_size=12,
                anchor_x="left",
                color=COLOR_PRESETS[self.color_key],
            )
            return

        # ---- DOSSIER (consola de comandos) ----
        if self.phase == "dossier":
            visible_lines = self._get_visible_dossier_lines()
            cursor_char = "|" if self.dossier_cursor_visible else " "
            all_lines = list(visible_lines)
            all_lines.append(
                f"{self.dossier_prompt}{self.dossier_current_input}{cursor_char}"
            )
            console_text = "\n".join(all_lines)

            self.dossier_console_label = Label(
                console_text,
                x=x + 40,
                y=dossier_console_y,
                width=iw - 80,
                multiline=True,
                font_name=self.font_name,
                font_size=13,
                color=COLOR_PRESETS[self.color_key], 
            )
            return



    def _get_visible_dossier_lines(self):
        total = len(self.dossier_lines)
        if total == 0:
            return []

        max_visible = self.dossier_max_lines
        if max_visible <= 0:
            return list(self.dossier_lines)

        max_offset = max(0, total - max_visible)
        offset = min(self.dossier_scroll_offset, max_offset)

        start = max(0, total - max_visible - offset)
        end = max(0, total - offset)
        return self.dossier_lines[start:end]

    # ---------------- DIBUJO ----------------

    def _draw_glow_label(self, label):
        if not label:
            return
        base_color = label.color
        r, g, b, _ = base_color
        a = int(self.text_alpha) if self.text_alpha is not None else base_color[3]
        base_color = (r, g, b, a)

        ox, oy = label.x, label.y
        glow_color = (r, g, b, int(a * 0.35))

        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            label.color = glow_color
            label.x, label.y = ox + dx, oy + dy
            label.draw()

        label.color = base_color
        label.x, label.y = ox, oy
        label.draw()

    def _draw_boot_noise(self, x, y, w, h):
        cell_w = 16
        cell_h = 10
        for yy in range(y, y + h, cell_h):
            for xx in range(x, x + w, cell_w):
                if random.random() < 0.45:
                    brightness = random.randint(40, 140)
                    rect = shapes.Rectangle(
                        xx,
                        yy,
                        cell_w - 1,
                        cell_h - 1,
                        color=(0, brightness, 0),
                    )
                    rect.opacity = random.randint(150, 240)
                    rect.draw()

    def _draw_scanlines(self, x, y, w, h):
        flick = random.uniform(-1, 1)

        base_alpha = 50
        if self.boot_active:
            base_alpha = 70
        if self.case_transition_active:
            base_alpha = max(base_alpha, 65)

        color = (0, 30, 0)
        for yy in range(y, y + h, 2):
            line = shapes.Rectangle(x, yy + flick, w, 1, color=color)
            line.opacity = base_alpha
            line.draw()

    def _draw_boot_noise(self, x, y, w, h):
        noise_lines = 24
        for i in range(noise_lines):
            yy = random.randint(y, y + h)
            flick = random.uniform(-2, 2)
            line = shapes.Rectangle(x, yy + flick, w, 1, color=(0, 255, 0))
            line.opacity = random.randint(80, 160)
            line.draw()


    # ---------------- ASCII TÍTULO: MORADO → ROJO + GOTEO ----------------

    def _draw_ascii_title(self, x, y, iw, ih):
        """
        Dibuja el ASCII del título con:
        - Degradado morado neón (arriba) → rojo neón (abajo).
        - Micro-glitch suave en bordes.
        - 'Goteo' sutil desde la base del ASCII.
        """
        # Si aún no hay título preparado, no dibujar
        if not getattr(self, "full_title", ""):
            return

        # Coordenadas base (mismas proporciones de _make_labels)
        top_y = y + int(ih * 0.87)
        left_x = x + 80
        max_width = iw - 160

        # Texto revelado hasta ahora (animación existente)
        if self.title_reveal_chars <= 0:
            return
        current_text = self.full_title[: self.title_reveal_chars]
        lines = current_text.splitlines()
        if not lines:
            return

        num_lines = len(lines)
        line_height = 14

        purple = (200, 120, 255)
        red = (255, 40, 40)

        line_labels = []

        # Dibujar cada línea con degradado vertical morado → rojo
        for i, line in enumerate(lines):
            t = 0.0 if num_lines == 1 else i / (num_lines - 1)
            r = int(purple[0] * (1 - t) + red[0] * t)
            g = int(purple[1] * (1 - t) + red[1] * t)
            b = int(purple[2] * (1 - t) + red[2] * t)

            line_y = top_y - i * line_height

            lbl = Label(
                line,
                x=left_x,
                y=line_y,
                width=max_width,
                multiline=False,
                font_name="Courier New",
                font_size=10,
                anchor_x="left",
                anchor_y="baseline",
                color=(r, g, b, 255),
            )
            self._draw_glow_label(lbl)
            line_labels.append((line_y, lbl))

        # Solo activamos glitch/goteo cuando el título ya está completo
        if self.title_reveal_chars < len(self.full_title):
            return

        if line_labels:
            # Glitch suave en la línea superior
            top_line_y, top_lbl = line_labels[0]
            if random.random() < 0.4:
                ghost_top = Label(
                    top_lbl.text,
                    x=top_lbl.x + random.choice([-1, 1]),
                    y=top_line_y + random.choice([-1, 1]),
                    width=max_width,
                    multiline=False,
                    font_name="Courier New",
                    font_size=10,
                    anchor_x="left",
                    anchor_y="baseline",
                    color=(200, 120, 255, 180),
                )
                self._draw_glow_label(ghost_top)

            # Glitch suave en la línea inferior
            bottom_line_y, bottom_lbl = line_labels[-1]
            if random.random() < 0.4:
                ghost_bottom = Label(
                    bottom_lbl.text,
                    x=bottom_lbl.x + random.choice([-1, 1]),
                    y=bottom_line_y + random.choice([-1, 1]),
                    width=max_width,
                    multiline=False,
                    font_name="Courier New",
                    font_size=10,
                    anchor_x="left",
                    anchor_y="baseline",
                    color=(255, 40, 40, 180),
                )
                self._draw_glow_label(ghost_bottom)

        # Goteo desde la base del ASCII (modo B – evidente pero elegante)
        bottom_y = top_y - (num_lines - 1) * line_height
        drip_count = 5
        for _ in range(drip_count):
            drip_x = random.randint(left_x, left_x + max_width)
            drip_height = random.randint(8, 22)
            drip_y = bottom_y - 4 - random.randint(0, 6)

            rect = shapes.Rectangle(
                drip_x,
                drip_y,
                2,  # ancho del goteo
                drip_height,
                color=(255, 40, 40),
            )
            rect.opacity = random.randint(120, 200)
            rect.draw()

    # ---------------- OVERLAYS LATINOS DEL AUDIT DAEMON ----------------

    def _draw_audit_daemon_overlays(self, x, y, iw, ih):
        """
        Mensajes latinos pequeños en márgenes izquierdo y derecho,
        simulando monitoreo del Audit Daemon.
        """
        latin_fragments = [
            "Libera nos a malo",
            "In Nomine Patris",
            "Deus in adiutorium",
            "Exsurge Domine",
            "Miserere nobis",
            "Noli timere",
            "Veritas vos liberabit",
            "In manus tuas Domine",
        ]

        min_y = y + 80
        max_y = y + ih - 100

        for i in range(4):
            frag = random.choice(latin_fragments)

            # Alternar entre margen izquierdo y derecho
            if i % 2 == 0:
                fx = x + 45
            else:
                fx = x + iw - 260

            fy = random.randint(min_y, max_y)

            r, g, b = (200, 120, 255)
            alpha = random.randint(80, 140)

            lbl = Label(
                frag,
                x=fx,
                y=fy,
                font_name=self.font_name,
                font_size=10,
                anchor_x="left",
                anchor_y="baseline",
                color=(r, g, b, alpha),
            )
            self._draw_glow_label(lbl)

    # ---------------- DIBUJO PRINCIPAL ----------------

    def on_draw(self):
        if not self.engine or not self.engine.window:
            return
        # Asegurarnos de que los labels están actualizados
        self._make_labels()

        w = self.engine.window.width
        h = self.engine.window.height
        x, y, iw, ih = self._get_screen_bounds(w, h)

        # Fondo de la “pantalla” de la terminal
        base = shapes.Rectangle(x, y, iw, ih, color=(5, 5, 5))
        base.draw()
        
        # Bordes oscuros estilo CRT
        opacity = 120
        band = 20
        for off_x, off_y, bw, bh in (
            (x, y + ih - band, iw, band),
            (x, y, iw, band),
            (x, y, band, ih),
            (x + iw - band, y, band, ih),
        ):
            v = shapes.Rectangle(off_x, off_y, bw, bh, color=(0, 0, 0))
            v.opacity = opacity
            v.draw()

        # Ruido de arranque si sigue activos
        if self.boot_active and self.boot_noise_active:
            self._draw_boot_noise(x, y, iw, ih)

        # ASCII: degradado morado → rojo + goteo + micro-glitch
        self._draw_ascii_title(x, y, iw, ih)

        # *Index* en el color actual de la terminal
        self._draw_glow_label(self.index_label)

        # ---------- FASES ----------
       
        # SPLASH: texto ENTER + diablito
        if self.phase == "splash":
            if self.synopsis_label:
                self._draw_glow_label(self.synopsis_label)

        # Diablito en el centro, debajo de *Index*
            if hasattr(self, "pet_sprite") and self.pet_sprite:
                pet = self.pet_sprite

                # Escalado más pequeño — ocupa un ~22% del ancho útil
                max_width = iw * 0.30
                scale = max_width / pet.image.width
                pet.scale = scale

            # Posición centrada horizontalmente
            pet.x = x + iw // 2 - pet.width // 2

            # Colocar un poco debajo del título *Index*
            if self.index_label:
                pet.y = self.index_label.y - pet.height - 25
            else:
                pet.y = y + ih // 2

            pet.opacity = 255
            pet.draw()


        # Scanlines al final
        self._draw_scanlines(x, y, iw, ih)


        if self.phase == "splash":
            self.synopsis_label = Label(
                self._splash_message(),
                x=x + 40,
                y=y + 40,
                width=iw - 80,
                multiline=True,
                font_name=self.font_name,
                font_size=16,
                color=COLOR_PRESETS[self.color_key],
            )
            return

        # MENÚ
        if self.phase == "menu":
            # Dibujar cada entrada del menú
            for idx_case, lbl in self.menu_labels:
                if idx_case == self.selected_index:
                    # Resalte para el caso seleccionado
                    r, g, b, _ = COLOR_PRESETS[self.color_key]
                    bar = shapes.Rectangle(
                        lbl.x - 10,
                        lbl.y - 4,
                        iw - 80,
                        lbl.font_size + 8,
                        color=(r, g, b),
                    )
                    bar.opacity = 220
                    bar.draw()
                    lbl.color = (0, 0, 0, 255)
                else:
                    lbl.color = COLOR_PRESETS[self.color_key]

                self._draw_glow_label(lbl)

            # Sinopsis del caso seleccionado
            if self.synopsis_label:
                self._draw_glow_label(self.synopsis_label)


        # DOSSIER
        if self.phase == "dossier":
            visible_lines = self._get_visible_dossier_lines()
            cursor_char = "|" if self.dossier_cursor_visible else " "

            all_lines = list(visible_lines)

            # 👉 Espacio visual entre el texto y el prompt
            all_lines.append("")  # si quieres más espacio, añade otro all_lines.append("")

            all_lines.append(
                f"{self.dossier_prompt}{self.dossier_current_input}{cursor_char}"
            )
            console_text = "\n".join(all_lines)

            # Dibujar la línea de consola del dossier si existe
            if self.dossier_console_label:
                self._draw_glow_label(self.dossier_console_label)


    def _get_visible_dossier_lines(self):
        total = len(self.dossier_lines)
        if total == 0:
            return []

        max_visible = self.dossier_max_lines
        if max_visible <= 0:
            return list(self.dossier_lines)

        max_offset = max(0, total - max_visible)
        offset = min(self.dossier_scroll_offset, max_offset)

        start = max(0, total - max_visible - offset)
        end = max(0, total - offset)
        return self.dossier_lines[start:end]
        # TRANSICIONES / GLITCH LABELS
        if self.case_transition_active:
            for lbl in self.glitch_labels:
                lbl.draw()

        # Overlays del Audit Daemon (frases latinas en los márgenes)
        self._draw_audit_daemon_overlays(x, y, iw, ih)

        # Scanlines CRT al final
        self._draw_scanlines(x, y, iw, ih)


        if self.overlay_opacity > 0:
            r, g, b = self.overlay_color
            if 0 <= r <= 1 and 0 <= g <= 1 and 0 <= b <= 1:
                rgb = (int(r * 255), int(g * 255), int(b * 255))
            else:
                rgb = (int(r), int(g), int(b))
            ov = shapes.Rectangle(x, y, iw, ih, color=rgb)
            ov.opacity = int(max(0.0, min(1.0, self.overlay_opacity)) * 255)
            ov.draw()

    # ---------------- UPDATE ----------------

    def on_update(self, dt):
        self._update_boot(dt)
        self._update_title_reveal(dt)
        self._make_labels()

    def _update_title_reveal(self, dt):
        total = len(self.full_title)
        if total <= 0:
            return
        if self.title_reveal_chars < total:
            before = self.title_reveal_chars
            self.title_reveal_chars += int(self.title_reveal_speed * dt)
            if self.title_reveal_chars > total:
                self.title_reveal_chars = total
            if self.title_reveal_chars != before:
                self._labels_dirty = True

    def _update_boot(self, dt):
        if not self.boot_active:
            return

        self.boot_timer += dt
        t = self.boot_timer

        FLASH_END = 0.18
        NOISE_END = 0.42
        FADE_START = 0.90
        FADE_END = 2.00
        FINISH = 2.30

        if t < FLASH_END:
            self.overlay_color = (0.9, 1.0, 0.9)
            self.overlay_opacity = 1.0 - (t / FLASH_END)
            self.text_alpha = 0
            self.boot_noise_active = False
        elif t < NOISE_END:
            self.overlay_opacity = 0.0
            self.boot_noise_active = True
            self.text_alpha = 0
        else:
            self.overlay_opacity = 0.0
            self.boot_noise_active = False

            if t < FADE_START:
                self.text_alpha = 0
            elif t < FADE_END:
                k = (t - FADE_START) / (FADE_END - FADE_START)
                k = max(0.0, min(1.0, k))
                self.text_alpha = int(255 * k)
            else:
                self.text_alpha = 255

        if t > FINISH:
            self.boot_active = False
            self.overlay_opacity = 0.0
            self.boot_noise_active = False
            self.text_alpha = 255

    # ---------------- ESTADO DEL DOSSIER ----------------

    def _reset_dossier_state(self):
        self.dossier_lines = []
        self.dossier_pending_lines = []
        self.dossier_animation_scheduled = False
        self.dossier_current_input = ""
        self.dossier_cursor_visible = True
        self.dossier_scroll_offset = 0
        self._labels_dirty = True

    def _init_dossier_header(self):
        header = [
            "INDEX // LANCASTER HILL CASE",
            
            "",
            "Enter HELP for case file query instructions.",
            "",
        ]
        self._dossier_enqueue_lines(header)

    def _dossier_trim_lines(self):
        if len(self.dossier_lines) > self.dossier_buffer_limit:
            self.dossier_lines = self.dossier_lines[-self.dossier_buffer_limit:]

    def _dossier_append_line_immediate(self, line: str):
        self.dossier_lines.append(line)
        self._dossier_trim_lines()
        self.dossier_scroll_offset = 0
        self._labels_dirty = True

    def _dossier_enqueue_lines(self, new_lines):
        if not new_lines:
            return
        self.dossier_pending_lines.extend(new_lines)
        if not self.dossier_animation_scheduled:
            self.dossier_animation_scheduled = True
            pyglet.clock.schedule_interval(self._dossier_drain_pending_lines, 0.05)
        self._labels_dirty = True

    def _dossier_drain_pending_lines(self, dt):
        if not self.dossier_pending_lines:
            self.dossier_animation_scheduled = False
            pyglet.clock.unschedule(self._dossier_drain_pending_lines)
            return
        line = self.dossier_pending_lines.pop(0)
        self.dossier_lines.append(line)
        self._dossier_trim_lines()
        self.dossier_scroll_offset = 0
        self._labels_dirty = True

    def _dossier_toggle_cursor(self, dt):
        self.dossier_cursor_visible = not self.dossier_cursor_visible
        self._labels_dirty = True

    # ---------------- INPUT ----------------

    def on_key(self, symbol, modifiers):
        from pyglet.window import key
        import pyglet.app

        # Cambios de color (no bloquean la escritura)
        if symbol == key.G:
            self.color_key = "green"
            self._labels_dirty = True
        elif symbol == key.A:
            self.color_key = "amber"
            self._labels_dirty = True
        elif symbol == key.W:
            self.color_key = "white"
            self._labels_dirty = True
        elif symbol == key.P:
            self.color_key = "purple"
            self._labels_dirty = True

        # SPLASH
        if self.phase == "splash":
            if symbol == key.ENTER:
                # Al salir del splash, el menú comienza en blanco
                self.phase = "menu"
                self.color_key = "white"
                self._labels_dirty = True
                self._play_sfx("enter")
            return


        # MENÚ
        if self.phase == "menu":
            if symbol == key.UP:
                self.selected_index = (self.selected_index - 1) % len(self.cases)
                self._labels_dirty = True
                self._play_sfx("move")
            elif symbol == key.DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.cases)
                self._labels_dirty = True
                self._play_sfx("move")
            elif symbol == key.ENTER:
                self._play_sfx("enter")
                if self.selected_index == 0:
                    self._enter_dossier()
                else:
                    self._go_case_external()
            elif symbol == key._2:
                pyglet.app.exit()
            return

        # DOSSIER
        if self.phase == "dossier":
            # --- Colores también activados en dossier ---
            if symbol == key.G:
                self.color_key = "green"
                self._labels_dirty = True
            elif symbol == key.A:
                 self.color_key = "amber"
                 self._labels_dirty = True
            elif symbol == key.W:
                 self.color_key = "white"
                 self._labels_dirty = True
            elif symbol == key.P:
                 self.color_key = "purple"
                 self._labels_dirty = True

            from pyglet.window import key as _key  # por si lo necesitas aquí

            # Scroll con ↑ / ↓
            if symbol == key.UP:
                total = len(self.dossier_lines)
                if total > self.dossier_max_lines:
                    max_offset = max(0, total - self.dossier_max_lines)
                    if self.dossier_scroll_offset < max_offset:
                        self.dossier_scroll_offset += 1
                        self._labels_dirty = True
                return

            if symbol == key.DOWN:
                if self.dossier_scroll_offset > 0:
                    self.dossier_scroll_offset -= 1
                    self._labels_dirty = True
                return

            # ENTER
            if symbol == key.ENTER:
               self._play_sfx("enter")
               self._execute_dossier_command()
               return

            # BACKSPACE
            if symbol == key.BACKSPACE:
                if self.dossier_current_input:
                    self.dossier_current_input = self.dossier_current_input[:-1]
                    self._labels_dirty = True
                return

            # Caracteres permitidos (escritura normal)
            ch = None

            if key.A <= symbol <= key.Z:
                offset = symbol - key.A
                ch = chr(ord("A") + offset)
                if not (modifiers & key.MOD_SHIFT):
                    ch = ch.lower()
            elif key._0 <= symbol <= key._9:
                offset = symbol - key._0
                ch = str(offset)
            elif symbol == key.SPACE:
                ch = " "
            elif symbol == key.BACKSLASH:
                ch = "\\"
            elif symbol == key.SLASH:
                ch = "/"
            elif symbol == key.COLON:
                ch = ":"
            elif symbol == key.MINUS:
                ch = "-"
            elif symbol == key.PERIOD:
                ch = "."
            elif symbol == key.APOSTROPHE or symbol == key.QUOTELEFT:
                ch = "'"

            if ch:
               self.dossier_current_input += ch
               self._labels_dirty = True
            return

    # ------------- TRANSICIÓN CASOS ---------------

    def _go_case_external(self):
        if self.case_transition_active:
            return
        self.case_transition_active = True
        self._play_sfx("locked")

        selected_case = self.cases[self.selected_index]
        target_scene = selected_case["scene"]

        def finish(_dt):
            self.case_transition_active = False
            self.engine.go_to(target_scene)

        pyglet.clock.schedule_once(finish, 0.4)

    # ------------- ENTRAR AL DOSSIER ---------------

    def _enter_dossier(self):
        self.phase = "dossier"
        self._reset_dossier_state()
        self._init_dossier_header()

        self.boot_active = False
        self.boot_noise_active = False
        self.overlay_opacity = 0.0
        self.text_alpha = 255

        pyglet.clock.schedule_interval(self._dossier_toggle_cursor, 0.5)
        # El dossier arranca en blanco por defecto
        self.color_key = "white"
        self._labels_dirty = True
        self._play_sfx("dossier_open")


    # ------------- COMANDOS DEL DOSSIER ------------

    def _execute_dossier_command(self):
        import pyglet.app

        raw_cmd = self.dossier_current_input.strip()
        if not raw_cmd:
            self._dossier_append_line_immediate(self.dossier_prompt)
            self.dossier_current_input = ""
            self._labels_dirty = True
            return

        # echo
        self._dossier_append_line_immediate(
            f"{self.dossier_prompt}{raw_cmd}"
        )

        cmd = raw_cmd.lower()

        # HELP
        if cmd == "help":
            block = [
                "",
                "DOSSIER COMMANDS:",
                "",
                "[Actors]      - Type 'ACTORS' to list the people involved.",
                "[Info]        - Type 'INFO' followed by the actor name",
                "                to get details (e.g. INFO M-12).",
                "[File Number] - Type 'FILE NUMBER' to see file ID and classification.",
                "[Location]    - Type 'LOCATION' to see where the case took place.",
                "[Status]      - Type 'STATUS' to see the current file status.",
                "[Show Image]  - Type 'SHOW IMAGE' to view the archive image description.",
                "[Case File]   - Type 'CASE FILE' to open the full case file.",
                "[Reset]       - Type 'RESET' to clear the dossier screen.",
                "[Back]        - Type 'BACK' to return to the case list.",
                "[Quit]        - Type 'QUIT' to exit Vatican Terminal.",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self._play_sfx("page")

        # ACTORS
        elif cmd == "actors":
            block = [
                "",
                "People involved in this case:",
                " - Minor M-12 — identity protected under child protection protocols",
                " - Legal guardian — identity protected under privacy regulations",
                " - Primary internal source — identity restricted by ecclesiastical authority",
                " - Fr. Aurelius Montfort — Apostolic Delegate for Preternatural Phenomena",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self._play_sfx("page")

        # INFO <actor>
        elif cmd.startswith("info"):
            arg = raw_cmd[4:].strip()
            norm = arg.lower().replace(".", "").replace("-", " ").strip()

            def match(variants):
                return any(v in norm for v in variants)

            if match(["minor m 12", "m 12", "minor", "child"]):
                block = [
                    "",
                    "INFO: Minor M-12",
                    " Internal boarding student with average academic performance.",
                    " No significant medical history recorded in the school's file.",
                    " Recent onset of prolonged fever, nocturnal agitation and",
                    " incidents reported as \"impossible\" by at least one staff member.",
                    "",
                ]
            elif match(["guardian", "legal guardian", "father", "parent"]):
                block = [
                    "",
                    "INFO: Legal guardian",
                    " Registered as the minor's legal tutor.",
                    " Multiple prior communications expressing concern about the",
                    " disciplinary methods used at Lancaster Hill.",
                    " Currently requesting more frequent reports on the minor's condition.",
                    "",
                ]
            elif match(["primary internal source", "primary", "source", "internal"]):
                block = [
                    "",
                    "INFO: Primary internal source",
                    " Identity restricted within the Archivum.",
                    " First to report preternatural phenomena occurring in M-12's room,",
                    " including nocturnal vocalizations in unknown languages and",
                    " objects found displaced without apparent cause.",
                    "",
                ]
            elif match(["aurelius montfort", "aurelius", "montfort", "priest", "father", "fr"]):
                block = [
                    "",
                    "INFO: Fr. Aurelius Montfort",
                    " Apostolic Delegate for Preternatural Phenomena.",
                    " Ordained 1968. Specialized in dogmatic theology and consultant",
                    " in cases of alleged demonic activity in educational contexts.",
                    "",
                    " Author of internal documents:",
                    "  - \"On Simulation and Deception in Minors\"",
                    "  - \"Preternatural Phenomena in Cloistered Environments\"",
                    "",
                ]
            else:
                block = [
                    "",
                    f"No dossier entry found for '{arg}'.",
                    "Type 'ACTORS' to see the list of available names.",
                    "",
                ]

            self._dossier_enqueue_lines(block)
            self._play_sfx("page")

        # FILE NUMBER
        elif cmd == "file number":
            block = [
                "",
                "FILE NUMBER:",
                "  ID: LHX-78/INC-Δ",
                "  Classification: Demonology / Level XII",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self._play_sfx("page")

        # LOCATION
        elif cmd == "location":
            block = [
                "",
                "LOCATION:",
                "  Oblate Boarding School of Lancaster Hill",
                "  Bedford County, Pennsylvania",
                "  Coordinates: 40.164° N, -78.684° W",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self._play_sfx("page")

        # STATUS
        elif cmd == "status":
            block = [
                "",
                "FILE STATUS:",
                "  Incomplete file. Most sections remain sealed.",
                "  Access restricted to personnel with Level XII clearance",
                "  or higher within the Archivum.",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self._play_sfx("page")

        # SHOW IMAGE
        elif cmd in ("show image", "image"):
            block = [
                "",
                "ARCHIVE IMAGE:",
                "  Grainy photograph of the north wing of the boarding school.",
                "  Windows on the third floor show an unidentified silhouette",
                "  in the dormitory assigned to M-12.",
                "  Embedded metadata contains inconsistent timestamps.",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self._play_sfx("page")

        # RESET
        elif cmd == "reset":
            self._reset_dossier_state()
            self._init_dossier_header()
            self._play_sfx("reset")

        # BACK
        elif cmd == "back":
            block = [
                "",
                "Closing Lancaster Hill dossier...",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self.dossier_current_input = ""
            try:
                pyglet.clock.unschedule(self._dossier_toggle_cursor)
            except Exception:
                pass
            self.phase = "menu"
            self._labels_dirty = True
            self._play_sfx("back")

        # CASE FILE
        elif cmd == "case file":
            block = [
                "",
                "Opening full case file for active investigation...",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self.dossier_current_input = ""
            self._play_sfx("case_open")

            def finish(_dt):
                self.engine.go_to("case_lancaster")

            pyglet.clock.schedule_once(finish, 0.4)

        # QUIT
        elif cmd == "quit":
            self._dossier_enqueue_lines(
                ["", "Exiting Vatican Terminal...", ""]
            )
            self._play_sfx("shutdown")
            pyglet.app.exit()

        # DESCONOCIDO
        else:
            block = [
                "",
                f"'{raw_cmd}' is not recognized as a valid dossier command.",
                "Type 'HELP' to see the list of available commands.",
                "",
            ]
            self._dossier_enqueue_lines(block)
            self._play_sfx("error")

        # Siempre limpiar input
        self.dossier_current_input = ""
        self._labels_dirty = True
