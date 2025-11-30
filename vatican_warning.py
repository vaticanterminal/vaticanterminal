from scene import Scene
from pyglet.text import Label
from pyglet import shapes
import pyglet
import random
import os

FONT_FILE = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "fonts",
    "Glass_TTY_VT220.ttf"
)

FONT_NAME = "Glass TTY VT220"
SCREEN_MARGIN = 80


BODY_LINES = [
    "The Daemonum Index ROM contains highly classified material involving",
    "preternatural phenomena, sealed investigations, and testimonies that",
    "were never intended for public eyes. Some entries remain incomplete,",
    "censored, or spiritually hazardous for unprepared personnel.",
    "",
    "• Access requires EXORCIST CLEARANCE LEVEL XII",
    "• Certain dossiers involve minors and clergy under pontifical seal",
    "• Every access event is logged by the Audit Daemon",
    "",
    "Loading security directives...",
    "",
    "Issued under the authority of Pope John Paul II.",
]


class VaticanWarning(Scene):
    """Cinematic CRT warning screen before Daemonum Index."""

    def __init__(self, engine):
        super().__init__(engine)
        self.font_name = FONT_NAME

        self.elapsed_time = 0.0
        self.duration = 35.0  # seconds before auto-transition
        self.dot_timer = 0.0
        self.dot_state = 0  # 0-3 dots for LOADING...

        self._dirty = True

    def on_enter(self, **kwargs):
        try:
            pyglet.font.add_file(FONT_FILE)
        except Exception:
            pass

        self.elapsed_time = 0.0
        self.dot_timer = 0.0
        self.dot_state = 0
        self._dirty = True

    # ----------------- GEOMETRÍA CRT -----------------

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

    # ----------------- UPDATE -----------------

    def on_update(self, dt):
        self.elapsed_time += dt
        self.dot_timer += dt

        if self.dot_timer >= 0.6:
            self.dot_timer = 0.0
            self.dot_state = (self.dot_state + 1) % 4
        # no need to mark dirty; loading label is rebuilt every frame

        if self.elapsed_time >= self.duration:
            self.engine.go_to("vatican_terminal")
            return

    # ----------------- DRAW HELPERS -----------------

    def _draw_glow_label(self, label, core_color, glow_color=None, glow_radius=1):
        """Simple CRT glow: blurred copies around, then main text."""
        if not label:
            return

        if glow_color is None:
            r, g, b, a = core_color
            glow_color = (r, g, b, int(a * 0.35))

        ox, oy = label.x, label.y
        label.color = glow_color

        for dx, dy in ((glow_radius, 0), (-glow_radius, 0),
                       (0, glow_radius), (0, -glow_radius)):
            label.x, label.y = ox + dx, oy + dy
            label.draw()

        label.x, label.y = ox, oy
        label.color = core_color
        label.draw()

    def _scanlines(self, x, y, w, h):
        flick = random.uniform(-1, 1)
        alpha = 55
        color = (0, 30, 0)
        for yy in range(y, y + h, 2):
            line = shapes.Rectangle(x, yy + flick, w, 1, color=color)
            line.opacity = alpha
            line.draw()

    # ----------------- DRAW -----------------

    def on_draw(self):
        if not self.engine or not self.engine.window:
            return

        w = self.engine.window.width
        h = self.engine.window.height
        x, y, iw, ih = self._get_screen_bounds(w, h)

        # Background CRT
        bg = shapes.Rectangle(x, y, iw, ih, color=(6, 6, 6))
        bg.draw()

        # Bezel
        opacity = 100
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

        # Flicker alpha for text
        flicker = random.randint(-10, 10)
        base_alpha = max(180, min(255, 255 + flicker))

        # ---- Title (centered, red with glow) ----
        title_text = "WARNING // DAEMONUM INDEX ROM"
        title_label = Label(
            title_text,
            x=x + iw // 2,
            y=y + ih - 70,
            anchor_x="center",
            anchor_y="center",
            font_name=self.font_name,
            font_size=18,
            color=(255, 40, 40, base_alpha),
        )
        title_core = (255, 40, 40, base_alpha)
        title_glow = (255, 40, 40, int(base_alpha * 0.4))
        self._draw_glow_label(title_label, title_core, title_glow, glow_radius=2)

        # ---- Body lines (amber text, red bullets) ----
        line_height = 20
        current_y = y + ih - 120
        text_x = x + 40

        for line in BODY_LINES:
            if not line:
                current_y -= line_height  # blank line
                continue

            if line.startswith("•"):
                # Bullet in red, text in amber
                bullet_label = Label(
                    "•",
                    x=text_x,
                    y=current_y,
                    font_name=self.font_name,
                    font_size=15,
                    anchor_x="left",
                    anchor_y="baseline",
                    color=(255, 40, 40, base_alpha),
                )
                bullet_core = (255, 40, 40, base_alpha)
                bullet_glow = (255, 40, 40, int(base_alpha * 0.5))
                self._draw_glow_label(bullet_label, bullet_core, bullet_glow, glow_radius=1)

                body_text = line[1:].lstrip()
                body_label = Label(
                    body_text,
                    x=text_x + 20,
                    y=current_y,
                    font_name=self.font_name,
                    font_size=15,
                    anchor_x="left",
                    anchor_y="baseline",
                    color=(255, 170, 60, base_alpha),
                )
                body_core = (255, 170, 60, base_alpha)
                body_glow = (255, 170, 60, int(base_alpha * 0.4))
                self._draw_glow_label(body_label, body_core, body_glow, glow_radius=1)
            else:
                body_label = Label(
                    line,
                    x=text_x,
                    y=current_y,
                    font_name=self.font_name,
                    font_size=15,
                    anchor_x="left",
                    anchor_y="baseline",
                    color=(255, 170, 60, base_alpha),
                )
                body_core = (255, 170, 60, base_alpha)
                body_glow = (255, 170, 60, int(base_alpha * 0.4))
                self._draw_glow_label(body_label, body_core, body_glow, glow_radius=1)

            current_y -= line_height

        # ---- LOADING indicator (bottom-right, red) ----
        dots = "." * self.dot_state
        loading_text = f"LOADING{dots}"
        loading_label = Label(
            loading_text,
            x=x + iw - 180,
            y=y + 40,
            font_name=self.font_name,
            font_size=14,
            anchor_x="left",
            anchor_y="baseline",
            color=(255, 50, 50, base_alpha),
        )
        load_core = (255, 50, 50, base_alpha)
        load_glow = (255, 50, 50, int(base_alpha * 0.4))
        self._draw_glow_label(loading_label, load_core, load_glow, glow_radius=1)

        # ---- Subtle "Audit Daemon" Latin fragments (glitch monitoring) ----
        latin_fragments = [
            "Vade retro Satana",
            "Libera nos a malo",
            "In Nomine Patris",
            "Exsurge Domine",
            "Deus in adiutorium",
        ]
        for _ in range(3):
            frag = random.choice(latin_fragments)
            fx = random.randint(x + iw // 2, x + iw - 40)
            fy = random.randint(y + 60, y + ih - 100)
            frag_alpha = random.randint(40, 90)
            frag_label = Label(
                frag,
                x=fx,
                y=fy,
                font_name=self.font_name,
                font_size=10,
                anchor_x="left",
                anchor_y="baseline",
                color=(200, 120, 255, frag_alpha),
            )
            frag_core = (200, 120, 255, frag_alpha)
            frag_glow = (200, 120, 255, int(frag_alpha * 0.6))
            self._draw_glow_label(frag_label, frag_core, frag_glow, glow_radius=1)

        # ---- Scanlines over everything ----
        self._scanlines(x, y, iw, ih)

    def on_key(self, symbol, modifiers):
        # No input on this screen; it auto-continues.
        pass
