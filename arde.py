# arde.py

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
    "green":  (0, 255, 140, 255),
    "amber":  (255, 170, 60, 255),
    "white":  (230, 230, 230, 255),
    "purple": (200, 120, 255, 255),
}

SCREEN_MARGIN = 80



class Arde(Scene):
    """
    ARDE — Archivum Romanum de Disturbia Extraordinaria
    """

    def __init__(self, engine):
        super().__init__(engine)

        self.font_name = "Courier New"
        self.color_key = "green"

        # Texto principal
        self.label = None

        # Estados internos
        self.mode = "console"         # "console", "run_case", "photo"
        self.console_lines = []       # buffer de consola
        self.case_lines = []          # buffer del caso RUN
        self.scroll = 0               # scroll consola
        self.case_scroll = 0          # scroll en casos
        self.max_lines = 22           # líneas visibles
        self._max_scroll = 0
        self._max_case_scroll = 0

        # Prompt
        self.prompt = r"C:\VaticanTerminal 1982\ARDE>"
        self.current_input = ""
        self.cursor_visible = True
        pyglet.clock.schedule_interval(self._toggle_cursor, 0.5)

        self._text_dirty = True
        self._last_size = (0, 0)

        # Casos y fotos
        self.current_entry = None
        self.loaded_images = {}
        self.image_paths = {}
        self.photo_texts = {}

        # Reconocimiento exacto de casos
        self.case_keys = {
            "1": 1, "01": 1, "aubry": 1, "nicole": 1, "nca-78": 1,
            "2": 2, "02": 2, "loudun": 2, "ldn-34": 2,
            "3": 3, "03": 3, "anna": 3, "emma": 3, "ecklund": 3, "ae-28": 3,
            "4": 4, "04": 4, "robbie": 4, "mannheim": 4, "rm-49": 4,
        }

        # Construir textos
        self._build_texts()
        self._setup_images()


    # ------------------------------------------------------
    #              CICLO DE VIDA DE LA ESCENA
    # ------------------------------------------------------
    def on_enter(self, **kwargs):
        self._load_custom_font()
        self._init_console_header()
        self.mode = "console"
        self.current_input = ""
        self.scroll = 0
        self.case_scroll = 0
        self._text_dirty = True
        self.current_entry = None


    # ------------------------------------------------------
    #                   FUENTE VT220
    # ------------------------------------------------------
    def _load_custom_font(self):
        if os.path.exists(FONT_FILE):
            try:
                pyglet.font.add_file(FONT_FILE)
                self.font_name = FONT_NAME
            except:
                pass


    # ------------------------------------------------------
    #                   TEXTOS ESTÁTICOS
    # ------------------------------------------------------
    def _build_texts(self):

        # Header fijo
        self.header_text = (
            "[ARDE] Archivum Romanum de Disturbia Extraordinaria\n"
            "Anomaly & Exorcism Chronology Access Subsystem v1.3\n"
            "(c) 1982 ExLibris TechnoSacrum Inc. — All rights reserved.\n"
            "\n"
            "This ROM contains restricted records extracted from the Pontifical Archives.\n"
            "It summarizes the most cited exorcism events in ecclesiastical documentation\n"
            "from the 1st to the 20th century.\n"
            "\n"
            "Enter HELP for additional assistance.\n"
        )

        # HELP
        self.help_block = (
            "\n"
            "COMMANDS\n"
            "\n"
            "[VIEW INFESTATION]  - Enter 'VIEW INFESTATION' to view infestation records.\n"
            "[RUN]               - Enter 'RUN' followed by the infestation name or code.\n"
            "[PHOTO]             - Enter 'PHOTO' inside an open infestation record.\n"
            "[RESET]             - Clears the console, preserving the ARDE header.\n"
            "[BACK]              - Returns to the previous screen or exits ARDE.\n"
            "[QUIT]              - Exits to Vatican Shell.\n"
        )

        # LISTA INFESTATION
        self.infestation_block = (
            "\n"
            "[01] Nicole Aubry — France / 1565–1578\n"
            "     Status: Early canonical indicators (pre-Rituale Romanum)\n"
            "     Entry: NCA-78\n"
            "\n"
            "[02] Loudun Convent — France / 1634\n"
            "     Status: Collective infestation pattern (Ursuline order)\n"
            "     Entry: LDN-34\n"
            "\n"
            "[03] Anna Ecklund — USA / 1928\n"
            "     Status: Documented long-term infestation (Earling case)\n"
            "     Entry: AE-28\n"
            "\n"
            "[04] Robbie Mannheim — USA / 1949\n"
            "     Status: Pre-possession escalation (inspiration for The Exorcist)\n"
            "     Entry: RM-49\n"
            "\n"
            "Type RUN <case> to retrieve the full historical record.\n"
        )

        # Casos RUN
        self.entry_texts = {
            1: (
                "[RUN — NICOLE AUBRY]\n"
                "France, 1565–1578\n"
                "\n"
                "Los archivos del caso de Nicole Aubry documentan múltiples fenómenos\n"
                "de glosolalia, fuerza inusual y reacciones violentas ante sacramentales.\n"
                "Testigos afirman que su temperatura corporal descendía al contacto con\n"
                "un crucifijo. Las voces reclamaban ser Beelzebub o Baalberith.\n"
                "\n"
                "Press BACK to return.\n"
            ),
            2: (
                "[RUN — LOUDUN CONVENT]\n"
                "France, 1634\n"
                "\n"
                "Las monjas de Loudun mostraban signos de posesión y voces atribuidas a\n"
                "Asmodeus y Leviathan. El exorcista Surin declaró episodios de frío súbito\n"
                "y condensación. Las manifestaciones parecían coordinadas.\n"
                "\n"
                "Press BACK to return.\n"
            ),
            3: (
                "[RUN — ANNA/EMMA ECKLUND]\n"
                "USA, 1928\n"
                "\n"
                "Caso documentado por Riesinger. Emma presentaba mutismo, glosolalia,\n"
                "vómitos y transformaciones faciales breves. Voces reclamaban ser Belial\n"
                "y Behemoth durante varias sesiones.\n"
                "\n"
                "Press BACK to return.\n"
            ),
            4: (
                "[RUN — ROBBIE MANNHEIM]\n"
                "USA, 1949\n"
                "\n"
                "Bowdern y Bishop registraron desplazamiento de muebles, descenso térmico\n"
                "y marcas en la piel. Cuatro objetos religiosos generaban fuertes\n"
                "reacciones. El caso inspiró 'The Exorcist'.\n"
                "\n"
                "Press BACK to return.\n"
            ),
        }


    # ------------------------------------------------------
    #                   FOTOS
    # ------------------------------------------------------
    def _setup_images(self):
        base = os.path.join(os.path.dirname(__file__), "assets", "images")
        self.image_paths = {
            1: os.path.join(base, "03.png"),
            2: os.path.join(base, "01.png"),
            3: os.path.join(base, "02.png"),
            4: os.path.join(base, "04.png"),
        }

        self.photo_texts = {
            1: "[PHOTO — NICOLE AUBRY]\nArchival visual reference.\nPress BACK to return.",
            2: "[PHOTO — LOUDUN]\nReconstruction still.\nPress BACK to return.",
            3: "[PHOTO — ANNA/EMMA]\n convent archival still.\nPress BACK to return.",
            4: "[PHOTO — ROBBIE]\nNewspaper microfilm.\nPress BACK to return.",
        }


    # ------------------------------------------------------
    #              INICIALIZAR CONSOLA (HEADER)
    # ------------------------------------------------------
    def _init_console_header(self):
        self.console_lines = self.header_text.splitlines()
        self.scroll = 0
        self._recalc_console_scroll()


    # ------------------------------------------------------
    #              CÁLCULO DE ÁREA CRT 4:3
    # ------------------------------------------------------
    def _get_screen_bounds(self):
        w = self.engine.window.width
        h = self.engine.window.height

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


    # ------------------------------------------------------
    #              TEXTO VISIBLE SEGÚN MODO
    # ------------------------------------------------------
    def _get_full_text(self):
        cursor = "|" if self.cursor_visible else " "
        prompt_line = f"{self.prompt}{self.current_input}{cursor}"

        if self.mode == "console":
            start = max(0, min(self.scroll, max(0, len(self.console_lines) - self.max_lines)))
            visible = self.console_lines[start:start + self.max_lines]
            visible.append("")
            visible.append(prompt_line)
            return "\n".join(visible)

        if self.mode == "run_case":
            start = max(0, min(self.case_scroll, max(0, len(self.case_lines) - self.max_lines)))
            visible = self.case_lines[start:start + self.max_lines]
            visible.append("")
            visible.append(prompt_line)
            return "\n".join(visible)

        if self.mode == "photo":
            txt = self.photo_texts.get(self.current_entry, "[No photo available]")
            visible = txt.splitlines()[:self.max_lines]
            visible.append("")
            visible.append(prompt_line)
            return "\n".join(visible)

        return prompt_line


    # ------------------------------------------------------
    #                LABEL / RENDER
    # ------------------------------------------------------
    def _make_label(self):
        if not self.engine.window:
            return

        w, h = self.engine.window.width, self.engine.window.height
        if (w, h) == self._last_size and not self._text_dirty:
            return

        self._last_size = (w, h)
        self._text_dirty = False

        x, y, iw, ih = self._get_screen_bounds()
        txt = self._get_full_text()

        self.label = Label(
            txt,
            x=x + 40,
            y=y + ih - 60,
            width=iw - 80,
            multiline=True,
            font_name=self.font_name,
            font_size=14,
            color=COLOR_PRESETS[self.color_key]
        )


    def on_update(self, dt):
        self._make_label()


    # ------------------------------------------------------
    #                     DRAW
    # ------------------------------------------------------
    def on_draw(self):
        if not self.engine.window:
            return

        self._make_label()

        x, y, iw, ih = self._get_screen_bounds()

        # Fondo CRT
        bg = shapes.Rectangle(x, y, iw, ih, color=(5, 5, 5))
        bg.draw()

        # Bordes CRT
        opacity = 120
        band = 20
        for dx, dy, bw, bh in (
            (x, y + ih - band, iw, band),
            (x, y, iw, band),
            (x, y, band, ih),
            (x + iw - band, y, band, ih),
        ):
            v = shapes.Rectangle(dx, dy, bw, bh, color=(0, 0, 0))
            v.opacity = opacity
            v.draw()

        # Scanlines
        self._draw_scanlines(x, y, iw, ih)

        # Modo PHOTO: dibujar imagen centrada
        if self.mode == "photo":
            self._ensure_photo_loaded(self.current_entry)
            self._draw_photo(x, y, iw, ih)

        # Glow del texto
        if self.label:
            self._draw_glow(self.label)


    def _draw_scanlines(self, x, y, w, h):
        color = (0, 30, 0)
        base_alpha = 55
        flick = random.uniform(-1, 1)
        for yy in range(y, y + h, 2):
            line = shapes.Rectangle(x, yy + flick, w, 1, color=color)
            line.opacity = base_alpha
            line.draw()


    def _draw_glow(self, label):
        ox, oy = label.x, label.y
        r, g, b, a = label.color
        glow = (r, g, b, int(0.35 * 255))

        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            label.color = glow
            label.x = ox + dx
            label.y = oy + dy
            label.draw()

        label.color = (r,g,b,a)
        label.x = ox
        label.y = oy
        label.draw()


    # ------------------------------------------------------
    #                        FOTO
    # ------------------------------------------------------
    def _ensure_photo_loaded(self, entry):
        if entry in self.loaded_images:
            return
        path = self.image_paths.get(entry)
        if path and os.path.exists(path):
            img = pyglet.image.load(path)
            self.loaded_images[entry] = pyglet.sprite.Sprite(img)


    def _draw_photo(self, x, y, iw, ih):
        spr = self.loaded_images.get(self.current_entry)
        if not spr:
            return

        max_w = iw * 0.6
        max_h = ih * 0.4

        scale_w = max_w / spr.width
        scale_h = max_h / spr.height
        scale = min(1.0, scale_w, scale_h)

        spr.update(
            x=x + (iw - spr.width * scale) / 2,
            y=y + (ih - spr.height * scale) / 2,
            scale=scale
        )
        spr.draw()


    # ------------------------------------------------------
    #                     CURSOR
    # ------------------------------------------------------
    def _toggle_cursor(self, dt):
        self.cursor_visible = not self.cursor_visible
        self._text_dirty = True


    # ------------------------------------------------------
    #                SCROLL LIMITS
    # ------------------------------------------------------
    def _recalc_console_scroll(self):
        self._max_scroll = max(0, len(self.console_lines) - self.max_lines)
        self.scroll = min(self.scroll, self._max_scroll)


    def _recalc_case_scroll(self):
        self._max_case_scroll = max(0, len(self.case_lines) - self.max_lines)
        self.case_scroll = min(self.case_scroll, self._max_case_scroll)


    # ------------------------------------------------------
    #                PROCESAMIENTO DE COMANDOS
    # ------------------------------------------------------
    def _execute_command(self, cmd):
        raw = cmd.strip()
        if not raw:
            return

        lower = raw.lower()
        self.current_input = ""
        self._text_dirty = True

        # BACK
        if lower == "back":
            if self.mode == "console":
                self.engine.go_to("vatican_shell")
            else:
                self.mode = "console"
                self.current_entry = None
            return

        # RESET
        if lower == "reset":
            self._init_console_header()
            self.mode = "console"
            self.current_entry = None
            return

        # QUIT
        if lower == "quit":
            self.engine.go_to("vatican_shell")
            return

        # HELP
        if lower == "help":
            if self.mode == "console":
                self.console_lines.extend(self.help_block.splitlines())
                self._recalc_console_scroll()
            return

        # VIEW INFESTATION (exacto)
        if lower == "view infestation":
            if self.mode == "console":
                self.console_lines.extend(self.infestation_block.splitlines())
                self._recalc_console_scroll()
            return

        # PHOTO (solo dentro del caso)
        if lower == "photo":
            if self.mode == "run_case" and self.current_entry is not None:
                self.mode = "photo"
            else:
                if self.mode == "console":
                    self.console_lines.append(
                        "PHOTO can only be used inside an infestation record."
                    )
                    self._recalc_console_scroll()
                else:
                    self.case_lines.append(
                        "[System] PHOTO can only be used inside an infestation record."
                    )
                    self._recalc_case_scroll()
            return

        # RUN <case>
        if lower.startswith("run "):
            parts = raw.split()
            if len(parts) < 2:
                # RUN sin argumento
                if self.mode == "console":
                    self.console_lines.append("Usage: RUN <infestation name or code>")
                    self._recalc_console_scroll()
                else:
                    self.case_lines.append("[System] Usage: RUN <infestation name or code>")
                    self._recalc_case_scroll()
                return

            key = parts[1].lower()
            if key in self.case_keys:
                entry = self.case_keys[key]
                self.current_entry = entry
                self.case_lines = self.entry_texts.get(entry, "").splitlines()
                self.case_scroll = 0
                self._recalc_case_scroll()
                self.mode = "run_case"
            else:
                # caso desconocido
                if self.mode == "console":
                    self.console_lines.append(
                        f"Unknown infestation record '{parts[1]}'. Type VIEW INFESTATION for the list."
                    )
                    self._recalc_console_scroll()
                else:
                    self.case_lines.append(
                        f"[System] Unknown infestation record '{parts[1]}'. Type BACK to return."
                    )
                    self._recalc_case_scroll()
            return

        # RUN sin espacio → error
        if lower == "run":
            if self.mode == "console":
                self.console_lines.append("Usage: RUN <infestation name or code>")
                self._recalc_console_scroll()
            else:
                self.case_lines.append("[System] Usage: RUN <infestation name or code>")
                self._recalc_case_scroll()
            return

        # -------------------------
        # COMANDO NO RECONOCIDO
        # -------------------------
        if self.mode == "console":
            self.console_lines.append(
                f"Unrecognized command: '{raw}'. Type HELP for a list of valid commands."
            )
            self._recalc_console_scroll()
        else:
            self.case_lines.append(
                f"[System] Unrecognized command: '{raw}'. Type BACK to return."
            )
            self._recalc_case_scroll()



    # ------------------------------------------------------
    #                     TECLADO
    # ------------------------------------------------------
    def on_key(self, symbol, modifiers):
        from pyglet.window import key

        # Scroll consola / caso
        if symbol == key.UP:
            if self.mode == "console":
                if self.scroll > 0:
                    self.scroll -= 1
                    self._text_dirty = True
            elif self.mode == "run_case":
                if self.case_scroll > 0:
                    self.case_scroll -= 1
                    self._text_dirty = True
            return

        if symbol == key.DOWN:
            if self.mode == "console":
                if self.scroll < self._max_scroll:
                    self.scroll += 1
                    self._text_dirty = True
            elif self.mode == "run_case":
                if self.case_scroll < self._max_case_scroll:
                    self.case_scroll += 1
                    self._text_dirty = True
            return

        # Letras
        if key.A <= symbol <= key.Z:
            ch = chr(symbol).lower()

            # Cambiar color y escribir la letra
            if symbol == key.G:
                self.color_key = "green"
            elif symbol == key.A:
                self.color_key = "amber"
            elif symbol == key.W:
                self.color_key = "white"
            elif symbol == key.P:
                self.color_key = "purple"

            self.current_input += ch
            self._text_dirty = True
            return

        # Números
        if key._0 <= symbol <= key._9:
            self.current_input += str(symbol - key._0)
            self._text_dirty = True
            return

        # Espacio
        if symbol == key.SPACE:
            self.current_input += " "
            self._text_dirty = True
            return

        # Borrar
        if symbol == key.BACKSPACE:
            if self.current_input:
                self.current_input = self.current_input[:-1]
                self._text_dirty = True
            return

        # ENTER → ejecutar comando
        if symbol == key.ENTER:
            cmd = self.current_input.strip()
            if cmd:
                self._execute_command(cmd)
            return

        # ESCAPE → salir
        if symbol == key.ESCAPE:
            self.engine.go_to("vatican_shell")
            return
