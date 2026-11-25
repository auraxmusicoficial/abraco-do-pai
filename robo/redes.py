"""Instagram e TikTok do Abraço do Pai pelo Buffer (conta própria do canal). O vídeo fica num release do GitHub
(link público que o Buffer baixa) e é agendado no mesmo horário do YouTube."""
import json, os, subprocess, urllib.request
from datetime import datetime, timedelta
from comum import BRT

CANAIS = {"instagram": "6b06f89d8541f09ecb9e25a6", "tiktok": "6b06f8378541f09ecb9e1107"}
REPO = os.environ.get("GITHUB_REPOSITORY", "auraxmusicoficial/abraco-do-pai")
MUT = """mutation($input: CreatePostInput!) { createPost(input: $input) { __typename
  ... on PostActionSuccess { post { id } } ... on InvalidInputError { message } ... on UnexpectedError { message } } }"""


def gql(q, v):
    req = urllib.request.Request("https://api.buffer.com", json.dumps({"query": q, "variables": v}).encode(),
                                 {"Authorization": "Bearer " + os.environ["BUFFER_KEY"], "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def hospedar(arquivo, data, nome):
    """Sobe o vídeo como asset do release pub-<data> e devolve o link público."""
    tag = f"pub-{data}"
    if subprocess.run(["gh", "release", "view", tag, "-R", REPO], capture_output=True).returncode != 0:
        subprocess.run(["gh", "release", "create", tag, "-R", REPO, "-t", f"Publicações {data}", "-n", "vídeos do dia (o robô apaga depois)"], check=True)
    alvo = arquivo.parent / nome
    if alvo != arquivo:
        alvo.write_bytes(arquivo.read_bytes())
    subprocess.run(["gh", "release", "upload", tag, str(alvo), "--clobber", "-R", REPO], check=True)
    return f"https://github.com/{REPO}/releases/download/{tag}/{nome}"


def limpar_releases(dias=4):
    out = subprocess.run(["gh", "release", "list", "-R", REPO, "--limit", "60", "--json", "tagName"], capture_output=True, text=True).stdout
    limite = (datetime.now(BRT) - timedelta(days=dias)).strftime("%Y-%m-%d")
    for r in json.loads(out or "[]"):
        tag = r["tagName"]
        if tag.startswith("pub-") and tag[4:] < limite:
            subprocess.run(["gh", "release", "delete", tag, "-R", REPO, "--yes", "--cleanup-tag"], capture_output=True)


def agendar(url, legenda, titulo_tt, quando_utc_iso):
    ids = {}
    for rede, meta in (("instagram", {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": False}}),
                       ("tiktok", {"tiktok": {"title": titulo_tt[:90], "isAiGenerated": False}})):
        inp = {"channelId": CANAIS[rede], "text": legenda, "assets": [{"video": {"url": url}}], "metadata": meta,
               "mode": "customScheduled", "dueAt": quando_utc_iso, "schedulingType": "automatic", "needsApproval": False}
        try:
            res = gql(MUT, {"input": inp})["data"]["createPost"]
            if res["__typename"] == "PostActionSuccess":
                ids[rede] = res["post"]["id"]
            else:
                print("Buffer recusou", rede, res)
        except Exception as e:
            print("Buffer falhou", rede, e)
    return ids
