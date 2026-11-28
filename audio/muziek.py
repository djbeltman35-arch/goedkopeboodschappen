# Eigen, rechtenvrij deuntje (versie 5, 28 nov 2026): modern pop/house, 122 bpm, 17 s.
# Pompende supersaw-akkoorden (sidechain), subbas, four-on-the-floor, klap met galm,
# 'vocal chop'-melodie (formantfilter) en een korte opbouw naar de drop. Geen pingelige toetsjes.
import numpy as np, wave, sys
from scipy.signal import butter, lfilter, fftconvolve

SR = 44100
BPM = 122
BEAT = 60 / BPM
BAR = 4 * BEAT
DUR = 17.0
n = int(SR * DUR)
rng = np.random.default_rng(5)

def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, fc, o=2): b, a = butter(o, min(fc, SR / 2 - 100) / (SR / 2)); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)

def supersaw(f, t, voices=7, spread=0.012):
    s = np.zeros_like(t)
    for v in range(voices):
        d = (v - (voices - 1) / 2) / ((voices - 1) / 2) * spread
        ph = (f * (1 + d) * t + rng.random()) % 1.0
        s += 2 * ph - 1
    return s / voices

def reverb(x, secs=1.2, mix=0.25):
    m = int(SR * secs); t = np.arange(m) / SR
    ir = rng.standard_normal(m) * np.exp(-t * 4.5)
    ir = lp(ir, 5000); ir /= np.sqrt(np.sum(ir ** 2))
    wet = fftconvolve(x, ir)[: len(x)]
    return x * (1 - mix) + wet * mix

# lagen (mono), later gemixt
L = {k: np.zeros(n) for k in ('kick', 'clap', 'hat', 'sub', 'chord', 'chop', 'fx')}
def put(layer, sig, start):
    i = int(start * SR)
    if i >= n or i < 0: return
    sig = sig[: n - i]; L[layer][i:i + len(sig)] += sig

def kick():
    t = np.arange(int(SR * 0.45)) / SR
    f = 45 + 120 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) + 0.25 * np.exp(-t * 500)
def clap():
    m = int(SR * 0.25); t = np.arange(m) / SR
    nz = bp(rng.standard_normal(m), 900, 6000)
    env = sum(np.exp(-np.maximum(0, t - d) * 60) * (t >= d) for d in (0, 0.008, 0.017)) / 3 + 0.7 * np.exp(-t * 18)
    return nz * env
def hat(open_=False):
    m = int(SR * (0.16 if open_ else 0.04)); t = np.arange(m) / SR
    return hp(rng.standard_normal(m), 7000) * np.exp(-t * (18 if open_ else 90))

# Am F C G (vi-IV-I-V), het moderne popschema
prog = [(57, (57, 60, 64, 69)), (53, (57, 60, 65, 69)), (48, (55, 60, 64, 67)), (55, (55, 59, 62, 67))]
nbars = int(np.ceil(DUR / BAR))
t_all = np.arange(n) / SR

# akkoorden: doorlopende supersaw per maat
for b in range(nbars):
    root, ch = prog[b % 4]
    m = int(SR * BAR); t = np.arange(m) / SR
    s = sum(supersaw(hz(x), t) for x in ch) / len(ch)
    s += 0.5 * supersaw(hz(ch[0] - 12), t, 5, 0.008)
    put('chord', s * np.minimum(1, t / 0.02), b * BAR)
    # subbas: grondtoon, sinus met een vleugje boventoon
    sb = np.sin(2 * np.pi * hz(root - 24) * t) + 0.15 * np.sin(2 * np.pi * hz(root - 12) * t)
    put('sub', sb * np.minimum(1, t / 0.01) * np.minimum(1, (BAR - t) / 0.02), b * BAR)

# drums: maat 0 = opbouw (alleen klap-roll), vanaf maat 1 de drop
for b in range(1, nbars):
    for k in range(4):
        put('kick', kick(), b * BAR + k * BEAT)
        put('hat', hat(True), b * BAR + k * BEAT + BEAT / 2)
        put('hat', 0.5 * hat(), b * BAR + k * BEAT + BEAT * 0.75)
    for k in (1, 3):
        put('clap', clap(), b * BAR + k * BEAT)
