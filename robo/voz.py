"""Voz do narrador: Gemini TTS, voz "Algieba" (escolhida pelo Felipe em 25/11), com tratamento para soar mansa,
masculina, imponente e acolhedora (mais lenta, um pouco mais grave, corpo nos graves, eco leve)."""
import base64, json, os, time, urllib.request
from pathlib import Path
from comum import run

VOZ = "Algieba"
MODELOS = ["gemini-3.8-flash-tts", "gemini-flash-tts-latest"]
TRATAMENTO = "atempo=0.92,asetrate=24000*0.96,aresample=24000,bass=g=3:f=120,aecho=0.8:0.6:60:0.18,loudnorm=I=-16:TP=-1.5"


def falar(texto, saida):
    saida = Path(saida); pcm = saida.with_suffix(".pcm")
    corpo = {"contents": [{"parts": [{"text": texto}]}], "generationConfig": {"responseModalities": ["AUDIO"],
             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOZ}}}}}
    erro = None
    for modelo in MODELOS:
        for t in range(4):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={os.environ['GEMINI_KEY']}"
                r = json.load(urllib.request.urlopen(urllib.request.Request(url, json.dumps(corpo).encode(),
                                                                            {"Content-Type": "application/json"}), timeout=180))
                pcm.write_bytes(base64.b64decode(r["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]))
                run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", pcm,
                     "-af", f"silenceremove=start_periods=1:start_threshold=-45dB,{TRATAMENTO}", "-ar", "44100", saida])
                pcm.unlink(missing_ok=True)
                return saida
            except Exception as e:
                erro = e; print(f"voz: {modelo} tentativa {t + 1} falhou: {e}")
                time.sleep(25 if "429" in str(e) else 8)
    raise RuntimeError(f"voz falhou: {erro}")
