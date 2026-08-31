"""Rendu d'un fond 'place de village' ensoleillee, destine a etre fortement
floute (faible profondeur de champ) derriere un portrait."""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

S = 3340
random.seed(7)

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def jitter(c, amt=10):
    return tuple(max(0, min(255, v + random.randint(-amt, amt))) for v in c)

def render():
    img = Image.new('RGB', (S, S), (255, 255, 255))
    d = ImageDraw.Draw(img, 'RGBA')

    HOR = int(0.74 * S)          # ligne de sol
    # --- ciel : degrade bleu pale -> blanc chaud
    sky_top, sky_bot = (150, 190, 224), (240, 233, 216)
    for y in range(0, HOR):
        t = y / HOR
        d.line([(0, y), (S, y)], fill=lerp(sky_top, sky_bot, t ** 0.8))

    # nuages diffus
    for _ in range(26):
        cx = random.randint(0, S)
        cy = random.randint(0, int(0.30 * S))
        rw = random.randint(int(0.06 * S), int(0.20 * S))
        rh = int(rw * random.uniform(0.25, 0.45))
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(255, 253, 248, 120))

    # --- rangee de facades
    walls = [(226, 198, 158), (233, 214, 180), (214, 176, 132),
             (238, 224, 199), (206, 162, 118), (228, 206, 172),
             (219, 187, 145), (241, 231, 210)]
    roof = [(176, 96, 62), (163, 84, 55), (188, 110, 72)]
    shut = [(96, 124, 118), (78, 104, 128), (120, 132, 96), (110, 96, 84)]

    x = -int(0.06 * S)
    while x < S:
        w = random.randint(int(0.13 * S), int(0.24 * S))
        top = int(random.uniform(0.30, 0.46) * S)
        wall = jitter(random.choice(walls), 8)
        d.rectangle([x, top, x + w, HOR], fill=wall)
        # toit en tuiles
        rh = int(0.035 * S)
        rc = jitter(random.choice(roof), 10)
        d.polygon([(x - int(0.012 * S), top), (x + w + int(0.012 * S), top),
                   (x + w, top - rh), (x, top - rh)], fill=rc)
        # bandeau d'ombre sous le toit
        d.rectangle([x, top, x + w, top + int(0.012 * S)], fill=(120, 92, 66, 70))

        # fenetres + volets, 2 a 3 niveaux
        levels = 2 if (HOR - top) < 0.30 * S else 3
        cols = max(2, int(w / (0.075 * S)))
        for lv in range(levels):
            wy = top + int(0.055 * S) + lv * int((HOR - top - 0.09 * S) / max(1, levels))
            for c in range(cols):
                wx = x + int((c + 0.5) * w / cols) - int(0.018 * S)
                ww, wh = int(0.036 * S), int(0.055 * S)
                d.rectangle([wx, wy, wx + ww, wy + wh], fill=(64, 62, 66))
                sc = jitter(random.choice(shut), 12)
                sw = int(ww * 0.42)
                d.rectangle([wx - sw, wy, wx, wy + wh], fill=sc)
                d.rectangle([wx + ww, wy, wx + ww + sw, wy + wh], fill=sc)
                # rebord clair
                d.rectangle([wx - sw, wy + wh, wx + ww + sw, wy + wh + int(0.006 * S)],
                            fill=(246, 240, 228))
            # balcon en fer forge de temps en temps
            if lv == 1 and random.random() < 0.5:
                by = wy + int(0.062 * S)
                d.rectangle([x + int(0.02 * S), by, x + w - int(0.02 * S), by + int(0.012 * S)],
                            fill=(70, 68, 64, 200))

        # rez-de-chaussee : arcades ou devantures
        gy = HOR - int(0.12 * S)
        if random.random() < 0.45:
            n = max(2, int(w / (0.085 * S)))
            for c in range(n):
                ax = x + int((c + 0.5) * w / n)
                aw = int(0.030 * S)
                d.rounded_rectangle([ax - aw, gy, ax + aw, HOR], radius=aw,
                                    fill=(126, 100, 78))
        else:
            d.rectangle([x + int(0.02 * S), gy, x + w - int(0.02 * S), HOR],
                        fill=jitter((138, 112, 88), 14))
            # store / auvent
            d.rectangle([x + int(0.015 * S), gy - int(0.020 * S), x + w - int(0.015 * S), gy],
                        fill=jitter((188, 92, 78), 16))
        x += w

    # --- clocher a gauche
    tx, tw = int(0.05 * S), int(0.115 * S)
    ttop = int(0.13 * S)
    d.rectangle([tx, ttop, tx + tw, HOR], fill=(230, 218, 192))
    d.polygon([(tx - int(0.018 * S), ttop), (tx + tw + int(0.018 * S), ttop),
               (tx + tw // 2, ttop - int(0.075 * S))], fill=(150, 84, 58))
    d.ellipse([tx + tw // 4, ttop + int(0.045 * S), tx + 3 * tw // 4, ttop + int(0.045 * S) + tw // 2],
              fill=(248, 244, 232), outline=(150, 130, 100), width=6)  # horloge
    d.rounded_rectangle([tx + tw // 3, ttop + int(0.14 * S), tx + 2 * tw // 3, ttop + int(0.22 * S)],
                        radius=tw // 6, fill=(88, 72, 60))

    # --- sol : pierres claires chaudes en perspective
    ground_far, ground_near = (214, 196, 166), (186, 166, 138)
    for y in range(HOR, S):
        t = (y - HOR) / (S - HOR)
        d.line([(0, y), (S, y)], fill=lerp(ground_far, ground_near, t ** 0.7))
    for _ in range(900):
        gy = random.randint(HOR, S)
        t = (gy - HOR) / (S - HOR)
        pw = int((0.008 + 0.05 * t) * S)
        ph = max(3, int(pw * 0.45))
        gx = random.randint(-pw, S)
        d.ellipse([gx, gy, gx + pw, gy + ph],
                  fill=(255, 250, 240, 26) if random.random() < 0.5 else (110, 96, 84, 22))

    # --- terrasse de cafe (parasols) a droite, silhouettes de passants
    for px, py, pw in [(int(0.86 * S), int(0.60 * S), int(0.19 * S)),
                       (int(0.98 * S), int(0.63 * S), int(0.17 * S))]:
        d.polygon([(px - pw, py), (px + pw, py), (px, py - int(0.075 * S))],
                  fill=(243, 236, 220))
        d.rectangle([px - int(0.006 * S), py, px + int(0.006 * S), py + int(0.13 * S)],
                    fill=(196, 184, 166))
    for _ in range(7):
        fx = random.choice([random.randint(0, int(0.28 * S)), random.randint(int(0.78 * S), S)])
        fy = random.randint(HOR - int(0.02 * S), HOR + int(0.06 * S))
        fh = int(random.uniform(0.10, 0.15) * S)
        fw = int(fh * 0.30)
        col = jitter((92, 84, 84), 30)
        d.rounded_rectangle([fx, fy - fh, fx + fw, fy], radius=fw // 3, fill=col + (215,))
        d.ellipse([fx + fw // 5, fy - fh - fw // 2, fx + 4 * fw // 5, fy - fh + fw // 6],
                  fill=(120, 96, 80, 215))

    # --- feuillages (platanes) en haut, cadrent la scene
    for cx, cy, r, n in [(int(-0.02 * S), int(0.04 * S), int(0.15 * S), 30),
                         (int(1.02 * S), int(0.05 * S), int(0.22 * S), 46),
                         (int(0.78 * S), int(0.34 * S), int(0.09 * S), 18)]:
        for _ in range(n):
            a, rr = random.uniform(0, 6.283), random.uniform(0, 1) ** 0.5 * r
            bx, by = cx + rr * math.cos(a), cy + rr * math.sin(a)
            br = random.randint(int(0.02 * S), int(0.05 * S))
            g = jitter((88, 122, 74), 26)
            d.ellipse([bx - br, by - br, bx + br, by + br], fill=g + (225,))

    # --- lumiere du soleil (haut gauche) + vignette chaude
    glow = Image.new('RGB', (S, S), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(0.55 * S)
    for i in range(40):
        rr = gr * (1 - i / 40)
        v = int(96 * (i / 40) ** 1.8)
        gd.ellipse([int(0.18 * S) - rr, int(0.05 * S) - rr,
                    int(0.18 * S) + rr, int(0.05 * S) + rr], fill=(v, v * 92 // 100, v * 74 // 100))
    img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(S // 12)))

    # texture : crepi / pierre, pour casser les aplats avant le flou
    tex = Image.effect_noise((S // 4, S // 4), 26).convert('L').resize((S, S), Image.BICUBIC)
    tex = tex.filter(ImageFilter.GaussianBlur(2))
    img = Image.merge('RGB', [ImageChops.add(ch, tex.point(lambda v: int(abs(v - 128) * 0.30)))
                              for ch in img.split()])
    # ombre portee douce des toits vers le bas de la place
    shade = Image.new('L', (S, S), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(int(0.74 * S), S):
        t = (y - 0.74 * S) / (S - 0.74 * S)
        sd.line([(0, y), (S, y)], fill=int(70 * t))
    img = Image.composite(ImageEnhance.Brightness(img).enhance(0.86), img, shade)
    return img

if __name__ == '__main__':
    render().save('village_sharp.png')
    print('ok')
