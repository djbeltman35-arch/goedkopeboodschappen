#!/usr/bin/env python3
"""Geanimeerde reel (1080x1920, 30 fps) met aanbiedingen of prijzen.

Gebruik:
  python3 reel.py deals.json uit.mp4 [--deuntje audio/deuntje.m4a] [--merk boodschappen|bespaarvriend|stroomwekker]

Tip-reel: {"haak": {"boven": "...", "groot": "Korte haak", "onder": "..."}, "items": [{"punt": "..."}, ...],
            "slot": {"kop": "...", "site": "bespaarvriend.nl", "onder": "..."}}

deals.json:
  {"haak": optioneel, "items": [{"winkel": "Dirk", "product": "...", "prijs": 3.99, "was": 12.35}, ...],
   "slot": {"getal": 7117, "regel": "aanbiedingen van 10 supermarkten", "site": "boodschappenvergelijk.nl"}}
Of: python3 reel.py --uit-tekst vandaag.json aanbiedingen uit.mp4  (leest de social-tekst van boodschappenvergelijk.nl)

Alleen prijzen uit de data; niets wordt verzonnen.
"""
import json, math, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
HIER = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(HIER, "fonts", n)
KOP = F("barlow-condensed-latin-700-normal.ttf")
KOP6 = F("barlow-condensed-latin-600-normal.ttf")
TXT = F("atkinson-hyperlegible-latin-700-normal.ttf")
TXT4 = F("atkinson-hyperlegible-latin-400-normal.ttf")

MERKEN = {
    "boodschappen": dict(bg1=(14, 124, 74), bg2=(6, 58, 35), kaart=(244, 247, 241), ink=(20, 35, 27), geel=(255, 210, 63), naam="BOODSCHAPPENVERGELIJK.NL", site="boodschappenvergelijk.nl"),
    "bespaarvriend": dict(bg1=(14, 124, 74), bg2=(6, 58, 35), kaart=(244, 247, 241), ink=(20, 35, 27), geel=(255, 210, 63), naam="BESPAARVRIEND", site="bespaarvriend.nl"),
    "stroomwekker": dict(bg1=(25, 52, 92), bg2=(10, 22, 42), kaart=(244, 246, 250), ink=(15, 35, 64), geel=(255, 210, 63), naam="STROOMWEKKER", site="stroomwekker.eu"),
}
_fc = {}
def font(p, s):
    k = (p, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(p, max(8, int(s)))
    return _fc[k]

def eur(x): return "€ " + f"{x:.2f}".replace(".", ",")
def clamp(x): return max(0.0, min(1.0, x))
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def ease_out(x): return 1 - (1 - x) ** 3
def ease_back(x, s=1.9): x -= 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_in(x): return x ** 3

def wrap(d, tekst, pad, maxb, start, minmaat=40, maxregels=3):
    """Zo groot mogelijk lettertype waarbij de tekst in maxregels past."""
    maat = start
    while maat >= minmaat:
        f = font(pad, maat); regels, cur = [], ""
        for w in tekst.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= maxb: cur = t
            else:
                if cur: regels.append(cur)
                cur = w
        if cur: regels.append(cur)
        if len(regels) <= maxregels and all(d.textlength(r, font=f) <= maxb for r in regels): return f, regels
        maat -= 4
    f = font(pad, minmaat); return f, regels[:maxregels]

def tekst_c(d, xy, t, f, fill, anchor="mm", stroke=0, sfill=None):
    d.text(xy, t, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sfill)

def pop_laag(img, laag, cx, cy, schaal, hoek=0.0, alpha=1.0):
    """Plak een RGBA-laag geschaald/gedraaid rond (cx, cy)."""
    if schaal <= 0.01 or alpha <= 0.01: return
    l = laag
    if abs(schaal - 1) > 0.005: l = l.resize((max(1, int(l.width * schaal)), max(1, int(l.height * schaal))), Image.BICUBIC)
    if abs(hoek) > 0.1: l = l.rotate(hoek, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = l.getchannel("A").point(lambda v: int(v * alpha)); l = l.copy(); l.putalpha(a)
    img.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))

