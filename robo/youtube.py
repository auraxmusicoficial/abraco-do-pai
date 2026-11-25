"""Envio direto ao YouTube do Abraço do Pai (API oficial, grátis): sobe o vídeo agendado (privado + publishAt)."""
import json, os, urllib.parse, urllib.request


def token():
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", d, timeout=60))["access_token"]


def enviar(arquivo, titulo, descricao, tags, publicar_em_iso, categoria="22"):
    tok = token()
    meta = {"snippet": {"title": titulo[:100], "description": descricao[:4900], "tags": tags[:15], "categoryId": categoria,
                        "defaultLanguage": "pt-BR", "defaultAudioLanguage": "pt-BR"},
            "status": {"privacyStatus": "private", "publishAt": publicar_em_iso, "selfDeclaredMadeForKids": False,
                       "embeddable": True}}
    dados = open(arquivo, "rb").read()
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=true",
        json.dumps(meta).encode(), {"Authorization": "Bearer " + tok, "Content-Type": "application/json; charset=UTF-8",
                                    "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(dados))})
    url = urllib.request.urlopen(req, timeout=60).headers["Location"]
    up = urllib.request.Request(url, dados, {"Content-Type": "video/mp4"}, method="PUT")
    vid = json.load(urllib.request.urlopen(up, timeout=600))["id"]
    return vid
