"""Junta os resultados de todos os casos em métricas gerais e aplica as metas (gates)."""

import operator
from collections import defaultdict

from evals.config import GATES
from evals.metrics import ResultadoCaso

_OPS = {">=": operator.ge, "<=": operator.le}


def _taxa(parte: int, total: int) -> float:
    return parte / total if total else 1.0


def resumir(resultados: list[ResultadoCaso]) -> dict:
    respondiveis = [r for r in resultados if not r.recusa_esperada]
    recusaveis = [r for r in resultados if r.recusa_esperada]

    grupos = defaultdict(list)
    for r in resultados:
        if r.grupo:
            grupos[r.grupo].append(r)
    grupos_ok = [all(x.checks.get("recall_fatos") == 1.0 for x in casos) for casos in grupos.values()]

    metricas = {
        "acuracia": _taxa(sum(r.passou for r in resultados), len(resultados)),
        "taxa_alucinacao": _taxa(sum(r.alucinou for r in resultados), len(resultados)),
        "idioma_correto": _taxa(sum(r.checks["idioma"] == r.lang for r in resultados), len(resultados)),
        "recusa_correta": _taxa(sum(r.checks["recusou"] for r in recusaveis), len(recusaveis)),
        "recusa_indevida": _taxa(sum(r.checks["recusou"] for r in respondiveis), len(respondiveis)),
        "citacao_correta": _taxa(sum(r.checks.get("citou_fonte", False) for r in respondiveis), len(respondiveis)),
        "recall_fatos": sum(r.checks.get("recall_fatos", 0) for r in respondiveis) / max(len(respondiveis), 1),
        "consistencia": _taxa(sum(grupos_ok), len(grupos_ok)),
    }

    por_categoria = defaultdict(lambda: [0, 0])
    for r in resultados:
        por_categoria[r.categoria][0] += r.passou
        por_categoria[r.categoria][1] += 1

    gates = {nome: (op, limite, _OPS[op](metricas[nome], limite)) for nome, (op, limite) in GATES.items()}
    return {
        "total": len(resultados),
        "metricas": metricas,
        "por_categoria": dict(por_categoria),
        "gates": gates,
        "aprovado": all(ok for _, _, ok in gates.values()),
    }
