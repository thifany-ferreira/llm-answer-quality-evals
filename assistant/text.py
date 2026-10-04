"""Funções de texto compartilhadas entre o assistente e as métricas."""

import re
import unicodedata

_STOPWORDS = {
    "pt": {
        "voce",
        "voces",
        "o",
        "os",
        "as",
        "da",
        "no",
        "na",
        "nos",
        "qual",
        "quais",
        "quanto",
        "quantos",
        "tem",
        "para",
        "um",
        "uma",
        "posso",
        "eu",
        "nao",
        "me",
        "suas",
        "sua",
        "com",
        "dias",
        "em",
        "ate",
        "e",
        "uteis",
        "aceitamos",
        "sao",
        "seu",
        "todos",
        "pelo",
        "ou",
        "frete",
        "compras",
    },
    "es": {
        "el",
        "la",
        "los",
        "las",
        "en",
        "cual",
        "cuanto",
        "cuantos",
        "tienen",
        "puedo",
        "como",
        "mi",
        "ustedes",
        "hay",
        "con",
        "del",
        "y",
        "recibo",
        "cuando",
        "dias",
        "hasta",
        "habiles",
        "tu",
        "envio",
        "aceptamos",
        "todos",
        "puedes",
        "despues",
        "se",
        "lo",
        "por",
        "esa",
        "tengo",
    },
    "en": {
        "the",
        "a",
        "do",
        "you",
        "is",
        "are",
        "what",
        "how",
        "can",
        "i",
        "my",
        "your",
        "there",
        "in",
        "with",
        "for",
        "me",
        "any",
        "make",
        "does",
        "have",
        "store",
        "of",
        "on",
        "we",
        "days",
        "within",
        "and",
        "all",
        "orders",
        "it",
        "that",
        "don't",
        "dont",
        "up",
        "at",
        "or",
        "get",
    },
}


def normalize(text: str) -> str:
    """Minúsculas e sem acentos, para comparar textos sem depender de grafia."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", normalize(text))


def detect_language(text: str) -> str:
    """Detecção simples de idioma (pt, es ou en) por palavras comuns. Empate fica com pt."""
    if "¿" in text or "¡" in text:
        return "es"
    tokens = words(text)
    scores = {lang: sum(t in sw for t in tokens) for lang, sw in _STOPWORDS.items()}
    best = max(scores.values())
    for lang in ("pt", "es", "en"):
        if scores[lang] == best:
            return lang
    return "pt"


def contains_term(normalized_text: str, term: str) -> bool:
    """Procura o termo como palavra inteira (\"entrega\" não casa com \"entregam\")."""
    return re.search(rf"(?<![a-z0-9]){re.escape(normalize(term))}(?![a-z0-9])", normalized_text) is not None


NUMBER_RE = re.compile(r"(?<![\w@.])\d+(?:[.,]\d+)?")


def numbers_in(text: str) -> set[str]:
    """Números citados no texto (\"19,90\", \"30\", \"9\" de \"9h\"). Ignora números colados em letras, como AURORA50."""
    return set(NUMBER_RE.findall(text))
