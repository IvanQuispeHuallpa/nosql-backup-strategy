"""Generate the PNG diagrams used in the Medium articles (Medium does not accept SVG)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
FONT = "C:/Windows/Fonts/arial.ttf"
BOLD = "C:/Windows/Fonts/arialbd.ttf"
MONO = "C:/Windows/Fonts/consola.ttf"
BG, CARD, FG, MUTED, GREEN, BLUE, AMBER = "#0f172a", "#1e293b", "#e2e8f0", "#94a3b8", "#10b981", "#38bdf8", "#f59e0b"


def font(path, size):
    return ImageFont.truetype(path, size)


def box(draw, xy, title, subtitle, color):
    draw.rounded_rectangle(xy, radius=18, fill=CARD, outline=color, width=3)
    x0, y0, x1, _ = xy
    draw.text(((x0 + x1) / 2, y0 + 38), title, font=font(BOLD, 28), fill=FG, anchor="mm")
    draw.text(((x0 + x1) / 2, y0 + 78), subtitle, font=font(FONT, 20), fill=MUTED, anchor="mm")


def arrow(draw, start, end, label=None, color=MUTED):
    draw.line([start, end], fill=color, width=4)
    ex, ey = end
    sx, sy = start
    d = 1 if ex >= sx else -1
    if abs(ex - sx) >= abs(ey - sy):
        draw.polygon([(ex, ey), (ex - 16 * d, ey - 9), (ex - 16 * d, ey + 9)], fill=color)
    else:
        d = 1 if ey >= sy else -1
        draw.polygon([(ex, ey), (ex - 9, ey - 16 * d), (ex + 9, ey - 16 * d)], fill=color)
    if label:
        draw.text(((sx + ex) / 2, (sy + ey) / 2 - 20), label, font=font(FONT, 18), fill=color, anchor="mm")


def architecture():
    img = Image.new("RGB", (1400, 640), BG)
    d = ImageDraw.Draw(img)
    d.text((700, 50), "Arquitectura del backup", font=font(BOLD, 40), fill=FG, anchor="mm")
    box(d, (60, 200, 360, 320), "Usuarios", "navegador / clientes API", MUTED)
    box(d, (480, 200, 800, 320), "App Flask", "Render (Docker)", GREEN)
    box(d, (940, 200, 1340, 320), "MongoDB Atlas", "M0 gratis, sin snapshots", BLUE)
    box(d, (940, 440, 1340, 560), "GitHub Actions", "cron: mongodump diario", AMBER)
    box(d, (480, 440, 800, 560), "Artefacto cifrado", "AES-256, retención 30 días", AMBER)
    arrow(d, (360, 260), (480, 260))
    arrow(d, (800, 260), (940, 260))
    arrow(d, (1140, 320), (1140, 440), "mongodump --gzip", AMBER)
    arrow(d, (940, 500), (800, 500), "openssl + subida", AMBER)
    img.save(OUT / "01-architecture.png")


def pipeline():
    img = Image.new("RGB", (1400, 420), BG)
    d = ImageDraw.Draw(img)
    d.text((700, 50), "CI/CD y automatización de backups", font=font(BOLD, 40), fill=FG, anchor="mm")
    steps = [("git push", "rama main", MUTED), ("pytest", "pruebas", BLUE), ("Simulacro", "dump + restore", GREEN),
             ("Despliegue", "hook Render", GREEN), ("Backup cron", "diario 06:00 UTC", AMBER)]
    w, gap = 220, 50
    x = 60
    for i, (title, sub, color) in enumerate(steps):
        box(d, (x, 160, x + w, 280), title, sub, color)
        if i < len(steps) - 1:
            arrow(d, (x + w, 220), (x + w + gap, 220))
        x += w + gap
    d.text((700, 350), "Cada push comprueba que un backup se puede restaurar antes de desplegar el código.", font=font(FONT, 24), fill=MUTED, anchor="mm")
    img.save(OUT / "02-pipeline.png")


def terminal():
    lines = [
        ("$ python -m app.backup create", FG),
        ('{ "name": "notesdb-20261021T091008Z", "size_bytes": 460,', MUTED),
        ('  "counts": { "notes": 10 } }', MUTED),
        ("", FG),
        ("$ mongosh notesdb --eval 'db.dropDatabase()'   # disaster", AMBER),
        ("after disaster: 0", AMBER),
        ("", FG),
        ("$ python -m app.backup restore notesdb-20261021T091008Z", FG),
        ("$ mongosh notesdb --eval 'db.notes.countDocuments()'", FG),
        ("after restore: 10", GREEN),
        ("", FG),
        ("$ python -m app.backup verify notesdb-20261021T091008Z", FG),
        ('{ "ok": true, "expected": {"notes": 10}, "restored": {"notes": 10} }', GREEN),
    ]
    img = Image.new("RGB", (1400, 90 + 36 * len(lines)), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 20, 1380, img.height - 20), radius=14, fill="#020617")
    for i, c in enumerate(("#ef4444", "#f59e0b", "#10b981")):
        d.ellipse((44 + i * 30, 40, 62 + i * 30, 58), fill=c)
    y = 80
    for text, color in lines:
        d.text((50, y), text, font=font(MONO, 24), fill=color)
        y += 36
    img.save(OUT / "04-terminal-restore.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture()
    pipeline()
    terminal()
