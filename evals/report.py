"""Relatório da avaliação em Markdown (terminal e painel do GitHub Actions) e JSON."""

import json
from pathlib import Path

from evals.metrics import ResultadoCaso

NOMES = {
    "acuracia": "Acurácia (casos 100% corretos)",
    "taxa_alucinacao": "Taxa de alucinação",
    "idioma_correto": "Responde no idioma do cliente",
    "recusa_correta": 'Diz "não sei" quando deve',
    "recusa_indevida": "Recusa o que deveria responder",
    "citacao_correta": "Cita a fonte certa",
    "recall_fatos": "Fatos obrigatórios presentes",
    "consistencia": "Consistência entre perguntas parecidas",
}
CATEGORIAS = {
    "factual": "Factual",
    "numerico": "Números e prazos",
    "multilingue": "Espanhol e inglês",
    "fora_do_escopo": "Fora da base",
    "manipulacao": "Tentativas de manipulação",
}


def _pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def markdown(modelo: str, resumo: dict, resultados: list[ResultadoCaso], juiz: dict | None = None) -> str:
    m = resumo["metricas"]
    linhas = [
        f"## Avaliação de qualidade · assistente `{modelo}`",
        "",
        f"**Resultado:** {'✅ aprovado nas metas de qualidade' if resumo['aprovado'] else '❌ reprovado'} "
        f"· {resumo['total']} perguntas",
        "",
        "| | Métrica | Valor | Meta |",
        "|---|---|---|---|",
    ]
    for nome, (op, limite, ok) in resumo["gates"].items():
        linhas.append(f"| {'✅' if ok else '❌'} | {NOMES[nome]} | {_pct(m[nome])} | {op} {_pct(limite)} |")
    linhas.append(f"| | {NOMES['recall_fatos']} | {_pct(m['recall_fatos'])} | |")

    linhas += ["", "### Por categoria", "", "| Categoria | Acertos |", "|---|---|"]
    for cat, (ok, total) in resumo["por_categoria"].items():
        linhas.append(f"| {CATEGORIAS.get(cat, cat)} | {ok}/{total} |")

    if juiz:
        linhas += ["", "### Juiz LLM (nota média de 1 a 5)", "", "| Critério | Nota |", "|---|---|"]
        linhas += [f"| {k} | {v:.1f} |" for k, v in juiz.items()]

    falhas = [r for r in resultados if not r.passou]
    if falhas:
        linhas += ["", f"### Falhas ({len(falhas)})", ""]
        for r in falhas[:15]:
            resposta = r.resposta if len(r.resposta) <= 160 else r.resposta[:157] + "..."
            linhas.append(f"- **{r.id}** · {r.pergunta}")
            linhas.append(f"  - Resposta: _{resposta}_")
            linhas.append(f"  - Por quê: {'; '.join(r.motivos)}")
        if len(falhas) > 15:
            linhas.append(f"- ... e mais {len(falhas) - 15} no JSON")
    return "\n".join(linhas) + "\n"


def salvar(pasta: Path, modelo: str, md: str, resumo: dict, resultados: list[ResultadoCaso]) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / f"avaliacao-{modelo}.md").write_text(md, encoding="utf-8")
    dados = {
        "modelo": modelo,
        "aprovado": resumo["aprovado"],
        "metricas": resumo["metricas"],
        "casos": [
            {
                "id": r.id,
                "passou": r.passou,
                "pergunta": r.pergunta,
                "resposta": r.resposta,
                "motivos": r.motivos,
                "checks": r.checks,
            }
            for r in resultados
        ],
    }
    caminho = pasta / f"avaliacao-{modelo}.json"
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho
