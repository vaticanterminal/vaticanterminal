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
    'assets', 'fonts', 'Glass_TTY_VT220.ttf'
)

FONT_NAME = "Glass TTY VT220"

COLOR_PRESETS = {
    "green":  (0, 255, 140, 255),
    "amber":  (255, 170, 60, 255),
    "white":  (230, 230, 230, 255),
    "purple": (200, 120, 255, 255),
}

SCREEN_MARGIN = 80  # margen del monitor dentro de la ventana


class VaticanFirmware(Scene):
    """
    Pantalla inicial de firmware:

    Vatican Terminal [Firmware v3.1.8]
    (c) 1982 ExLibris TechnoSacrum Inc. All rights reserved.

    Press ENTER to continue...
    """

    def __init__(self, engine):
        super().__init__(engine)

        self.font_name = "Courier New"
        self.color_key = "green"

        self.title_label = None

        # Boot CRT
        self.boot_sequence_played = False
        self.boot_active = False
        self.boot_timer = 0.0
        self.text_alpha = 0          # 0–255 (fade del texto)
        self.boot_noise_active = False

        # Overlay (flash fósforo)
        self.overlay_opacity = 0.0   # 0–1
        self.overlay_color = (0.0, 0.0, 0.0)

        # PERF: control de reconstrucción de labels
        self._labels_dirty = True
        self._last_size = (0, 0)

    # ---------------- FUENTE ----------------

    def _load_custom_font(self):
        if os.path.exists(FONT_FILE):
            try:
                pyglet.font.add_file(FONT_FILE)
                self.font_name = FONT_NAME
                print("[FONT] Cargada fuente VT220 (Firmware):", FONT_FILE)
                self._labels_dirty = True  # PERF: cambiar fuente => reconstruir label
            except Exception as e:
                print("[FONT] Error cargando fuente VT220 (Firmware):", e)
        else:
            print("[FONT] Archivo de fuente VT220 no encontrado (Firmware):", FONT_FILE)

    # ---------------- TEXTO ----------------

    def _firmware_text(self) -> str:
        return (
            "Vatican Terminal [Firmware v3.1.8]\n"
            "(c) 1982 ExLibris TechnoSacrum Inc. All rights reserved.\n"
            "\n"
            "\n"
            "Press ENTER to continue..."
        )

    # ---------------- CICLO DE VIDA ----------------

    def on_enter(self, **kwargs):
        self._load_custom_font()

        # Boot CRT solo la primera vez
        if not self.boot_sequence_played:
            self.boot_sequence_played = True
            self._start_boot()
        else:
            self.boot_active = False
            self.boot_timer = 0.0
            self.overlay_opacity = 0.0
            self.text_alpha = 255
            self.boot_noise_active = False

        self._labels_dirty = True  # PERF: forzar reconstrucción al entrar

    def _start_boot(self):
        """Inicializa el efecto de encendido CRT."""
        self.boot_active = True
        self.boot_timer = 0.0
        self.overlay_color = (0.9, 1.0, 0.9)
        self.overlay_opacity = 1.0
        self.text_alpha = 0
        self.boot_noise_active = False

    def _make_labels(self):
        """Crea el label central con el texto de firmware sólo si es necesario."""
        if not self.engine or not self.engine.window:
            return

        w = self.engine.window.width
        h = self.engine.window.height
        size = (w, h)

        # PERF: si ni cambió el tamaño ni el contenido, no recreamos
        if (
            not self._labels_dirty
            and self.title_label is not None
            and size == self._last_size
        ):
            return

        self._last_size = size
        self._labels_dirty = False

        x, y, iw, ih = self._get_screen_bounds(w, h)
        fw_text = self._firmware_text()

        self.title_label = Label(
            fw_text,
            x=x + 40,
            y=y + ih // 2,
            width=iw - 80,
            multiline=True,
            anchor_x="left",
            anchor_y="center",
            font_name=self.font_name,
            font_size=16,
            color=COLOR_PRESETS[self.color_key],
        )

    def on_update(self, dt):
        # PERF: solo actualizamos la lógica de boot; los labels se aseguran en on_draw
        self._update_boot(dt)

    def _update_boot(self, dt):
        """
        Mismo estilo de boot CRT que en VaticanTerminal:
        flash fósforo -> ruido VRAM -> fade-in de texto.
        """
        if not self.boot_active:
            return

        self.boot_timer += dt
        t = self.boot_timer

        FLASH_END = 0.18
        NOISE_START = 0.18
        NOISE_END = 0.42
        FADE_START = 0.90
        FADE_END = 2.00
        FINISH = 2.30

        if t < FLASH_END:
            # Flash de fósforo
            self.overlay_color = (0.9, 1.0, 0.9)
            self.overlay_opacity = 1.0 - (t / FLASH_END)
            self.text_alpha = 0
            self.boot_noise_active = False

        elif t < NOISE_END:
            # Pantalla de bloques tipo VRAM sucia
            self.overlay_opacity = 0.0
            self.boot_noise_active = True
            self.text_alpha = 0

        else:
            self.overlay_opacity = 0.0
            self.boot_noise_active = False

            # Fade-in del texto
            if t < FADE_START:
                self.text_alpha = 0
            elif t < FADE_END:
                k = (t - FADE_START) / (FADE_END - FADE_START)
                k = max(0.0, min(1.0, k))
                self.text_alpha = int(255 * k)
            else:
                self.text_alpha = 255

        # Fin del boot
        if t > FINISH:
            self.boot_active = False
            self.overlay_opacity = 0.0
            self.boot_noise_active = False
            self.text_alpha = 255

    # ---------------- GEOMETRÍA CRT 4:3 ----------------

    def _get_screen_bounds(self, w, h):
        w2 = w - SCREEN_MARGIN * 2
        h2 = h - SCREEN_MARGIN * 2
        if w2 / h2 > 4 / 3:
            ih = h2
            iw = int(ih * 4 / 3)
        else:
            iw = w2
            ih = int(iw * 3 / 4)
        x = (w - iw) // 2
        y = (h - ih) // 2
        return x, y, iw, ih

    # ---------------- DIBUJO ----------------

    def _draw_glow_label(self, label):
        if not label:
            return
        base_color = label.color
        r, g, b, _ = base_color
        a = int(self.text_alpha)
        base_color = (r, g, b, a)

        ox, oy = label.x, label.y
        glow_color = (r, g, b, int(a * 0.35))

        # Glow alrededor
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            label.color = glow_color
            label.x, label.y = ox + dx, oy + dy
            label.draw()

        # Texto principal
        label.color = base_color
        label.x, label.y = ox, oy
        label.draw()

    def on_draw(self):
        if not self.engine or not self.engine.window:
            return

        # PERF: aseguramos labels sólo aquí
        self._make_labels()

        w = self.engine.window.width
        h = self.engine.window.height
        x, y, iw, ih = self._get_screen_bounds(w, h)

        # BASE CRT
        base = shapes.Rectangle(x, y, iw, ih, color=(5, 5, 5))
        base.draw()

        # VIÑETA / CURVATURA
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

        # Ruido de boot
        if self.boot_active and self.boot_noise_active:
            self._draw_boot_noise(x, y, iw, ih)

        # TEXTO
        self._draw_glow_label(self.title_label)

        # SCANLINES
        self._draw_scanlines(x, y, iw, ih)

        # OVERLAY flash fósforo
        if self.overlay_opacity > 0:
            r, g, b = self.overlay_color
            if 0 <= r <= 1 and 0 <= g <= 1 and 0 <= b <= 1:
                rgb = (int(r * 255), int(g * 255), int(b * 255))
            else:
                rgb = (int(r), int(g), int(b))
            ov = shapes.Rectangle(x, y, iw, ih, color=rgb)
            ov.opacity = int(max(0.0, min(1.0, self.overlay_opacity)) * 255)
            ov.draw()

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
        base_alpha = 70 if self.boot_active else 50
        color = (0, 30, 0)
        for yy in range(y, y + h, 2):
            line = shapes.Rectangle(x, yy + flick, w, 1, color=color)
            line.opacity = base_alpha
            line.draw()

    # ---------------- INPUT ----------------

    def on_key(self, symbol, modifiers):
        from pyglet.window import key

        # Cambio de color opcional (por si quieres)
        if symbol == key.G:
            self.color_key = "green"
        elif symbol == key.A:
            self.color_key = "amber"
        elif symbol == key.W:
            self.color_key = "white"
        elif symbol == key.P:
            self.color_key = "purple"
            self._labels_dirty = True  # si quieres que el label tome el nuevo color inmediatamente

        # ENTER: pasar a sistema de login de la ROM (Daemonum Index)
        if symbol == key.ENTER:
            self.engine.go_to("vatican_shell")
