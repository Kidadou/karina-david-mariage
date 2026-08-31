"""Compositing : sujet detoure + fond 'place de village' floute (bokeh)."""
import os, random
from PIL import Image, ImageFilter, ImageEnhance, ImageChops, ImageDraw

SCR = os.environ.get('WORKDIR', './work/')
SRC = os.environ.get('SRC', SCR + 'source.jpg')
random.seed(11)

photo = Image.open(SRC).convert('RGB')
S = photo.size[0]

# ---------- fond : flou de profondeur de champ + bokeh + grain ----------
bg = Image.open(os.environ.get('BGFILE', 'village_sharp.png')).convert('RGB').resize((int(S*1.18), int(S*1.18)), Image.LANCZOS)
bg = bg.crop((int(S*0.09), int(S*0.13), int(S*0.09)+S, int(S*0.13)+S))
bg = bg.filter(ImageFilter.GaussianBlur(S * 0.0125))

# points lumineux hors-focus (bokeh)
bok = Image.new('RGB', (S, S), (0, 0, 0))
bd = ImageDraw.Draw(bok)
for _ in range(22):
    x = random.randint(0, S)
    y = random.randint(0, int(0.55 * S))
    r = random.randint(int(0.012 * S), int(0.032 * S))
    v = random.randint(14, 38)
    bd.ellipse([x - r, y - r, x + r, y + r], fill=(v, int(v * 0.94), int(v * 0.8)))
bg = ImageChops.add(bg, bok.filter(ImageFilter.GaussianBlur(S * 0.006)))

# vignette douce
vig = Image.new('L', (S, S), 0)
ImageDraw.Draw(vig).ellipse([-int(0.18 * S), -int(0.18 * S), int(1.18 * S), int(1.18 * S)], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(S * 0.10))
bg = Image.composite(bg, ImageEnhance.Brightness(bg).enhance(0.82), vig)

# ---------- sujet ----------
mask = Image.open(SCR + 'mask_birefnet-general.png').convert('L').resize((S, S), Image.LANCZOS)
# leger retrait du bord (supprime le lisere clair de la vitre) puis adoucissement
mask = mask.filter(ImageFilter.MinFilter(5))
mask = mask.point(lambda v: 0 if v < 26 else min(255, int((v - 26) * 255 / 190)))
mask = mask.filter(ImageFilter.GaussianBlur(S * 0.0013))

subj = photo
# ambiance ensoleillee : legere chaleur + micro-contraste
r, g, b = subj.split()
subj = Image.merge('RGB', (r.point(lambda v: min(255, int(v * 1.045 + 3))),
                           g.point(lambda v: min(255, int(v * 1.012 + 1))),
                           b.point(lambda v: int(v * 0.965))))
subj = ImageEnhance.Contrast(subj).enhance(1.06)
subj = ImageEnhance.Color(subj).enhance(1.04)

out = bg.copy()
out.paste(subj, (0, 0), mask)

# ---------- unification : lumiere ambiante + grain commun ----------
# halo de lumiere venant du fond (spill light) sur les contours du sujet
edge = ImageChops.subtract(mask.filter(ImageFilter.GaussianBlur(S * 0.0125)), mask)
warm = Image.new('RGB', (S, S), (255, 236, 205))
out = Image.composite(Image.blend(out, warm, 0.16), out, edge.point(lambda v: min(255, v * 2)))

grain = Image.effect_noise((S, S), 9).convert('L')
out = Image.merge('RGB', [ImageChops.add(ch, grain.point(lambda v: int(abs(v - 128) * 0.16)))
                          for ch in out.split()])
out = ImageEnhance.Contrast(out).enhance(1.02)
out.save(SCR + 'result.jpg', quality=94, subsampling=0)
out.resize((760, 760), Image.LANCZOS).save(SCR + 'prev_result.jpg', quality=90)
print('ok', out.size)
