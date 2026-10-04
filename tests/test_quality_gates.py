"""A avaliação de ponta a ponta: o assistente bom passa e o defeituoso é reprovado pelos motivos certos."""

import json

import pytest

from assistant.models import AssistenteAlucina, AssistenteSimulado
from evals.aggregate import resumir
from evals.run import executar, main


@pytest.fixture(scope="module")
def resumo_bom(casos, facts):
    return resumir(executar(AssistenteSimulado(facts), casos, facts))


@pytest.fixture(scope="module")
def resumo_ruim(casos, facts):
    return resumir(executar(AssistenteAlucina(facts), casos, facts))


def test_assistente_bom_aprovado_em_todas_as_metas(resumo_bom):
    reprovadas = [nome for nome, (_, _, ok) in resumo_bom["gates"].items() if not ok]
    assert resumo_bom["aprovado"], f"metas reprovadas: {reprovadas}"


def test_assistente_bom_nao_alucina(resumo_bom):
    assert resumo_bom["metricas"]["taxa_alucinacao"] == 0


def test_prova_de_eficacia_assistente_defeituoso_e_reprovado(resumo_ruim):
    assert not resumo_ruim["aprovado"]


@pytest.mark.parametrize("meta", ["taxa_alucinacao", "idioma_correto", "recusa_correta", "consistencia"])
def test_cada_defeito_e_pego_pela_metrica_certa(resumo_ruim, meta):
    _, _, ok = resumo_ruim["gates"][meta]
    assert not ok, f"a métrica '{meta}' não pegou o defeito"


def test_cli_aprova_simulado_e_salva_relatorios(tmp_path):
    assert main(["--model", "simulado", "--out", str(tmp_path)]) == 0
    dados = json.loads((tmp_path / "avaliacao-simulado.json").read_text(encoding="utf-8"))
    assert dados["aprovado"] and len(dados["casos"]) > 20
    assert (tmp_path / "avaliacao-simulado.md").exists()


def test_cli_reprova_assistente_defeituoso(tmp_path):
    assert main(["--model", "alucina", "--out", str(tmp_path)]) == 1


def test_cli_expect_fail_vira_sucesso_quando_reprova(tmp_path):
    assert main(["--model", "alucina", "--expect-fail", "--out", str(tmp_path)]) == 0
