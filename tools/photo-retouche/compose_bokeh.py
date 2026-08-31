"""Fond exterieur tres flou (bokeh) + sujet detoure : rendu type mode portrait."""
import math, os, random
from PIL import Image, ImageFilter, ImageEnhance, ImageChops, ImageDraw

SCR = os.environ.get('WORKDIR', './work/')
SRC = os.environ.get('SRC', SCR + 'source.jpg')
random.seed(23)

photo = Image.open(SRC).convert('RGB')
S = photo.size[0]

# ---------- base : masses colorees organiques (aucune forme identifiable) ----------
# palette d'une rue ensoleillee : ciel clair, feuillages, pierre chaude, ombre au sol
base = Image.new('RGB', (S, S), (206, 190, 168))
d = ImageDraw.Draw(base, 'RGBA')

def band(y0, y1, c0, c1):
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0)
        d.line([(0, y), (S, y)],
               fill=tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)))

band(0, int(0.34 * S), (222, 228, 232), (231, 219, 196))      # ciel / haut lumineux
band(int(0.34 * S), int(0.70 * S), (231, 219, 196), (196, 168, 134))  # facades chaudes
band(int(0.70 * S), S, (196, 168, 134), (128, 112, 96))        # sol, plus sombre

# masses organiques : feuillages, ombres, taches de lumiere
BLOBS = [((0.02, 0.14), (128, 142, 104), 0.30, 22),  # feuillage gauche, adouci
         ((0.96, 0.08), (112, 132, 96), 0.36, 26),   # feuillage droit
         ((0.74, 0.42), (146, 152, 116), 0.15, 12),  # verdure basse
         ((0.26, 0.52), (218, 188, 148), 0.28, 18),  # mur au soleil
         ((0.90, 0.60), (198, 168, 134), 0.24, 16),  # mur a droite
         ((0.08, 0.70), (158, 138, 116), 0.22, 14),  # zone d'ombre
         ((0.50, 0.92), (134, 120, 104), 0.42, 18)]  # sol proche
for (cx, cy), col, rad, n in BLOBS:
    for _ in range(n):
        a, rr = random.uniform(0, 6.283), random.uniform(0, 1) ** 0.6 * rad * S
        bx, by = cx * S + rr * math.cos(a), cy * S + rr * math.sin(a)
        br = random.uniform(0.05, 0.13) * S
        c = tuple(max(0, min(255, v + random.randint(-16, 16))) for v in col)
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=c + (110,))

# variation basse frequence (evite les aplats)
lowf = Image.effect_noise((28, 28), 60).convert('L').resize((S, S), Image.BICUBIC)
lowf = lowf.filter(ImageFilter.GaussianBlur(S * 0.04))
base = Image.merge('RGB', [ImageChops.add(ch, lowf.point(lambda v: int(abs(v - 128) * 0.5)))
                           for ch in base.split()])

# flou de profondeur de champ : tres fort, plus dense vers le bas (avant-plan proche)
far = base.filter(ImageFilter.GaussianBlur(S * 0.045))
near = base.filter(ImageFilter.GaussianBlur(S * 0.075))
ramp = Image.linear_gradient('L').resize((S, S))          # 0 en haut -> 255 en bas
bg = Image.composite(near, far, ramp.point(lambda v: min(255, int(v * 1.4))))

# ---------- bokeh : disques lumineux hors-focus ----------
bok = Image.new('RGB', (S, S), (0, 0, 0))
bd = ImageDraw.Draw(bok, 'RGBA')
CLUSTERS = [(0.04, 0.14, 0.26), (0.95, 0.10, 0.30), (0.74, 0.40, 0.14)]
for _ in range(26):
    cx, cy, cr = random.choice(CLUSTERS)
    x = (cx + random.gauss(0, 0.55) * cr) * S
    y = max(0.01, cy + random.gauss(0, 0.55) * cr) * S
    r = random.uniform(0.018, 0.048) * S
    v = random.randint(16, 52)
    tint = random.choice([(1.0, 0.97, 0.86), (0.94, 0.99, 0.9), (1.0, 0.92, 0.78)])
    col = tuple(int(v * t) for t in tint)
    bd.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))
    # liseré legerement plus clair, comme un vrai disque de flou
    bd.ellipse([x - r, y - r, x + r, y + r], outline=tuple(int(c * 1.5) for c in col) + (255,),
               width=max(2, int(r * 0.10)))
bok = bok.filter(ImageFilter.GaussianBlur(S * 0.010))
bg = ImageChops.add(bg, bok)
bg = ImageEnhance.Color(bg).enhance(0.86)

# vignette + derive chromatique douce (comme un objectif ouvert)
vig = Image.new('L', (S, S), 0)
ImageDraw.Draw(vig).ellipse([-int(0.16 * S), -int(0.16 * S), int(1.16 * S), int(1.16 * S)], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(S * 0.11))
bg = Image.composite(bg, ImageEnhance.Brightness(bg).enhance(0.80), vig)

# ---------- sujet ----------
mask = Image.open(SCR + 'mask_birefnet-general.png').convert('L').resize((S, S), Image.LANCZOS)
mask = mask.filter(ImageFilter.MinFilter(5))
mask = mask.point(lambda v: 0 if v < 26 else min(255, int((v - 26) * 255 / 190)))
mask = mask.filter(ImageFilter.GaussianBlur(S * 0.0013))

subj = photo
r, g, b = subj.split()
subj = Image.merge('RGB', (r.point(lambda v: min(255, int(v * 1.035 + 3))),
                           g.point(lambda v: min(255, int(v * 1.01 + 1))),
                           b.point(lambda v: int(v * 0.97))))
subj = ImageEnhance.Contrast(subj).enhance(1.05)
subj = ImageEnhance.Color(subj).enhance(1.03)

out = bg.copy()
out.paste(subj, (0, 0), mask)

# lumiere du fond qui deborde sur les contours du sujet
edge = ImageChops.subtract(mask.filter(ImageFilter.GaussianBlur(S * 0.009)), mask)
warm = Image.new('RGB', (S, S), (255, 238, 208))
out = Image.composite(Image.blend(out, warm, 0.15), out, edge.point(lambda v: min(255, v * 2)))

# grain commun aux deux couches (unifie le montage)
grain = Image.effect_noise((S, S), 9).convert('L')
out = Image.merge('RGB', [ImageChops.add(ch, grain.point(lambda v: int(abs(v - 128) * 0.17)))
                          for ch in out.split()])
out = ImageEnhance.Contrast(out).enhance(1.02)
out.save(SCR + 'result_bokeh.jpg', quality=94, subsampling=0)
out.resize((760, 760), Image.LANCZOS).save(SCR + 'prev_bokeh.jpg', quality=90)
print('ok')
