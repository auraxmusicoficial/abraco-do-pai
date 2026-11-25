"""Produção diária do Abraço do Pai — 100% sem Claude (GitHub Actions + IA grátis).
python3 robo/main.py            -> faz os 3 Shorts do dia (manhã 7h, tarde 12h, noite 20h) e agenda no YouTube
python3 robo/main.py teste      -> faz 1 Short e NÃO publica (fica em saida/)"""
import glob, json, os, random, sys, traceback, urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from comum import BRT, EST, RAIZ, dur, ler, salvar
import render, roteiro, trilha, voz

HORARIOS = {"manha": "07:00", "tarde": "12:00", "noite": "20:00"}
FIXAS = "#oração #deus #jesus #fé"


def imagens(periodo, rnd):
    pint = sorted(glob.glob(str(RAIZ / "assets" / "pinturas" / "*.jpg")))
    pais = sorted(glob.glob(str(RAIZ / "assets" / "paisagens" / "*.jpg")))
    rnd.shuffle(pint); rnd.shuffle(pais)
    escolha = pint[:3] + pais[:3] if pais else pint[:5]
    rnd.shuffle(escolha)
    return escolha or pint


def avisar(msg):
    topico = os.environ.get("NTFY_TOPIC")
    if topico:
        try:
            urllib.request.urlopen(urllib.request.Request(f"https://ntfy.sh/{topico}", msg.encode(),
                                                          {"Title": "Abraco do Pai"}), timeout=30)
        except Exception as e:
            print("ntfy falhou:", e)


def um_short(periodo, data, publicar=True):
    saida = RAIZ / "saida" / f"{data}_{periodo}"; saida.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(f"{data}{periodo}")
    r = roteiro.criar(periodo)
    salvar(saida / "roteiro.json", r)
    voz.falar(r["texto"], saida / "voz.wav")
    trilha.gerar(saida / "trilha.wav", dur(saida / "voz.wav") + 6, semente=rnd.randint(0, 10 ** 6))
    video = render.montar(r, imagens(periodo, rnd), saida / "voz.wav", saida / "trilha.wav", saida / "short.mp4",
                          saida / "tmp", semente=rnd.randint(0, 10 ** 6))
    print(f"ok {periodo}: {r['titulo']} ({dur(video):.1f}s)")
    if not publicar:
        return r, None
    hh, mm = map(int, HORARIOS[periodo].split(":"))
    quando = datetime.strptime(data, "%Y-%m-%d").replace(hour=hh, minute=mm, tzinfo=BRT)
    if quando < datetime.now(BRT) + timedelta(minutes=20):
        quando = datetime.now(BRT) + timedelta(minutes=25)
    tags_hash = " ".join(h if h.startswith("#") else "#" + h for h in r.get("hashtags", []))
    titulo = f"{r['titulo']} 🙏 {FIXAS}"[:100]
    desc = (f"{r.get('descricao', '')}\n\n🙏 Escreva nos comentários o nome de quem você quer abençoar.\n"
            f"👍 Curta e compartilhe com quem precisa desta oração.\n🔔 Inscreva-se para orar com a gente todos os dias.\n\n"
            f"📖 {r.get('versiculo_ref', '')}\n\n{tags_hash} {FIXAS}")
    tags = ["oração", "oração do dia", "deus", "jesus", "fé", r["tema"], {"manha": "oração da manhã", "tarde": "oração da tarde",
            "noite": "oração da noite"}[periodo], "abraço do pai"]
    from youtube import enviar
    from datetime import timezone
    vid = enviar(video, titulo, desc, tags, quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    reg = ler(EST / "publicacoes.json", [])
    reg.append({"data": data, "periodo": periodo, "quando": quando.isoformat(), "video_id": vid, "titulo": titulo,
                "tema": r["tema"], "versiculo": r.get("versiculo_ref"), "duracao": round(dur(video), 1)})
    salvar(EST / "publicacoes.json", reg)
    return r, vid


def main():
    teste = len(sys.argv) > 1 and sys.argv[1] == "teste"
    data = datetime.now(BRT).strftime("%Y-%m-%d")
    feitos, erros = [], []
    for periodo in (["noite"] if teste else ["manha", "tarde", "noite"]):
        ja = [p for p in ler(EST / "publicacoes.json", []) if p["data"] == data and p["periodo"] == periodo]
        if ja and not teste:
            print("já feito:", periodo); continue
        try:
            r, vid = um_short(periodo, data, publicar=not teste)
            feitos.append(f"{HORARIOS[periodo]} {r['titulo']}")
        except Exception:
            erros.append(periodo); traceback.print_exc()
    if not teste:
        msg = "Orações agendadas hoje:\n" + "\n".join(feitos) if feitos else "Nenhuma oração agendada hoje."
        if erros:
            msg += f"\n⚠️ Falhou: {', '.join(erros)} (o robô tenta de novo na próxima rodada)"
        avisar(msg)
    if erros and not feitos:
        sys.exit(1)


if __name__ == "__main__":
    main()
