"""Trilha de fundo ORIGINAL (gerada aqui, sem música de terceiros = sem reivindicação de direitos autorais):
pad suave de acordes + notas de "piano" espaçadas, bem tranquila, estilo música de oração."""
import random, wave
from pathlib import Path
import numpy as np

SR = 44100
# progressões calmas (graus em semitons a partir da tônica)
PROGRESSOES = [[[0, 4, 7, 11], [9, 12, 16, 19], [5, 9, 12, 16], [7, 11, 14, 17]],      # Imaj7 vi IV V
               [[0, 4, 7, 14], [5, 9, 12, 16], [9, 12, 16, 19], [5, 9, 12, 17]],
               [[0, 7, 12, 16], [5, 12, 17, 21], [7, 14, 19, 23], [0, 7, 12, 16]]]


def freq(semi, base):
    return base * 2 ** (semi / 12)


def gerar(saida, segundos, semente=None, tonica=None):
    rnd = random.Random(semente); saida = Path(saida)
    base = tonica or rnd.choice([130.81, 146.83, 164.81, 174.61])  # C3, D3, E3, F3
    prog = rnd.choice(PROGRESSOES); acorde_s = rnd.choice([6.0, 7.0, 8.0])
    n = int(segundos * SR); t = np.arange(n) / SR; som = np.zeros(n)
    k = 0; ini = 0.0
    while ini < segundos:
        notas = prog[k % len(prog)]; a, b = int(ini * SR), int(min(segundos, ini + acorde_s + 2) * SR)
        tt = t[a:b] - ini; env = np.minimum(1, tt / 2.5) * np.minimum(1, np.maximum(0, (acorde_s + 2 - tt)) / 2.5)
        for s in notas:
            f = freq(s, base)
            for det in (-0.6, 0.6):   # leve "chorus"
                som[a:b] += 0.05 * env * np.sin(2 * np.pi * (f + det) * tt)
            som[a:b] += 0.02 * env * np.sin(2 * np.pi * f * 2 * tt)
        # notas de piano espaçadas
        for _ in range(rnd.choice([1, 2, 2, 3])):
            st = ini + rnd.uniform(0.5, acorde_s - 0.5)
            if st >= segundos:
                continue
            f = freq(rnd.choice(notas) + 12, base); pa = int(st * SR); pb = min(n, pa + int(4 * SR))
            tp = t[pa:pb] - st
            som[pa:pb] += 0.07 * np.exp(-tp * 1.3) * (np.sin(2 * np.pi * f * tp) + 0.3 * np.sin(2 * np.pi * 2 * f * tp))
        ini += acorde_s; k += 1
    # "reverb" simples com ecos decrescentes
    for atraso, g in ((0.11, 0.35), (0.23, 0.25), (0.37, 0.18), (0.53, 0.12)):
        d = int(atraso * SR); som[d:] += g * som[:-d]
    fade = int(3 * SR); som[:fade] *= np.linspace(0, 1, fade); som[-fade:] *= np.linspace(1, 0, fade)
    som = som / (np.max(np.abs(som)) + 1e-9) * 0.6
    est = np.stack([som, np.roll(som, int(0.012 * SR))], 1)
    with wave.open(str(saida), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((est * 32767).astype(np.int16).tobytes())
    return saida


if __name__ == "__main__":
    gerar("/tmp/trilha_teste.wav", 70, semente=1)
