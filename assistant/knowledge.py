"""Base de conhecimento e busca (retrieval) dos fatos relevantes para cada pergunta."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from assistant.text import contains_term, normalize

KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.yaml"


@dataclass(frozen=True)
class Fact:
    id: str
    fonte: str
    termos: tuple[str, ...]
    texto: dict  # {"pt": ..., "es": ..., "en": ...}


def load_facts(path: Path = KB_PATH) -> list[Fact]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        Fact(id=f["id"], fonte=f["fonte"], termos=tuple(f["termos"]), texto={k: f[k] for k in ("pt", "es", "en")})
        for f in data["fatos"]
    ]


def retrieve(question: str, facts: list[Fact], limit: int = 2) -> list[Fact]:
    """Devolve os fatos mais relevantes. Termos com mais palavras pesam mais (\"frete gratis\" > \"frete\").

    Fatos com menos da metade da pontuação do melhor ficam de fora, para não poluir a resposta.
    Lista vazia = a pergunta não está coberta pela base.
    """
    q = normalize(question)
    scored = []
    for fact in facts:
        score = sum(len(t.split()) for t in fact.termos if contains_term(q, t))
        if score:
            scored.append((score, fact))
    if not scored:
        return []
    scored.sort(key=lambda s: -s[0])
    best = scored[0][0]
    return [fact for score, fact in scored if score * 2 >= best][:limit]