def tekstlaag(t, f, fill, stroke=0, sfill=None, pad=20):
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    x0, y0, x1, y1 = d0.textbbox((0, 0), t, font=f, stroke_width=stroke)
    l = Image.new("RGBA", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(l).text((pad - x0, pad - y0), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return l

class Reel:
    def __init__(s, data, merk):
        s.m = MERKEN[merk]; s.items = data["items"]; s.sl = data.get("slot") or {}; s.data = data
        s.punten = all("punt" in i for i in s.items)
        s.met_was = (not s.punten) and any(i.get("was") for i in s.items)
        for i in s.items:
            if s.punten: i["pct"] = 0; continue
            i["pct"] = round((1 - i["prijs"] / i["was"]) * 100) if i.get("was") and i["was"] > i["prijs"] else 0
        if s.met_was: s.items.sort(key=lambda i: i["pct"])  # beste deal als laatste: spanning tot het eind
        s.T_HAAK, s.T_ITEM, s.T_SLOT = 2.3, (3.4 if s.punten else 2.3), 3.4
        s.duur = s.T_HAAK + len(s.items) * s.T_ITEM + s.T_SLOT
        # achtergrond met diagonale strepen, groter dan het beeld zodat hij kan schuiven
        g = Image.new("RGB", (W, H + 240)); gd = ImageDraw.Draw(g)
        for y in range(H + 240):
            k = y / (H + 240); c = tuple(int(s.m["bg1"][j] * (1 - k) + s.m["bg2"][j] * k) for j in range(3)); gd.line([(0, y), (W, y)], fill=c)
        st = Image.new("RGBA", g.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        for x in range(-H, W + H, 120): sd.polygon([(x, 0), (x + 48, 0), (x + 48 + H + 240, H + 240), (x + H + 240, H + 240)], fill=(255, 255, 255, 10))
        s.bg = Image.alpha_composite(g.convert("RGBA"), st)

    def achtergrond(s, t):
        off = int((t * 40) % 120)
        return s.bg.crop((0, off, W, off + H)).copy()

    def kopbalk(s, img, d, t):
        tekst_c(d, (W / 2, 120), s.m["naam"], font(KOP6, 46), (255, 255, 255, 220))

    # ---------- haak ----------
    def haak(s, img, d, t):
        h = s.data.get("haak") or {}
        if s.punten:
            a = ease_back(seg(t, 0.0, 0.5)); c = ease_out(seg(t, 0.45, 0.9)); uit = ease_in(seg(t, s.T_HAAK - 0.25, s.T_HAAK)); al = 1 - uit
            if h.get("boven"): pop_laag(img, tekstlaag(h["boven"], font(KOP, 110), s.m["kaart"]), W / 2, 620, a, alpha=al)
            f, regels = wrap(d, h.get("groot", ""), KOP, 960, 210, 110, 3)
            y0 = 900 - (len(regels) - 1) * f.size * 0.55
            for j, r in enumerate(regels): pop_laag(img, tekstlaag(r, f, s.m["geel"], stroke=8, sfill=s.m["bg2"]), W / 2, y0 + j * f.size * 1.1, a * (1 + uit * 0.5), hoek=-3 * a, alpha=al)
            if h.get("onder") and c > 0:
                f2, r2 = wrap(d, h["onder"], TXT, 900, 60, 44, 2)
                for j, r in enumerate(r2): pop_laag(img, tekstlaag(r, f2, (255, 255, 255)), W / 2, 1240 + j * f2.size * 1.25 + 30 * (1 - c), 1, alpha=c * al)
            return
        if s.met_was:
            best = max(s.items, key=lambda i: i["pct"])
            boven, groot, onder = h.get("boven", "TOT"), h.get("groot", f"{best['pct']}%"), h.get("onder", "KORTING")
            sub = h.get("sub", f"{len(s.items)} deals van vandaag")
        else:
            goed = min(s.items, key=lambda i: i["prijs"])
            boven, groot, onder = h.get("boven", goed["product"].split()[0].upper() if len(goed["product"]) < 22 else "NU"), h.get("groot", eur(goed["prijs"])), h.get("onder", f"BIJ {goed['winkel'].upper()}")
            sub = h.get("sub", "Check eerst waar het goedkoopst is")
        a = ease_back(seg(t, 0.0, 0.45)); b = ease_back(seg(t, 0.15, 0.6)); c = ease_out(seg(t, 0.55, 1.0))
        uit = ease_in(seg(t, s.T_HAAK - 0.25, s.T_HAAK)); sch = 1 + uit * 0.6; al = 1 - uit
        schud = math.sin(t * 40) * 6 * (1 - seg(t, 0.45, 0.9))
        pop_laag(img, tekstlaag(boven, font(KOP, 120), s.m["kaart"]), W / 2, 640, a * sch, alpha=al)
        fg = font(KOP, 400 if len(groot) <= 4 else 300 if len(groot) <= 6 else 230)
        pop_laag(img, tekstlaag(groot, fg, s.m["geel"], stroke=10, sfill=s.m["bg2"]), W / 2 + schud, 900, b * sch, hoek=-4 * b, alpha=al)
        pop_laag(img, tekstlaag(onder, font(KOP, 140), s.m["kaart"]), W / 2, 1170, a * sch, alpha=al)
        if c > 0: pop_laag(img, tekstlaag(sub, font(TXT, 56), (255, 255, 255)), W / 2, 1330 + 30 * (1 - c), 1.0, alpha=c * al)

    # ---------- één deal ----------
    def punt(s, img, d, t, i, it):
        m = s.m; n = len(s.items)
        inn = ease_back(seg(t, 0, 0.4)); uit = ease_in(seg(t, s.T_ITEM - 0.24, s.T_ITEM)); dx = -uit * W * 0.9
        bw = 760; x0 = (W - bw) / 2
        d.rounded_rectangle([x0, 300, x0 + bw, 314], 7, fill=(255, 255, 255, 60))
        d.rounded_rectangle([x0, 300, x0 + bw * (i + seg(t, 0, s.T_ITEM)) / n, 314], 7, fill=m["geel"])
        kaart = Image.new("RGBA", (920, 980), (0, 0, 0, 0)); kd = ImageDraw.Draw(kaart)
        kd.rounded_rectangle([12, 22, 920, 980], 56, fill=(0, 0, 0, 70)); kd.rounded_rectangle([0, 0, 900, 960], 56, fill=m["kaart"])
        kd.ellipse([60, 60, 220, 220], fill=m["geel"], outline=m["ink"], width=6); kd.text((140, 140), str(i + 1), font=font(KOP, 120), fill=m["ink"], anchor="mm")
        fp, regels = wrap(kd, it["punt"], TXT, 780, 92, 50, 6)
        y = 290
        for r in regels: kd.text((60, y), r, font=fp, fill=m["ink"]); y += fp.size * 1.22
        pop_laag(img, kaart, W / 2 + dx, 400 + 490, 0.85 + 0.15 * inn, alpha=clamp(inn * 1.5))

    def deal(s, img, d, t, i, it):
        m = s.m; n = len(s.items)
        inn = ease_out(seg(t, 0, 0.32)); uit = ease_in(seg(t, s.T_ITEM - 0.24, s.T_ITEM))
        dx = (1 - inn) * W * 0.9 - uit * W * 0.9
        # voortgang
        tekst_c(d, (W / 2, 250), f"DEAL {i + 1} VAN {n}" if s.met_was else f"{i + 1} / {n}", font(KOP6, 52), m["geel"])
        bw = 760; x0 = (W - bw) / 2
        d.rounded_rectangle([x0, 300, x0 + bw, 314], 7, fill=(255, 255, 255, 60))
        d.rounded_rectangle([x0, 300, x0 + bw * (i + seg(t, 0, s.T_ITEM)) / n, 314], 7, fill=m["geel"])
        # kaart
        kaart = Image.new("RGBA", (920, 1080), (0, 0, 0, 0)); kd = ImageDraw.Draw(kaart)
        kd.rounded_rectangle([12, 22, 920, 1080], 56, fill=(0, 0, 0, 70))
        kd.rounded_rectangle([0, 0, 900, 1060], 56, fill=m["kaart"])
        fw = font(KOP, 68); wb = kd.textlength(it["winkel"].upper(), font=fw) + 80
        kd.rounded_rectangle([60, 60, 60 + wb, 160], 50, fill=m["bg1"])
        kd.text((60 + wb / 2, 110), it["winkel"].upper(), font=fw, fill=(255, 255, 255), anchor="mm")
        fp, regels = wrap(kd, it["product"], TXT, 780, 84, 46, 3)
        y = 230
        for r in regels: kd.text((60, y), r, font=fp, fill=m["ink"]); y += fp.size * 1.18
        img.alpha_composite(kaart, (int(80 + dx), 400))
        ky = 400
        # oude prijs met doorhaalstreep die zich tekent
        if it.get("was"):
            fwas = font(KOP6, 110); wt = eur(it["was"]); wx, wy = 140 + dx, ky + 640
            d.text((wx, wy), wt, font=fwas, fill=(120, 130, 125), anchor="lm")
            L = d.textlength(wt, font=fwas); k = ease_out(seg(t, 0.35, 0.65))
            if k > 0: d.line([(wx - 10, wy + 4), (wx - 10 + (L + 20) * k, wy - 6)], fill=(214, 40, 40), width=12)
        # nieuwe prijs ploft erin
        p = ease_back(seg(t, 0.55, 0.95))
        if p > 0:
            pl = tekstlaag(eur(it["prijs"]), font(KOP, 250), m["ink"])
            pop_laag(img, pl, 80 + dx + 60 + pl.width / 2 - 20, ky + 860, p)
        # kortingsbadge
        if it.get("pct"):
            b = ease_back(seg(t, 0.75, 1.1), 2.4)
            if b > 0:
                bl = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
                bd.ellipse([10, 10, 290, 290], fill=m["geel"], outline=m["ink"], width=8)
                bd.text((150, 150), f"-{it['pct']}%", font=font(KOP, 112), fill=m["ink"], anchor="mm")
                pop_laag(img, bl, 820 + dx, ky + 600, b, hoek=12 - 24 * b + 12)

    # ---------- slot ----------
    def slot(s, img, d, t):
        m = s.m; sl = s.sl
        a = ease_out(seg(t, 0, 0.35))
        getal = sl.get("getal")
        if getal:
            k = ease_out(seg(t, 0.1, 1.2)); g = int(getal * k)
            pop_laag(img, tekstlaag(f"{g:,}".replace(",", "."), font(KOP, 300), m["geel"], stroke=8, sfill=m["bg2"]), W / 2, 640, 0.6 + 0.4 * a)
            if sl.get("regel"):
                f, regels = wrap(d, sl["regel"], TXT, 900, 64, 44, 2)
                for j, r in enumerate(regels): pop_laag(img, tekstlaag(r, f, (255, 255, 255)), W / 2, 830 + j * f.size * 1.2, 1, alpha=a)
        else:
            f, regels = wrap(d, sl.get("kop", "Bekijk ze allemaal"), KOP, 940, 150, 80, 3)
            for j, r in enumerate(regels): pop_laag(img, tekstlaag(r, f, m["geel"]), W / 2, 700 - (len(regels) - 1) * f.size * 0.55 + j * f.size * 1.1, 0.6 + 0.4 * a)
        b = ease_back(seg(t, 0.8, 1.25))
        if b > 0:
            site = sl.get("site", m["site"]); fs = font(KOP, 96); L = d.textlength(site, font=fs) + 110
            pil = Image.new("RGBA", (int(L) + 20, 190), (0, 0, 0, 0)); pd = ImageDraw.Draw(pil)
            pd.rounded_rectangle([0, 0, L, 170], 85, fill=m["geel"]); pd.text((L / 2, 85), site, font=fs, fill=m["ink"], anchor="mm")
            puls = 1 + 0.03 * math.sin(max(0, t - 1.3) * 7)
            pop_laag(img, pil, W / 2, 1120, b * puls)
        c = ease_out(seg(t, 1.2, 1.6))
        if c > 0:
            pop_laag(img, tekstlaag(sl.get("onder", "Gratis · zonder reclame"), font(TXT, 58), (255, 255, 255)), W / 2, 1300, 1, alpha=c)
            pop_laag(img, tekstlaag("link in bio", font(TXT4, 50), (255, 255, 255)), W / 2, 1390, 1, alpha=c * 0.85)

    def frame(s, t):
        img = s.achtergrond(t); d = ImageDraw.Draw(img); s.kopbalk(img, d, t)
        if t < s.T_HAAK: s.haak(img, d, t)
        else:
            u = t - s.T_HAAK; i = int(u // s.T_ITEM)
            if i < len(s.items): (s.punt if s.punten else s.deal)(img, d, u - i * s.T_ITEM, i, s.items[i])
            else: s.slot(img, d, u - len(s.items) * s.T_ITEM)
        return img.convert("RGB")

    def render(s, uit, deuntje=None):
        tmp = uit + ".stil.mp4"
        p = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
        for k in range(int(s.duur * FPS)): p.stdin.write(s.frame(k / FPS).tobytes())
        p.stdin.close(); p.wait()
        if deuntje and os.path.exists(deuntje):
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", tmp, "-i", deuntje, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                            "-af", f"afade=t=in:d=0.2,afade=t=out:st={s.duur - 1.2:.2f}:d=1.2,volume=-2dB", "-c:a", "aac", "-b:a", "128k", "-t", f"{s.duur:.2f}", "-movflags", "+faststart", uit], check=True)
            os.remove(tmp)
        else: os.replace(tmp, uit)

def uit_tekst(post):
    """Leest de deals uit de social-tekst van boodschappenvergelijk.nl (data/social/vandaag.json)."""
    items = []
    for r in post["tekst"].splitlines():
        m = re.match(r"\s*\S+\s+([^:]+):\s+(.+?)\s+(?:voor\s+)?€\s*([\d.,]+)(?:\s+\(was\s+€\s*([\d.,]+)\))?\s*$", r)
        if m:
            num = lambda x: float(x.replace(".", "").replace(",", ".")) if x else None
            items.append({"winkel": m.group(1).strip(), "product": m.group(2).strip(), "prijs": num(m.group(3)), "was": num(m.group(4))})
    m = re.search(r"alle (\d+) aanbiedingen van (\d+) supermarkten", post["tekst"])
    slot = {"getal": int(m.group(1)), "regel": f"aanbiedingen van {m.group(2)} supermarkten, vergeleken"} if m else {"kop": "Waar is jouw lijst het goedkoopst?"}
    if not m: slot["onder"] = "Gratis · zonder reclame"
    return {"items": items, "slot": slot}

if __name__ == "__main__":
    a = sys.argv[1:]; deun = None; merk = "boodschappen"
    if "--deuntje" in a: i = a.index("--deuntje"); deun = a[i + 1]; del a[i:i + 2]
    if "--merk" in a: i = a.index("--merk"); merk = a[i + 1]; del a[i:i + 2]
    if a[0] == "--uit-tekst":
        post = next(p for p in json.load(open(a[1]))["posts"] if p["soort"] == a[2]); data = uit_tekst(post); uit = a[3]
    else: data = json.load(open(a[0])); uit = a[1]
    if not data["items"]: sys.exit("geen items gevonden")
    r = Reel(data, merk); r.render(uit, deun); print(uit, f"{r.duur:.1f}s", len(data["items"]), "items")
