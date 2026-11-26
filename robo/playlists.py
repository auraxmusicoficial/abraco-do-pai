"""Playlists do Abraço do Pai: Oração da Manhã / do Meio-dia / da Noite. Cria as que faltam e coloca cada vídeo na certa.
Quem termina uma oração emenda na próxima da playlist (mais tempo assistido no canal).
python3 robo/playlists.py organizar  -> coloca também os vídeos ANTIGOS do canal (pelo título: bom dia / boa tarde / boa noite)"""
import json, sys, urllib.request
from comum import EST, ler, salvar
from youtube import token

PLAYLISTS = {
    "manha": ("Oração da Manhã 🙏 Comece o Dia com Deus",
              "Orações da manhã para começar o dia na presença de Deus. Escreva nos comentários o seu nome e o de quem você quer abençoar."),
    "tarde": ("Oração do Meio-dia 🙏 Uma Pausa com Deus",
              "Orações do meio do dia para renovar a fé, a paz e a força. Deixe seu nome nos comentários para orarmos por você."),
    "noite": ("Oração da Noite 🙏 Antes de Dormir",
              "Orações da noite para dormir em paz, entregando tudo a Deus. Escreva nos comentários o nome de quem você quer abençoar."),
}


def api(tok, metodo, caminho, corpo=None):
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/" + caminho, json.dumps(corpo).encode() if corpo else None,
                                 {"Authorization": "Bearer " + tok, "Content-Type": "application/json"}, method=metodo)
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        return {"error": {"message": e.read().decode()[:300]}}


def garantir(tok, chave):
    ids = ler(EST / "playlists.json", {})
    if chave in ids:
        return ids[chave]
    titulo, desc = PLAYLISTS[chave]
    r = api(tok, "POST", "playlists?part=snippet,status", {"snippet": {"title": titulo, "description": desc, "defaultLanguage": "pt-BR"},
                                                          "status": {"privacyStatus": "public"}})
    if "error" in r:
        print("playlist não criada:", r["error"]["message"]); return None
    ids[chave] = r["id"]; salvar(EST / "playlists.json", ids); print("playlist criada:", titulo)
    return r["id"]


def adicionar(vid, chave, tok=None):
    tok = tok or token(); pl = garantir(tok, chave)
    if not pl:
        return False
    r = api(tok, "POST", "playlistItems?part=snippet", {"snippet": {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}})
    print("playlist", chave, vid, "ok" if "error" not in r else r["error"]["message"][:120])
    return "error" not in r


def periodo_pelo_titulo(t):
    t = t.lower()
    if any(x in t for x in ("boa noite", "noite", "dormir", "deitar")):
        return "noite"
    if any(x in t for x in ("bom dia", "manhã", "manha", "amanhecer")):
        return "manha"
    if any(x in t for x in ("boa tarde", "tarde", "meio-dia", "meio dia")):
        return "tarde"
    return None


def organizar():
    tok = token()
    up = api(tok, "GET", "channels?part=contentDetails&mine=true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ja = set(ler(EST / "playlist_feitos.json", [])); pt = ""
    while True:
        r = api(tok, "GET", f"playlistItems?part=snippet,status&maxResults=50&playlistId={up}" + (f"&pageToken={pt}" if pt else ""))
        for it in r.get("items", []):
            vid = it["snippet"]["resourceId"]["videoId"]
            if vid in ja or it.get("status", {}).get("privacyStatus") != "public":
                continue
            p = periodo_pelo_titulo(it["snippet"]["title"])
            if p and adicionar(vid, p, tok):
                ja.add(vid)
        pt = r.get("nextPageToken")
        if not pt:
            break
    salvar(EST / "playlist_feitos.json", sorted(ja))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "organizar":
        organizar()
