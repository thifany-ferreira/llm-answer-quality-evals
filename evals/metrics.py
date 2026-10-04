"""Métricas de cada resposta. Todas são determinísticas: mesma resposta, mesmo resultado."""

import re
from dataclasses import dataclass, field

from assistant.knowledge import Fact
from assistant.text import detect_language, normalize, numbers_in, words
from evals.config import MAX_PALAVRAS

_CITACAO_RE = re.compile(r"\[(?:fonte|fuente|source):\s*([\w-]+)\]", re.IGNORECASE)
_MARCAS_RECUSA = [
    "nao tenho essa informacao",
    "nao sei",
    "nao encontrei essa informacao",
    "no tengo esa informacion",
    "no lo se",
    "no encontre esa informacion",
    "i don't have that information",
    "i do not have that information",
    "i don't know",
]


def citacoes(resposta: str) -> list[str]:
    return [c.lower() for c in _CITACAO_RE.findall(resposta)]


def eh_recusa(resposta: str) -> bool:
    texto = normalize(resposta)
    return any(marca in texto for marca in _MARCAS_RECUSA)


def fatos_encontrados(resposta: str, deve_conter: list[list[str]]) -> list[bool]:
    """Para cada fato obrigatório, se alguma das variações aparece na resposta."""
    texto = normalize(resposta)
    return [any(normalize(v) in texto for v in variacoes) for variacoes in deve_conter]


def numeros_sem_fonte(resposta: str, pergunta: str, facts: list[Fact]) -> set[str]:
    """Números na resposta que não existem nos documentos citados (nem na pergunta do cliente).

    É o principal sinal de alucinação: um prazo, preço ou desconto que a base não tem.
    Sem citação, compara com a base inteira.
    """
    citadas = set(citacoes(resposta))
    fontes = [f for f in facts if f.fonte in citadas] if citadas else facts
    permitidos = set().union(*(numbers_in(t) for f in fontes for t in f.texto.values())) if fontes else set()
    return numbers_in(resposta) - permitidos - numbers_in(pergunta)


@dataclass
class ResultadoCaso:
    id: str
    categoria: str
    pergunta: str
    resposta: str
    lang: str
    grupo: str | None
    recusa_esperada: bool
    checks: dict = field(default_factory=dict)
    motivos: list[str] = field(default_factory=list)

    @property
    def passou(self) -> bool:
        return not self.motivos

    @property
    def alucinou(self) -> bool:
        return (
            bool(self.checks.get("numeros_sem_fonte"))
            or self.checks.get("conteudo_proibido", False)
            or (self.recusa_esperada and not self.checks.get("recusou", False))
        )


def avaliar(caso: dict, resposta: str, facts: list[Fact]) -> ResultadoCaso:
    r = ResultadoCaso(
        id=caso["id"],
        categoria=caso["categoria"],
        pergunta=caso["pergunta"],
        resposta=resposta,
        lang=caso["lang"],
        grupo=caso.get("grupo"),
        recusa_esperada=caso.get("recusa", False),
    )
    c = r.checks
    c["idioma"] = detect_language(resposta)
    c["recusou"] = eh_recusa(resposta)
    c["numeros_sem_fonte"] = sorted(numeros_sem_fonte(resposta, caso["pergunta"], facts))
    proibidos = [t for t in caso.get("nao_deve_conter", []) if normalize(t) in normalize(resposta)]
    c["conteudo_proibido"] = bool(proibidos)
    c["palavras"] = len(words(resposta))

    if c["idioma"] != r.lang:
        r.motivos.append(f"respondeu em '{c['idioma']}', o cliente escreveu em '{r.lang}'")
    if proibidos:
        r.motivos.append(f"conteúdo proibido: {', '.join(proibidos)}")
    if c["numeros_sem_fonte"]:
        r.motivos.append(f"números que não estão na fonte: {', '.join(c['numeros_sem_fonte'])}")
    if c["palavras"] > MAX_PALAVRAS:
        r.motivos.append(f"resposta longa demais ({c['palavras']} palavras)")

    if r.recusa_esperada:
        if not c["recusou"]:
            r.motivos.append("deveria dizer que não sabe, mas respondeu")
        return r

    encontrados = fatos_encontrados(resposta, caso.get("deve_conter", []))
    c["recall_fatos"] = sum(encontrados) / len(encontrados) if encontrados else 1.0
    faltando = [v[0] for v, ok in zip(caso.get("deve_conter", []), encontrados, strict=True) if not ok]
    if c["recusou"]:
        r.motivos.append("recusou uma pergunta que a base responde")
    if faltando:
        r.motivos.append(f"faltou: {', '.join(faltando)}")
    c["citou_fonte"] = caso.get("fonte") in citacoes(resposta)
    if not c["citou_fonte"]:
        r.motivos.append(f"não citou a fonte '{caso.get('fonte')}'")
    return r
