"""Assistente Claude e juiz LLM testados com um cliente falso: sem rede e sem custo."""

from types import SimpleNamespace

import pytest

from assistant.models import SYSTEM_PROMPT, AssistenteClaude
from evals.judge import JuizLLM, media, parse_notas


class ClienteFalso:
    def __init__(self, resposta: str):
        self.resposta = resposta
        self.chamadas = []
        self.messages = self

    def create(self, **kwargs):
        self.chamadas.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.resposta)])


def test_assistente_claude_envia_contexto_da_base_e_regras(facts):
    cliente = ClienteFalso("O frete custa R$ 19,90.\n[fonte: frete]")
    resposta = AssistenteClaude(client=cliente, model="modelo-teste", facts=facts).responder("Quanto custa o frete?")

    chamada = cliente.chamadas[0]
    assert chamada["system"] == SYSTEM_PROMPT and chamada["temperature"] == 0
    assert "R$ 19,90" in chamada["messages"][0]["content"]  # o fato certo foi para o contexto
    assert resposta.texto == "O frete custa R$ 19,90. [fonte: frete]"


def test_assistente_claude_avisa_quando_nao_ha_contexto(facts):
    cliente = ClienteFalso("Não tenho essa informação na minha base.")
    AssistenteClaude(client=cliente, model="m", facts=facts).responder("Vocês vendem carros?")
    assert "(nenhuma informação encontrada)" in cliente.chamadas[0]["messages"][0]["content"]


def test_parse_notas_extrai_json_cercado_de_texto():
    notas = parse_notas('Segue: {"correcao": 5, "fidelidade": 4, "tom": 9, "justificativa": "ok"} fim')
    assert notas == {"correcao": 5, "fidelidade": 4, "tom": 5, "justificativa": "ok"}  # 9 vira 5


def test_parse_notas_sem_json_falha_com_mensagem_clara():
    with pytest.raises(ValueError, match="não devolveu JSON"):
        parse_notas("não sei avaliar")


def test_juiz_usa_rubrica_e_fatos_de_referencia():
    cliente = ClienteFalso('{"correcao": 4, "fidelidade": 5, "tom": 5, "justificativa": "boa"}')
    notas = JuizLLM(client=cliente, model="m").avaliar("Frete?", "R$ 19,90", ["Frete de R$ 19,90"])
    assert notas["correcao"] == 4
    assert "Frete de R$ 19,90" in cliente.chamadas[0]["messages"][0]["content"]


def test_media_das_notas():
    notas = [{"correcao": 4, "fidelidade": 5, "tom": 3}, {"correcao": 2, "fidelidade": 5, "tom": 5}]
    assert media(notas) == {"correcao": 3, "fidelidade": 5, "tom": 4}
