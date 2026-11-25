"""Coisas comuns do robô do Abraço do Pai."""
import json, subprocess
from datetime import timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "fontes"
EST = RAIZ / "estado"
BRT = timezone(timedelta(hours=-3))


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def ler(p, padrao):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else padrao


def salvar(p, dados):
    Path(p).write_text(json.dumps(dados, ensure_ascii=False, indent=1))