# opbouw: klap-roll die versnelt + ruis-riser
for i, pos in enumerate(np.concatenate([np.arange(0, 2, 0.5), np.arange(2, 3, 0.25), np.arange(3, 4, 0.125)])):
    put('clap', clap() * (0.25 + 0.55 * pos / 4), pos * BEAT)
m = int(SR * BAR); t = np.arange(m) / SR
riser = rng.standard_normal(m); out_r = np.zeros(m)
for j in range(16):  # filter opent langzaam
    a, e = j * m // 16, (j + 1) * m // 16
    out_r[a:e] = bp(riser, 400 + 6000 * (j / 16) ** 2, 800 + 9000 * (j / 16) ** 2)[a:e]
put('fx', out_r * (t / BAR) ** 2 * 0.5, 0)

# 'vocal chop': korte formant-noten met kleine toonglijder
def chop(f, length, vowel):
    t = np.arange(int(SR * length)) / SR
    glide = f * (1 + 0.03 * np.exp(-t * 40))
    ph = np.cumsum(glide) / SR
    src = 2 * (ph % 1) - 1
    F = {'a': (800, 1200, 2500), 'o': (500, 900, 2400), 'e': (550, 1800, 2600)}[vowel]
    s = sum(bp(src, f0 * 0.85, f0 * 1.15) * g for f0, g in zip(F, (1, 0.6, 0.25)))
    env = np.minimum(1, t * 120) * np.minimum(1, (length - t) * 60)
    return s * env
mel = [  # (tel in maat, midi, lengte in tellen, klinker)
    [(0, 76, 0.5, 'a'), (0.75, 76, 0.25, 'o'), (1.5, 72, 0.5, 'a'), (2.5, 74, 0.5, 'e'), (3.25, 76, 0.5, 'a')],
    [(0, 77, 0.5, 'o'), (0.75, 76, 0.25, 'a'), (1.5, 72, 1.0, 'a'), (3, 69, 0.5, 'e')],
    [(0, 79, 0.5, 'a'), (0.75, 79, 0.25, 'o'), (1.5, 76, 0.5, 'a'), (2.5, 74, 0.5, 'e'), (3.25, 72, 0.5, 'a')],
    [(0, 74, 0.75, 'o'), (1, 71, 0.5, 'e'), (2, 74, 0.5, 'a'), (2.75, 79, 1.0, 'a')],
]
for b in range(1, nbars):
    for pos, mm, ln, v in mel[(b - 1) % 4]:
        put('chop', chop(hz(mm), ln * BEAT * 0.95, v), b * BAR + pos * BEAT)

# --- mix ---
# sidechain-pomp op elke tel vanaf de drop (het typische moderne 'ademende' geluid)
ph = (t_all % BEAT) / BEAT
pump = np.where(t_all >= BAR, 0.15 + 0.85 * np.minimum(1, ph / 0.55) ** 1.5, 1.0)
# akkoorden: in de opbouw dicht gefilterd, daarna open
chord_closed = lp(L['chord'], 700); chord_open = lp(L['chord'], 4200)
xf = np.clip((t_all - BAR + 0.05) / 0.05, 0, 1)
chords = (2.2 * chord_closed * (1 - xf) + chord_open * xf) * pump
chords = reverb(chords, 1.0, 0.2)
sub = L['sub'] * pump * (t_all >= BAR)
chopv = reverb(L['chop'], 1.4, 0.3)
clapv = reverb(L['clap'], 0.9, 0.2)
mono = 0.9 * L['kick'] + 0.5 * clapv * np.where(t_all < BAR, 1.6, 1.0) + 0.07 * L['hat'] + 0.55 * sub + 0.28 * chords + 0.5 * chopv + 0.25 * L['fx']
# stereo: akkoorden en hats iets breder
side = 0.12 * reverb(L['chord'] * pump, 0.6, 1.0) * (t_all >= BAR) + 0.03 * L['hat']
out = np.stack([mono + side, mono - side], axis=1)
out = out / np.max(np.abs(out))
out = np.tanh(out * 2.0)
out = out / np.max(np.abs(out)) * 0.92
data = (out * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('ok')
