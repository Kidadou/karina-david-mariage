"""Variante : sujet detoure sur le fond aquarelle du site (patio andalou)."""
import os
from PIL import Image, ImageFilter, ImageEnhance, ImageChops

SCR = os.environ.get('WORKDIR', './work/')
SRC = os.environ.get('SRC', SCR + 'source.jpg')
BG = os.environ.get('BG', '../../images/hero-bg.jpg')

photo = Image.open(SRC).convert('RGB')
S = photo.size[0]

# fond aquarelle : recadre en carre sur la partie basse (patio + fontaine), zoom
bg = Image.open(BG).convert('RGB')
w, h = bg.size
side = w
bg = bg.crop((0, h - side - int(h * 0.02), w, h - int(h * 0.02))).resize((S, S), Image.LANCZOS)
bg = bg.resize((int(S * 1.25), int(S * 1.25)), Image.LANCZOS)
bg = bg.crop((int(S * 0.125), int(S * 0.16), int(S * 0.125) + S, int(S * 0.16) + S))
bg = bg.filter(ImageFilter.GaussianBlur(S * 0.004))
bg = ImageEnhance.Color(bg).enhance(1.15)
bg = ImageEnhance.Brightness(bg).enhance(0.98)

mask = Image.open(SCR + 'mask_birefnet-general.png').convert('L').resize((S, S), Image.LANCZOS)
mask = mask.filter(ImageFilter.MinFilter(5))
mask = mask.point(lambda v: 0 if v < 26 else min(255, int((v - 26) * 255 / 190)))
mask = mask.filter(ImageFilter.GaussianBlur(S * 0.0013))

# sujet legerement eclairci et desature pour s'accorder a l'aquarelle
subj = ImageEnhance.Color(photo).enhance(0.92)
subj = ImageEnhance.Brightness(subj).enhance(1.05)
r, g, b = subj.split()
subj = Image.merge('RGB', (r.point(lambda v: min(255, int(v * 1.03 + 4))), g,
                           b.point(lambda v: int(v * 0.98))))

out = bg.copy()
out.paste(subj, (0, 0), mask)

# lisere lumineux (le sujet baigne dans la lumiere claire du fond)
edge = ImageChops.subtract(mask.filter(ImageFilter.GaussianBlur(S * 0.012)), mask)
warm = Image.new('RGB', (S, S), (255, 250, 238))
out = Image.composite(Image.blend(out, warm, 0.22), out, edge.point(lambda v: min(255, v * 2)))

# grain papier commun aux deux couches
grain = Image.effect_noise((S, S), 8).convert('L')
out = Image.merge('RGB', [ImageChops.add(ch, grain.point(lambda v: int(abs(v - 128) * 0.14)))
                          for ch in out.split()])
out.save(SCR + 'result_aquarelle.jpg', quality=94, subsampling=0)
out.resize((760, 760), Image.LANCZOS).save(SCR + 'prev_aquarelle.jpg', quality=90)
print('ok')
