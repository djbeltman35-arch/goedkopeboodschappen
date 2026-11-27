# Eigen, rechtenvrij deuntje: vrolijk, simpel (C-groot, 116 bpm), marimba + bas + shaker.
import numpy as np, wave, sys
SR = 44100
BPM = 116
BEAT = 60 / BPM
DUR = 17.0
n = int(SR * DUR)
out = np.zeros((n, 2))

def hz(m): return 440 * 2 ** ((m - 69) / 12)

def marimba(f, length, amp):
    t = np.arange(int(SR * length)) / SR
    env = np.exp(-t * 7) * np.minimum(1, t * 400)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 20) + 0.15 * np.sin(2 * np.pi * 2 * f * t)
    return amp * s * env

def bass(f, length, amp):
    t = np.arange(int(SR * length)) / SR
    env = np.exp(-t * 3) * np.minimum(1, t * 200)
    s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)
    return amp * s * env

def shaker(length, amp, rng):
    m = int(SR * length)
    t = np.arange(m) / SR
    noise = rng.standard_normal(m)
    noise = np.diff(np.concatenate([[0], noise]))  # hoog-doorlaat-achtig
    return amp * noise * np.exp(-t * 60)

def add(sig, start, pan=0.0):
    i = int(start * SR)
    if i >= n: return
    sig = sig[: n - i]
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    out[i:i + len(sig), 0] += sig * l
    out[i:i + len(sig), 1] += sig * r

rng = np.random.default_rng(7)
# akkoorden per maat (4 tellen): C G Am F
chords = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]
roots = [36, 43, 45, 41]
# melodie per maat in achtsten (None = rust)
mel = [
    [72, None, 76, 79, 76, None, 74, 72],
    [74, None, 71, 74, 79, None, 77, 74],
    [76, None, 72, 76, 81, None, 79, 76],
    [77, 76, 74, None, 72, None, 74, None],
]
bar = 4 * BEAT
nbars = int(DUR / bar) + 1
for b in range(nbars):
    t0 = b * bar
    c = chords[b % 4]
    # bas op tel 1 en 3
    add(bass(hz(roots[b % 4]), BEAT * 1.8, 0.35), t0)
    add(bass(hz(roots[b % 4] + 7), BEAT * 1.8, 0.25), t0 + 2 * BEAT)
    # akkoordtoetsjes op de 'en'-tellen (huppelend)
    for k in range(4):
        for j, m in enumerate(c):
            add(marimba(hz(m), 0.5, 0.07), t0 + k * BEAT + BEAT / 2, pan=-0.3 + 0.3 * j)
    # melodie (vanaf maat 1, na 1 maat intro alleen begeleiding)
    if b >= 1:
        for k, m in enumerate(mel[b % 4] if b % 8 < 4 else mel[(b + 2) % 4]):
            if m is not None:
                add(marimba(hz(m), 0.6, 0.22), t0 + k * BEAT / 2, pan=0.15)
    # shaker op elke zestiende, accent op achtsten
    for k in range(16):
        add(shaker(0.06, 0.05 if k % 2 == 0 else 0.025, rng), t0 + k * BEAT / 4, pan=0.4)
    # klapje op tel 2 en 4
    for k in (1, 3):
        add(shaker(0.12, 0.12, rng), t0 + k * BEAT, pan=-0.1)

# zachte limiter en normaliseren
out = np.tanh(out * 1.2)
out = out / np.max(np.abs(out)) * 0.7
data = (out * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('ok')
