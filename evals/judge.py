"""Juiz LLM (opcional): um segundo modelo dá notas de 1 a 5 para cada resposta.

Complementa as métricas determinísticas em critérios difíceis de medir com regra fixa,
como clareza e tom. Só roda com ANTHROPIC_API_KEY.
"""

import json
import os
import re

RUBRICA = """Você avalia respostas de um assistente de suporte de loja virtual.
Dê notas de 1 a 5:
- correcao: a resposta está de acordo com os FATOS DE REFERÊNCIA? (5 = totalmente correta)
- fidelidade: a resposta evita inventar qualquer coisa fora dos fatos? (5 = nada inventado)
- tom: é educada, clara e direta, como um bom atendimento? (5 = excelente)
Se a resposta certa era recusar (fatos de referência vazios), dê correcao 5 apenas se o assistente disse que não sabe.
Responda SOMENTE com JSON: {"correcao": n, "fidelidade": n, "tom": n, "justificativa": "..."}"""

CRITERIOS = ("correcao", "fidelidade", "tom")


class JuizLLM:
    def __init__(self, client=None, model: str | None = None):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self.model = model or os.environ.get("JUDGE_MODEL") or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    def avaliar(self, pergunta: str, resposta: str, fatos: list[str]) -> dict:
        referencia = "\n".join(f"- {f}" for f in fatos) or "(nenhum: a resposta certa é dizer que não sabe)"
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            temperature=0,
            system=RUBRICA,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"PERGUNTA:\n{pergunta}\n\nFATOS DE REFERÊNCIA:\n{referencia}\n\nRESPOSTA DO ASSISTENTE:\n{resposta}"
                    ),
                }
            ],
        )
        texto = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return parse_notas(texto)


def parse_notas(texto: str) -> dict:
    """Extrai o JSON da resposta do juiz, mesmo que venha cercado de texto. Notas fora de 1 a 5 são limitadas."""
    achado = re.search(r"\{.*\}", texto, re.DOTALL)
    if not achado:
        raise ValueError(f"o juiz não devolveu JSON: {texto[:120]}")
    dados = json.loads(achado.group(0))
    notas = {c: min(5, max(1, int(dados[c]))) for c in CRITERIOS}
    notas["justificativa"] = str(dados.get("justificativa", ""))
    return notas


def media(notas: list[dict]) -> dict:
    return {c: sum(n[c] for n in notas) / len(notas) for c in CRITERIOS} if notas else {}
