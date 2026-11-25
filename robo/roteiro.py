"""Roteiro da oração (IA grátis: Groq, com Gemini de reserva). Português do Brasil.
Formato que fazia o canal crescer: oração direcionada a quem assiste, gentil, pedindo o nome de alguém nos comentários."""
import json, random
from comum import EST, ler, salvar
from ia import gerar

TEMAS = ["ansiedade e paz no coração", "cura e saúde", "proteção da família", "provisão e trabalho", "gratidão",
         "força para não desistir", "perdão e recomeço", "filhos e netos", "sono tranquilo e descanso", "casamento e lar",
         "libertação do medo", "esperança em dias difíceis", "luto e consolo", "sabedoria nas decisões",
         "fé que move montanhas", "portas abertas", "proteção na estrada e no dia", "amor de Deus que acolhe",
         "milagre na vida financeira", "paz na mente antes de dormir"]
PERIODO = {"manha": ("nesta manhã", "bom dia"), "tarde": ("nesta tarde", "boa tarde"), "noite": ("nesta noite", "boa noite")}

SISTEMA = """Você escreve orações curtas para o canal cristão "Abraço do Pai" (YouTube Shorts), em português do Brasil.
Quem fala é um NARRADOR que ora pela pessoa (NUNCA fale como se fosse Jesus ou Deus em primeira pessoa).
Tom: manso, acolhedor, reverente, nunca agressivo, nunca promessas absolutas de cura ou dinheiro, nada de medo ou culpa.
Estrutura: 1) pergunta gentil de abertura ("Posso orar por você {periodo}?"); 2) convite para escrever nos comentários o
nome de alguém que a pessoa quer abençoar; 3) a oração em si, falando com Deus ("Senhor...", "Pai..."), citando com
palavras próprias UM versículo (diga a referência POR EXTENSO para a voz ler bem, ex.: "como diz o Salmo vinte e três", "Filipenses, capítulo quatro, versículo sete"); 4) agradecimento e "Amém"; 5) convite
curto e carinhoso para curtir e compartilhar com quem precisa. Frases curtas, com pausas (use reticências ... ).
Sem emojis no texto falado."""


def escolher_tema(periodo):
    usados = ler(EST / "temas_usados.json", [])
    livres = [t for t in TEMAS if t not in usados[-12:]] or TEMAS
    if periodo == "noite":
        livres = [t for t in livres if "sono" in t or "noite" in t or "paz" in t or "descanso" in t] or livres
    tema = random.choice(livres)
    salvar(EST / "temas_usados.json", (usados + [tema])[-60:])
    return tema


def criar(periodo="manha", tema=None, palavras=(165, 185)):
    tema = tema or escolher_tema(periodo)
    quando, saudacao = PERIODO[periodo]
    pedido = f"""Tema: {tema}. Período: {quando} ({saudacao}).
Escreva o texto FALADO com {palavras[0]} a {palavras[1]} palavras (o vídeo tem ~65 s com voz lenta).
Responda só em JSON:
{{"titulo": "título curto e emocional, 2 a 5 palavras, como 'Jesus te Cura Agora', 'Deus Manda te Dizer Hoje', '{saudacao.title()} Deus'",
 "versiculo_ref": "SÓ com números, ex.: Salmos 23:1 ou Filipenses 4:7 (este aparece escrito na tela)",
 "frase_tela": "a ideia do versículo em até 12 palavras, com suas palavras",
 "texto": "texto falado",
 "descricao": "2 linhas para a descrição do YouTube + pedido de nome nos comentários",
 "hashtags": ["#deus", "#jesus", "#oração", "... 5 a 7 no total"]}}"""
    for tentativa in range(3):
        r = json.loads(gerar(pedido.replace("{periodo}", quando), sistema=SISTEMA.replace("{periodo}", quando), json_saida=True))
        if len(r.get("texto", "").split()) >= palavras[0] - 15:
            break
        pedido += f"\nATENÇÃO: o texto anterior ficou curto demais. Escreva PELO MENOS {palavras[0]} palavras."
    r.update({"tema": tema, "periodo": periodo})
    return r


if __name__ == "__main__":
    import sys
    print(json.dumps(criar(sys.argv[1] if len(sys.argv) > 1 else "manha"), ensure_ascii=False, indent=1))
