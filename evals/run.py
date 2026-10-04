"""Roda a avaliação: python -m evals.run --model simulado

Termina com código 1 se alguma meta de qualidade for violada (o CI fica vermelho).
Com --expect-fail, o esperado é reprovar: serve para provar que a avaliação pega um assistente ruim.
"""

import argparse
import os
import sys
from pathlib import Path

import yaml

from assistant.knowledge import load_facts
from assistant.models import MODELOS
from evals.aggregate import resumir
from evals.metrics import avaliar
from evals.report import markdown, salvar

ROOT = Path(__file__).resolve().parent.parent


def carregar_casos(caminho: Path = ROOT / "data" / "golden.yaml") -> list[dict]:
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))["casos"]


def executar(modelo, casos: list[dict], facts) -> list:
    return [avaliar(caso, modelo.responder(caso["pergunta"]).texto, facts) for caso in casos]


def notas_do_juiz(casos: list[dict], resultados: list, facts) -> dict:
    from evals.judge import JuizLLM, media

    juiz = JuizLLM()
    por_fonte = {}
    for f in facts:
        por_fonte.setdefault(f.fonte, []).append(f.texto["pt"])
    notas = [
        juiz.avaliar(c["pergunta"], r.resposta, [] if c.get("recusa") else por_fonte.get(c.get("fonte"), []))
        for c, r in zip(casos, resultados, strict=True)
    ]
    return {k.capitalize(): v for k, v in media(notas).items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Avaliação de qualidade de respostas de IA")
    parser.add_argument("--model", choices=sorted(MODELOS), default="simulado")
    parser.add_argument("--judge", action="store_true", help="usa um LLM como juiz (requer ANTHROPIC_API_KEY)")
    parser.add_argument("--expect-fail", action="store_true", help="o esperado é reprovar (prova de eficácia)")
    parser.add_argument("--out", default=str(ROOT / "reports"))
    args = parser.parse_args(argv)

    facts = load_facts()
    casos = carregar_casos()
    resultados = executar(MODELOS[args.model](), casos, facts)
    resumo = resumir(resultados)
    juiz = notas_do_juiz(casos, resultados, facts) if args.judge else None

    md = markdown(args.model, resumo, resultados, juiz)
    print(md)
    salvar(Path(args.out), args.model, md, resumo, resultados)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as painel:
            painel.write(md + "\n")

    if args.expect_fail:
        print(
            "✅ A avaliação reprovou o assistente defeituoso, como esperado."
            if not resumo["aprovado"]
            else "❌ O assistente defeituoso passou: a avaliação não pegou os problemas!"
        )
        return 0 if not resumo["aprovado"] else 1
    return 0 if resumo["aprovado"] else 1


if __name__ == "__main__":
    sys.exit(main())
