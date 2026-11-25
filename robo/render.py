"""Monta o Short de oração 1080x1920: pinturas clássicas/paisagens com zoom lento e transições suaves, luz quente,
referência do versículo no topo, legendas frase a frase (fonte serifada Lora), voz do narrador + trilha suave."""
import random, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from comum import FONTES, dur, run

W, H, FPS = 1080, 1920, 30


def t(s):
    s = max(0, s); return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def ass_txt(x):
    return x.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def frases(texto):
    partes = re.split(r"(?<=[.!?…])\s+|\.\.\.\s*", texto.strip())
    out = []
    for p in partes:
        p = p.strip(" .")
        if not p:
            continue
        while len(p) > 60:   # quebra frases longas em pedaços de leitura confortável
            corte = p.rfind(",", 0, 60)
            corte = corte if corte > 25 else p.rfind(" ", 0, 52)
            out.append(p[:corte].strip(" ,")); p = p[corte + 1:].strip()
        out.append(p)
    return out


def legenda_ass(r, dur_voz, total, saida):
    fs = frases(r["texto"]); pesos = [len(f) + 8 for f in fs]; soma = sum(pesos); t0 = 0.4
    L = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
         "[V4+ Styles]",
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
         "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
         "Style: Leg,Lora,80,&H00FFFFFF,&H00FFFFFF,&H00302010,&H96000000,1,0,0,0,100,100,0,0,1,3,4,5,90,90,0,1",
         "Style: Ref,Lora,54,&H0080D8FF,&H0080D8FF,&H00201000,&H96000000,0,1,0,0,100,100,1,0,1,2,3,8,80,80,170,1",
         "Style: Fra,Lora,66,&H00FFFFFF,&H00FFFFFF,&H00201000,&H96000000,1,1,0,0,100,100,0,0,1,3,3,8,90,90,240,1",
         "Style: Fim,Lora,74,&H0080D8FF,&H0080D8FF,&H00201000,&H96000000,1,0,0,0,100,100,0,0,1,3,4,5,90,90,0,1", "",
         "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    L.append(f"Dialogue: 1,{t(0.3)},{t(total)},Ref,,0,0,0,,{{\\fad(800,600)}}{ass_txt(r.get('versiculo_ref', ''))}")
    L.append(f"Dialogue: 1,{t(0.3)},{t(min(9, total))},Fra,,0,0,0,,{{\\fad(800,800)}}{ass_txt(r.get('frase_tela', ''))}")
    for f, p in zip(fs, pesos):
        d = dur_voz * p / soma
        L.append(f"Dialogue: 2,{t(t0)},{t(t0 + d - 0.05)},Leg,,0,0,0,,{{\\pos(540,1240)\\fad(250,200)}}{ass_txt(f)}")
        t0 += d
    L.append(f"Dialogue: 2,{t(dur_voz + 0.3)},{t(total)},Fim,,0,0,0,,{{\\pos(540,1240)\\fad(400,500)}}"
             f"Escreva nos comentários\\No nome de quem você\\Nquer abençoar")
    Path(saida).write_text("\n".join(L) + "\n", encoding="utf-8")


def luz(saida):
    """Camada de luz quente + vinheta (dá o clima de oração e unifica as imagens)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i in range(40):   # vinheta
        a = int(150 * (i / 40) ** 2)
        d.rectangle((i * 12, i * 20, W - i * 12, H - i * 20), outline=(0, 0, 0, max(0, 150 - a)), width=14)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(g)
    dg.ellipse((-300, -500, 900, 700), fill=(255, 200, 120, 45))        # luz vinda do alto
    dg.rectangle((0, 1000, W, H), fill=(0, 0, 0, 90))                    # base mais escura p/ legenda
    g = g.filter(ImageFilter.GaussianBlur(160))
    img = Image.alpha_composite(img.filter(ImageFilter.GaussianBlur(30)), g)
    img.save(saida)
    return saida


def montar(r, imagens, voz, musica, saida, tmp, semente=0):
    tmp = Path(tmp); tmp.mkdir(parents=True, exist_ok=True)
    dv = dur(voz); total = dv + 3.2
    n = max(3, min(len(imagens), int(total // 9) + 1)); rnd = random.Random(semente)
    imgs = imagens[:]; rnd.shuffle(imgs); imgs = (imgs * 3)[:n]
    seg = total / n + 1.0; xf = 1.0
    ent, fc = [], ""
    for i, im in enumerate(imgs):
        ent += ["-loop", "1", "-framerate", str(FPS), "-t", f"{seg:.2f}", "-i", im]
        zin = rnd.choice([True, False]); fr = int(seg * FPS)
        z = f"'min(1+0.0010*on,1.12)'" if zin else f"'max(1.12-0.0010*on,1.0)'"
        fc += (f"[{i}:v]scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
               f"zoompan=z={z}:d={fr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
               f"eq=saturation=0.95:brightness=0.02:gamma=1.12,setsar=1,format=yuv420p[v{i}];")
    ant = "v0"; off = 0.0
    for i in range(1, n):
        off += seg - xf
        fc += f"[{ant}][v{i}]xfade=transition=fade:duration={xf}:offset={off:.2f}[x{i}];"; ant = f"x{i}"
    lz = luz(tmp / "luz.png"); ass = tmp / "leg.ass"; legenda_ass(r, dv, total, ass)
    k = len(imgs)
    ent += ["-loop", "1", "-t", f"{total:.2f}", "-i", lz, "-i", voz, "-i", musica]
    fc += (f"[{ant}][{k}:v]overlay=0:0,trim=0:{total:.2f},ass='{ass}':fontsdir={FONTES}[v];"
           f"[{k + 1}:a]adelay=400|400,apad[vz];[{k + 2}:a]volume=0.20,afade=t=out:st={total - 3:.2f}:d=3[mu];"
           f"[vz][mu]amix=inputs=2:duration=longest:normalize=0,atrim=0:{total:.2f}[a]")
    run(["ffmpeg", "-y", "-v", "error", *ent, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", saida])
    return saida
