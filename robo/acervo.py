"""Monta o acervo de imagens SEM chave: Wikimedia Commons, só arquivos em DOMÍNIO PÚBLICO ou CC0 (uso livre, sem crédito
obrigatório). Pinturas clássicas de Jesus (assets/pinturas) e paisagens calmas — céu, nuvens, pôr do sol, mar, luz
(assets/paisagens). Roda no GitHub Actions (a rede de lá acessa o Commons). Uso: python3 robo/acervo.py"""
import json, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image
from comum import RAIZ

UA = {"User-Agent": "AbracoDoPaiBot/1.0 (https://github.com/auraxmusicoficial/abraco-do-pai)"}
API = "https://commons.wikimedia.org/w/api.php"
CATEGORIAS = {
    "pinturas": ["Paintings_by_Carl_Heinrich_Bloch", "Paintings_by_Heinrich_Hofmann", "Christ_in_Gethsemane_in_art",
                 "Sermon_on_the_Mount_in_art", "Good_Shepherd_in_art", "Christ_blessing_in_art",
                 "Paintings_of_the_Resurrection_of_Jesus", "Jesus_walking_on_water_in_art", "Christ_Pantocrator_icons"],
    "paisagens": ["Quality_images_of_sunsets", "Quality_images_of_sunrises", "Quality_images_of_clouds",
                  "Featured_pictures_of_sunsets", "Quality_images_of_seascapes", "Crepuscular_rays",
                  "Featured_pictures_of_clouds", "Quality_images_of_lakes"],
}
LIVRE = ("public domain", "pd-", "cc0", "cc-zero", "pd-old", "pd-art")
MAX_POR_TIPO = 60


def api(**q):
    q.update({"format": "json"})
    for t in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers=UA), timeout=60))
        except Exception as e:
            print("api:", e); time.sleep(5 * (t + 1))
    return {}


def arquivos(cat):
    r = api(action="query", list="categorymembers", cmtitle="Category:" + cat, cmtype="file", cmlimit=80)
    return [m["title"] for m in r.get("query", {}).get("categorymembers", [])]


def info(titulos):
    r = api(action="query", titles="|".join(titulos), prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=1400)
    return list(r.get("query", {}).get("pages", {}).values())


def main():
    reg_p = RAIZ / "assets" / "creditos.json"
    reg = json.loads(reg_p.read_text()) if reg_p.exists() else {}
    for tipo, cats in CATEGORIAS.items():
        pasta = RAIZ / "assets" / tipo; pasta.mkdir(parents=True, exist_ok=True)
        n = len(list(pasta.glob("*.jpg")))
        for cat in cats:
            if n >= MAX_POR_TIPO:
                break
            tits = [t for t in arquivos(cat) if t.lower().endswith((".jpg", ".jpeg"))]
            for i in range(0, len(tits), 20):
                for p in info(tits[i:i + 20]):
                    if n >= MAX_POR_TIPO:
                        break
                    ii = (p.get("imageinfo") or [{}])[0]; meta = ii.get("extmetadata", {})
                    lic = (meta.get("LicenseShortName", {}).get("value", "") + " " + meta.get("License", {}).get("value", "")).lower()
                    if not any(x in lic for x in LIVRE):
                        continue
                    if ii.get("width", 0) < 1000 or ii.get("height", 0) < 900:
                        continue
                    nome = "".join(c if c.isalnum() else "_" for c in p["title"][5:])[:80] + ".jpg"
                    destino = pasta / nome
                    if destino.exists():
                        continue
                    try:
                        raw = urllib.request.urlopen(urllib.request.Request(ii["thumburl"], headers=UA), timeout=60).read()
                        tmp = destino.with_suffix(".tmp"); tmp.write_bytes(raw)
                        im = Image.open(tmp).convert("RGB"); im.thumbnail((1400, 1400)); im.save(destino, quality=86); tmp.unlink()
                        reg[f"{tipo}/{nome}"] = {"arquivo": p["title"], "licenca": lic.strip()[:60],
                                                 "autor": meta.get("Artist", {}).get("value", "")[:120]}
                        n += 1; print("ok", tipo, nome, lic[:30])
                    except Exception as e:
                        print("falhou", nome, e)
                    time.sleep(0.5)
        print(tipo, n, "imagens")
    reg_p.write_text(json.dumps(reg, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
