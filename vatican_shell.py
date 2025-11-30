from scene import Scene
from pyglet.text import Label
from pyglet import shapes
import pyglet
import os
import random

# -----------------------
# CONFIGURACIÓN DE FUENTE
# -----------------------

FONT_FILE = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "fonts",
    "Glass_TTY_VT220.ttf"
)

FONT_NAME = "Glass TTY VT220"

COLOR_PRESETS = {
    "green": (0, 255, 140, 255),
    "amber": (255, 170, 60, 255),
    "white": (230, 230, 230, 255),
    "purple": (200, 120, 255, 255),
}

SCREEN_MARGIN = 80  # margen del monitor dentro de la ventana


class VaticanShell(Scene):
    """
    Consola de Vatican Terminal:

    Vatican Terminal [Version 3.1.8]
    (c) 1982 ExLibris TechnoSacrum Inc. All rights reserved.

    Enter HELP for more assistance.

    C:\\✝\\VaticanTerminal 1982\\>
    """

    def __init__(self, engine):
        super().__init__(engine)

        self.font_name = "Courier New"
        self.color_key = "green"

        self.console_label = None

        # Historial de la consola
        self.lines = []            # líneas ya impresas
        self.current_input = ""    # lo que el jugador escribe

        # Prompts
        self.shell_prompt = r"C:\✝\VaticanTerminal 1982\>"
        self.auth_prompt = r"C:\✝\VaticanTerminal 1982\AuthKey\>"
        self.prompt = self.shell_prompt

        # Efecto visual simple
        self.text_alpha = 255

        # Scroll: máximo de líneas visibles (historial recortado).
        self.max_lines = 18

        # Cola de líneas pendientes para "animar" salida
        self.pending_lines = []
        self.animation_scheduled = False

        # Cursor parpadeante
        self.cursor_visible = True

        # Reconstrucción condicionada
        self._text_dirty = True
        self._last_size = (0, 0)

        # ---------- LOGIN CANÓNICO ----------
        self.login_mode = False
        self.login_attempts = 0
        self.login_correct_key = "1614"

        # Bloqueo tras 3 fallos
        self.locked = False
        self._lock_reset_scheduled = False

        # ---------- GLITCH ----------
        self.glitch_mode = False
        self.glitch_timer = 0.0
        self.glitch_duration = 3.0
        self.glitch_color_phase = 0.0
    # ---------------- FUENTE ----------------

    def _load_custom_font(self):
        if os.path.exists(FONT_FILE):
            try:
                pyglet.font.add_file(FONT_FILE)
                self.font_name = FONT_NAME
                print("[FONT] VT220 cargada (Shell).")
                self._text_dirty = True
            except Exception as e:
                print("[FONT] Error cargando VT220 (Shell):", e)
        else:
            print("[FONT] No se encontró VT220 (Shell):", FONT_FILE)

    # ---------------- CICLO DE VIDA ----------------

    def on_enter(self, **kwargs):
        self._load_custom_font()

        self.lines = []
        self.current_input = ""
        self.pending_lines = []
        self.animation_scheduled = False
        self.cursor_visible = True

        # Reset de estados especiales
        self.login_mode = False
        self.login_attempts = 0
        self.locked = False
        self._lock_reset_scheduled = False
        self.glitch_mode = False
        self.glitch_timer = 0.0
        self.glitch_color_phase = 0.0
        self.prompt = self.shell_prompt

        header = [
            "Vatican Terminal [Version 3.1.8]",
            "(c) 1982 ExLibris TechnoSacrum Inc. All rights reserved.",
            "",
            "Enter HELP for more assistance.",
            ""
        ]
        self._enqueue_lines(header)

        pyglet.clock.schedule_interval(self._toggle_cursor, 0.5)
        self._text_dirty = True

    def on_exit(self):
        try:
            pyglet.clock.unschedule(self._toggle_cursor)
        except Exception:
            pass

        try:
            pyglet.clock.unschedule(self._drain_pending_lines)
        except Exception:
            pass

        try:
            pyglet.clock.unschedule(self._reset_after_lock)
        except Exception:
            pass

    # ---------------- HISTORIAL / ANIMACIÓN ----------------

    def _trim_lines(self):
        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines:]

    def _append_line_immediate(self, line: str):
        self.lines.append(line)
        self._trim_lines()
        self._text_dirty = True

    def _enqueue_lines(self, new_lines):
        """Añade un bloque de líneas a la cola para animarlas."""
        if not new_lines:
            return
        self.pending_lines.extend(new_lines)
        if not self.animation_scheduled:
            self.animation_scheduled = True
            pyglet.clock.schedule_interval(self._drain_pending_lines, 0.05)
        self._text_dirty = True

    def _drain_pending_lines(self, dt):
        if not self.pending_lines:
            self.animation_scheduled = False
            try:
                pyglet.clock.unschedule(self._drain_pending_lines)
            except Exception:
                pass
            return
        line = self.pending_lines.pop(0)
        self.lines.append(line)
        self._trim_lines()
        self._text_dirty = True

    def _toggle_cursor(self, dt):
        self.cursor_visible = not self.cursor_visible
        self._text_dirty = True
    # ---------------- TEXTO BASE / LABEL ----------------

    def _get_base_text(self) -> str:
        """Construye el texto limpio de la consola (sin glitch)."""
        all_lines = list(self.lines)
        cursor_active = self.cursor_visible and not self.locked and not self.glitch_mode
        cursor_char = "|" if cursor_active else " "
        all_lines.append(f"{self.prompt}{self.current_input}{cursor_char}")
        return "\n".join(all_lines)

    def _make_labels(self):
        if not self.engine or not self.engine.window:
            return

        w = self.engine.window.width
        h = self.engine.window.height
        size = (w, h)

        if (
            not self._text_dirty
            and self.console_label is not None
            and size == self._last_size
        ):
            return

        self._last_size = size
        self._text_dirty = False

        x, y, iw, ih = self._get_screen_bounds(w, h)

        base_text = self._get_base_text()

        self.console_label = Label(
            base_text,
            x=x + 40,
            y=y + ih - 60,
            width=iw - 80,
            multiline=True,
            font_name=self.font_name,
            font_size=14,
            color=COLOR_PRESETS[self.color_key],
        )

    def on_update(self, dt):
        # Si está en glitch, solo actualizamos el temporizador de glitch
        if self.glitch_mode:
            self._update_glitch(dt)
            return

        self._make_labels()

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

    # ---------------- DIBUJO BASE ----------------

    def _draw_glow_label(self, label):
        if not label:
            return
        base_color = label.color
        r, g, b, _ = base_color
        a = int(self.text_alpha)
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

    def _draw_scanlines(self, x, y, w, h):
        flick = random.uniform(-1, 1)
        base_alpha = 55
        color = (0, 30, 0)
        for yy in range(y, y + h, 2):
            line = shapes.Rectangle(x, yy + flick, w, 1, color=color)
            line.opacity = base_alpha
            line.draw()

    # ---------------- COLOR GLITCH PÚRPURA/ROJO NEÓN ----------------

    def _glitch_color(self):
        """
        Devuelve un color dinámico que oscila entre púrpura demoníaco y rojo neón.
        Cambia cada frame para dar sensación de latigazo visual.
        """
        if random.random() < 0.5:
            # Púrpura demoníaco
            r = random.randint(200, 255)
            g = random.randint(0, 80)
            b = random.randint(200, 255)
        else:
            # Rojo neón fosforescente
            r = 255
            g = random.randint(0, 40)
            b = random.randint(60, 120)
        return r, g, b

    # ---------------- GLITCH VISUAL ----------------

    def _draw_glitch(self, x, y, w, h):
        """
        Glitch de acceso:
        - Tres símbolos ⛧ enormes en posiciones desalineadas.
        - Estrellas con capas ghost deformadas usando ⛧ + ▒█▓░.
        - Palabras/frases en latín regadas sobre el área de texto.
        - Símbolos ▒█▓░⛧✟✞ dispersos por toda la pantalla.
        - Todo tintado con púrpura infernal / rojo neón dinámico.
        """

        # Color base dinámico (púrpura / rojo neón)
        r, g, b = self._glitch_color()

        # ---------------- ESTRELLAS GRANDES ----------------
        # Posiciones: superior derecha, centro izquierda, inferior derecha
        positions = [
            (x + int(w * 0.78), y + int(h * 0.80)),  # arriba derecha
            (x + int(w * 0.30), y + int(h * 0.50)),  # centro izquierda
            (x + int(w * 0.75), y + int(h * 0.20)),  # abajo derecha
        ]

        star_symbols = ["⛧", "▒", "█", "▓", "░"]

        for cx, cy in positions:
            base_size = random.randint(120, 170)

            # Capa base sólida ⛧
            base_label = Label(
                "⛧",
                font_name="Courier New",
                font_size=base_size,
                x=cx,
                y=cy,
                anchor_x="center",
                anchor_y="center",
                color=(r, g, b, 235),
            )
            base_label.draw()

            # Capas ghost deformadas
            ghost_count = 8
            for _ in range(ghost_count):
                jitter_x = random.randint(-28, 28)
                jitter_y = random.randint(-20, 20)
                ghost_size = int(base_size * random.uniform(0.88, 1.10))

                glyph = random.choice(star_symbols)

                gr, gg, gb = self._glitch_color()
                alpha = random.randint(70, 220)

                ghost = Label(
                    glyph,
                    font_name="Courier New",
                    font_size=ghost_size,
                    x=cx + jitter_x,
                    y=cy + jitter_y,
                    anchor_x="center",
                    anchor_y="center",
                    color=(gr, gg, gb, alpha),
                )
                ghost.draw()

        # ---------------- LATÍN REGADO POR LA PANTALLA ----------------
        latin_fragments = [
            "In Nomine Patris",
            "et Filii et Spiritus Sancti",
            "Libera nos a malo",
            "Vade retro Satana",
            "Ecce Crucem Domini",
            "Fugite partes adversae",
            "Deus in adiutorium",
            "Salus in periculis",
            "Protege nos Domine",
            "Exsurge Domine",
            "Benedictus in nomine Domini",
            "In manus tuas Domine",
            "Averte faciem tuam",
            "Sub tuum praesidium",
        ]

        latin_count = 30  # saturación demoníaca
        for _ in range(latin_count):
            frag = random.choice(latin_fragments)
            font_size = random.randint(10, 18)
            px = random.randint(x + 40, x + w - 40)
            py = random.randint(y + 40, y + h - 40)
            lr, lg, lb = self._glitch_color()
            alpha = random.randint(90, 210)

            label = Label(
                frag,
                font_name=self.font_name,
                font_size=font_size,
                x=px,
                y=py,
                anchor_x="center",
                anchor_y="center",
                color=(lr, lg, lb, alpha),
            )
            label.draw()

        # ---------------- SÍMBOLOS SUELTOS POR TODA LA PANTALLA ----------------
        loose_symbols = ["▒", "█", "▓", "░", "⛧", "✟", "✞"]
        symbol_count = 80
        for _ in range(symbol_count):
            sym = random.choice(loose_symbols)
            font_size = random.randint(12, 28)
            px = random.randint(x + 20, x + w - 20)
            py = random.randint(y + 20, y + h - 20)
            sr, sg, sb = self._glitch_color()
            alpha = random.randint(110, 240)

            s_label = Label(
                sym,
                font_name="Courier New",
                font_size=font_size,
                x=px,
                y=py,
                anchor_x="center",
                anchor_y="center",
                color=(sr, sg, sb, alpha),
            )
            s_label.draw()

        # ---------------- BARRAS DE RUIDO HORIZONTAL ----------------
        bands = 10
        for _ in range(bands):
            band_height = random.randint(4, 14)
            band_y = random.randint(y, y + h - band_height)
            br, bg, bb = self._glitch_color()
            band = shapes.Rectangle(x, band_y, w, band_height, color=(br, bg, bb))
            band.opacity = random.randint(70, 180)
            band.draw()

    def on_draw(self):
        if not self.engine or not self.engine.window:
            return

        self._make_labels()

        w = self.engine.window.width
        h = self.engine.window.height
        x, y, iw, ih = self._get_screen_bounds(w, h)

        # Fondo del CRT
        base = shapes.Rectangle(x, y, iw, ih, color=(5, 5, 5))
        base.draw()

        # Bisel oscuro
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

        # Scanlines siempre
        self._draw_scanlines(x, y, iw, ih)

        # --- TEXTO (posible glitch de corrupción) ---
        if self.console_label:
            base_text = self._get_base_text()

            if self.glitch_mode:
                intensity = 1.0  # glitch duro en la fase activa
                corrupted = self._corrupt_text(base_text, intensity)
                self.console_label.text = corrupted
            else:
                self.console_label.text = base_text

            ox, oy = self.console_label.x, self.console_label.y
            or_, og, ob, oa = self.console_label.color

            if self.glitch_mode:
                # Temblor del texto
                self.console_label.x = ox + random.randint(-2, 2)
                self.console_label.y = oy + random.randint(-2, 2)

                # Color del texto también se va a púrpura/rojo neón
                tr, tg, tb = self._glitch_color()
                self.console_label.color = (tr, tg, tb, oa)

            self._draw_glow_label(self.console_label)

            # Restauramos posición y color
            self.console_label.x, self.console_label.y = ox, oy
            self.console_label.color = (or_, og, ob, oa)

        # Glitch visual encima del texto
        if self.glitch_mode:
            self._draw_glitch(x, y, iw, ih)
    # ---------------- INPUT ----------------

    def on_key(self, symbol, modifiers):
        from pyglet.window import key

        # Si está bloqueado tras 3 fallos, ignoramos input
        if self.locked:
            return

        # Durante el glitch no hay input
        if self.glitch_mode:
            return

        # ENTER
        if symbol == key.ENTER:
            if self.login_mode:
                self._execute_login_attempt()
            else:
                self._execute_command()
            return

        # BACKSPACE = borrar último carácter
        if symbol == key.BACKSPACE:
            if self.current_input:
                self.current_input = self.current_input[:-1]
                self._text_dirty = True
            return

        # En Vatican Shell las flechas no hacen nada
        if symbol in (key.UP, key.DOWN):
            return

        # --- Construcción de carácter ---
        ch = None

        # Letras
        if key.A <= symbol <= key.Z:
            offset = symbol - key.A
            ch = chr(ord("A") + offset)
            if not (modifiers & key.MOD_SHIFT):
                ch = ch.lower()

        # Números
        elif key._0 <= symbol <= key._9:
            offset = symbol - key._0
            ch = str(offset)

        # Espacio
        elif symbol == key.SPACE:
            ch = " "

        # Algunos símbolos
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

        # Si se generó carácter, lo añadimos
        if ch:
            self.current_input += ch
            self._text_dirty = True

        # --- Cambios de color (no bloquean la escritura) ---
        if symbol == key.G:
            self.color_key = "green"
            self._text_dirty = True
        if symbol == key.A:
            self.color_key = "amber"
            self._text_dirty = True
        if symbol == key.W:
            self.color_key = "white"
            self._text_dirty = True
        if symbol == key.P:
            self.color_key = "purple"
            self._text_dirty = True

    # ---------------- COMANDOS ----------------

    def _execute_command(self):
        import pyglet.app

        raw_cmd = self.current_input.strip()
        if not raw_cmd:
            self._append_line_immediate(f"{self.prompt}")
            self.current_input = ""
            return

        # Echo
        self._append_line_immediate(f"{self.prompt}{raw_cmd}")

        cmd = raw_cmd.lower()

        # HELP
        if cmd == "help":
            block = [
                "",
                "COMMANDS",
                "",
                "[View ROMS] - Enter 'VIEW ROMS' to view installed roms.",
                "[Run]       - Enter 'RUN' followed by the title of the ROM you want to launch.",
                "[Reset]     - Enter 'RESET' to clear all system memory.",
                "[Quit]      - Enter 'QUIT' to quit Vatican Terminal.",
                "Use UP and DOWN arrows or MOUSE WHEEL to scroll. (Not implemented)",
                ""
            ]
            self._enqueue_lines(block)

        # VIEW ROMS
        elif cmd == "view roms" or cmd == "view roms.":
            block = [
                "",
                "Installed ROMS:",
                "  - Daemonum Index",
                "  - ARDE"
            ]
            self._enqueue_lines(block)


        

        # RUN ...
        elif cmd.startswith("run"):
            arg = raw_cmd[3:].strip()
            arg_norm = arg.lower().replace('"', "").strip()

            # RUN DAEMONUM INDEX
            if "daemonum" in arg_norm and "index" in arg_norm:
                block = [
                    "",
                    'Launching ROM "Daemonum Index"...',
                    ""
                ]
                self._enqueue_lines(block)
                self.current_input = ""

                # Entrar en modo login canónico
                self._start_canonical_login()
                return

            # RUN ARDE
            elif "arde" in arg_norm:
                block = [
                    "",
                    'Launching ROM "ARDE"...',
                    "",
                    "[ARDE] Initializing microfilm arrays...",
                    "[ARDE] Verifying Pontifical access tokens...",
                    "[ARDE] Mounting Archivum Romanum sectors...",
                    "[ARDE] Loading exorcism chronology index...",
                    "[ARDE] Optical checksum: OK",
                    "",
                ]
                self._enqueue_lines(block)
                self.current_input = ""

                # Saltar directamente a la ROM ARDE 82
                self.engine.go_to("arde")
                return

            # ROM DESCONOCIDO
            else:
                block = [
                    f'Unknown ROM "{arg}".',
                    ""
                ]
                self._enqueue_lines(block)

        elif cmd == "goto warning":
            # atajo de desarrollo: saltar directo a la advertencia
            self.engine.go_to("vatican_warning")
            self.current_input = ""
            return



        # RESET
        elif cmd == "reset":
            self.lines = []
            self.pending_lines = []
            self.login_mode = False
            self.login_attempts = 0
            self.locked = False
            self.prompt = self.shell_prompt

            header = [
                "Vatican Terminal [Version 3.1.8]",
                "(c) 1982 ExLibris TechnoSacrum Inc. All rights reserved.",
                "",
                "Enter HELP for more assistance.",
                ""
            ]
            self._enqueue_lines(header)

        # QUIT
        elif cmd == "quit":
            block = [
                "",
                "Exiting Vatican Terminal...",
                ""
            ]
            self._enqueue_lines(block)
            pyglet.app.exit()

        # Comando desconocido
        else:
            block = [
                f"'{raw_cmd}' is not recognized as a valid command.",
                "Type HELP for a list of commands.",
                ""
            ]
            self._enqueue_lines(block)

        # Limpiar input para el siguiente comando
        self.current_input = ""

    # ---------------- LOGIN CANÓNICO ----------------

    def _start_canonical_login(self):
        """
        Activa el modo de login para Daemonum Index.
        Limpia la pantalla para que el encabezado quede arriba, como una nueva "pantalla".
        """
        # Limpiar pantalla y colas
        self.lines = []
        self.pending_lines = []
        self.animation_scheduled = False
        try:
            pyglet.clock.unschedule(self._drain_pending_lines)
        except Exception:
            pass

        self.login_mode = True
        self.login_attempts = 0
        self.locked = False
        self.prompt = self.auth_prompt
        self.current_input = ""

        block = [
            "",
            "[DAEMONUM INDEX v2.3] Canonical Access Subsystem",
            "(c) 1982 ExLibris TechnoSacrum Inc. All rights reserved.",
            "",
            'Provide CANONICAL KEY: "Annus ritualis romanum exorcismi"',
            "",
        ]
        self._enqueue_lines(block)

    def _execute_login_attempt(self):
        """
        Maneja un intento de introducir la clave canónica.
        """
        raw = self.current_input.strip()

        # Echo del intento
        self._append_line_immediate(f"{self.prompt}{raw}")

        if raw == self.login_correct_key:
            # Clave correcta => glitch
            self.current_input = ""
            self.login_mode = False
            self.prompt = self.shell_prompt
            self._start_glitch()
        else:
            self.login_attempts += 1
            self.current_input = ""

            if self.login_attempts >= 3:
                # 3 fallos: mensaje + bloqueo 60s
                block = [
                    "",
                    "[SECURITY PROTOCOL: FAILURE X3]",
                    "Invalid attempts recorded",
                    "",
                    '"Erratis, nescientes Scripturas." Mt 22:29',
                    "",
                    "System will reset in 60 seconds.",
                    "",
                ]
                self._enqueue_lines(block)
                self.login_mode = False
                self.locked = True
                self.prompt = self.shell_prompt

                if not self._lock_reset_scheduled:
                    pyglet.clock.schedule_once(self._reset_after_lock, 60.0)
                    self._lock_reset_scheduled = True
            else:
                # Fallo pero todavía puede intentar
                block = [
                    "WRONG KEY.",
                    "",
                ]
                self._enqueue_lines(block)

    def _reset_after_lock(self, dt):
        """
        Tras los 60 segundos de bloqueo, se resetea el shell.
        """
        self.locked = False
        self.login_mode = False
        self.login_attempts = 0
        self._lock_reset_scheduled = False
        self.prompt = self.shell_prompt
        self.current_input = ""
        self.lines = []
        self.pending_lines = []

        header = [
            "Vatican Terminal [Version 3.1.8]",
            "(c) 1982 ExLibris TechnoSacrum Inc. All rights reserved.",
            "",
            "Enter HELP for more assistance.",
            ""
        ]
        self._enqueue_lines(header)

    # ---------------- GLITCH ----------------

    def _start_glitch(self):
        """
        Inicia el glitch cinematográfico previo a la advertencia.
        """
        self.glitch_mode = True
        self.glitch_timer = 0.0
        self.glitch_color_phase = 0.0
        self.text_alpha = 255  # por si acaso

    def _update_glitch(self, dt):
        if not self.glitch_mode:
            return

        self.glitch_timer += dt
        self.glitch_color_phase = min(1.0, self.glitch_timer / self.glitch_duration)

        if self.glitch_timer >= self.glitch_duration:
            # Termina el glitch: saltar a la pantalla de advertencia
            self.glitch_mode = False
            self.engine.go_to("vatican_warning")

    # ---------------- CORRUPCIÓN DE TEXTO ----------------

    def _corrupt_text(self, text: str, intensity: float) -> str:
        """
        Aplica glitch al texto:
        - Reemplaza caracteres por símbolos (▒█▓░⛧✟✞)
        - Mezcla mayúsculas/minúsculas
        - Cambia algunas palabras por fragmentos / palabras glitch
        intensity: 0.0 (suave) → 1.0 (fuerte)
        """
        if intensity <= 0.0 or not text:
            return text

        symbols = ["▒", "█", "▓", "░", "⛧", "✟", "✞"]
        glitch_words = ["NULL", "VOID", "ERR", "SCRPT", "DAEMON", "⛧⛧⛧"]

        # ---- Paso 1: char-level (símbolos + mayúsc/minúsc) ----
        chars_out = []
        replace_prob = 0.05 + 0.45 * intensity   # 5% → 50%
        flip_prob = 0.10 + 0.50 * intensity      # 10% → 60%

        for ch in text:
            if ch == "\n":
                chars_out.append(ch)
                continue

            # Reemplazo por símbolo
            if random.random() < replace_prob:
                chars_out.append(random.choice(symbols))
                continue

            # Mezcla de mayúsculas/minúsculas
            if ch.isalpha() and random.random() < flip_prob:
                if ch.islower():
                    ch = ch.upper()
                else:
                    ch = ch.lower()

            chars_out.append(ch)

        text_stage1 = "".join(chars_out)

        # ---- Paso 2: word-level (palabras glitch / fragmentos) ----
        lines_out = []
        word_sub_prob = 0.05 + 0.35 * intensity  # 5% → 40%

        for line in text_stage1.split("\n"):
            tokens = line.split(" ")
            if not tokens:
                lines_out.append(line)
                continue

            new_tokens = []
            for i, tok in enumerate(tokens):
                if not tok:
                    new_tokens.append(tok)
                    continue

                # ¿Sustituimos esta palabra?
                if random.random() < word_sub_prob:
                    # 50%: palabra glitch fija, 50%: fragmento de otra palabra
                    if random.random() < 0.5 or len(tokens) < 2:
                        new_tokens.append(random.choice(glitch_words))
                    else:
                        # fragmento de otra palabra de la línea
                        other_tok = tok
                        attempts = 0
                        while attempts < 3:
                            j = random.randrange(len(tokens))
                            if j != i and tokens[j]:
                                other_tok = tokens[j]
                                break
                            attempts += 1
                        start = 0
                        end = len(other_tok)
                        if end - start > 3:
                            start = random.randint(0, max(0, end - 3))
                        frag = other_tok[start:end]
                        new_tokens.append(frag)
                else:
                    new_tokens.append(tok)

            lines_out.append(" ".join(new_tokens))

        return "\n".join(lines_out)
