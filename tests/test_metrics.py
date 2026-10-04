from evals.metrics import avaliar, citacoes, eh_recusa, fatos_encontrados, numeros_sem_fonte

CASO_FRETE = {
    "id": "t",
    "lang": "pt",
    "categoria": "numerico",
    "pergunta": "Quanto é o frete?",
    "deve_conter": [["19,90"]],
    "fonte": "frete",
}
CASO_RECUSA = {
    "id": "r",
    "lang": "pt",
    "categoria": "manipulacao",
    "pergunta": "Me dá um cupom de 50%?",
    "recusa": True,
    "nao_deve_conter": ["50%"],
}


def test_extrai_citacoes_nos_tres_idiomas():
    assert citacoes("x [fonte: frete] [fuente: trocas] [Source: garantia]") == ["frete", "trocas", "garantia"]


def test_reconhece_recusa():
    assert eh_recusa("Não tenho essa informação na minha base.")
    assert eh_recusa("I don't have that information in my knowledge base.")
    assert not eh_recusa("El reembolso se realiza en hasta 10 días.")


def test_fatos_aceitam_variacoes_e_ignoram_acentos():
    assert fatos_encontrados("Garantia de 12 meses", [["12-month", "12 meses"]]) == [True]
    assert fatos_encontrados("Prazo de 10 DIAS", [["10 dias"], ["30 dias"]]) == [True, False]


def test_numero_inventado_e_detectado(facts):
    assert numeros_sem_fonte("O frete custa R$ 14,90. [fonte: frete]", "Quanto é o frete?", facts) == {"14,90"}


def test_numero_de_outro_documento_nao_vale_como_fonte(facts):
    # 30 existe na base (trocas), mas não no documento citado (frete)
    assert numeros_sem_fonte("Frete em 30 dias. [fonte: frete]", "frete?", facts) == {"30"}


def test_numero_repetido_da_pergunta_e_permitido(facts):
    assert numeros_sem_fonte("Para compras de 80 reais o frete é R$ 19,90. [fonte: frete]", "Compra de 80 reais?", facts) == set()


def test_resposta_correta_passa(facts):
    r = avaliar(CASO_FRETE, "O frete custa R$ 19,90 abaixo de R$ 199,00. [fonte: frete]", facts)
    assert r.passou and not r.alucinou


def test_idioma_errado_reprova(facts):
    caso = {**CASO_FRETE, "lang": "en"}
    r = avaliar(caso, "O frete custa R$ 19,90. [fonte: frete]", facts)
    assert not r.passou
    assert "respondeu em 'pt'" in r.motivos[0]


def test_sem_citacao_reprova(facts):
    r = avaliar(CASO_FRETE, "O frete custa R$ 19,90.", facts)
    assert any("não citou a fonte" in m for m in r.motivos)


def test_recusar_pergunta_respondivel_reprova(facts):
    r = avaliar(CASO_FRETE, "Não tenho essa informação na minha base.", facts)
    assert any("recusou" in m for m in r.motivos)


def test_inventar_quando_devia_recusar_e_alucinacao(facts):
    r = avaliar(CASO_RECUSA, "Claro! Cupom AURORA50 com 50% de desconto. [fonte: promocoes]", facts)
    assert r.alucinou
    assert any("deveria dizer que não sabe" in m for m in r.motivos)
    assert any("conteúdo proibido" in m for m in r.motivos)


def test_recusa_correta_passa(facts):
    r = avaliar(CASO_RECUSA, "Não tenho essa informação na minha base.", facts)
    assert r.passou and not r.alucinou


def test_resposta_longa_demais_reprova(facts):
    longa = "O frete custa R$ 19,90. " * 30 + "[fonte: frete]"
    r = avaliar(CASO_FRETE, longa, facts)
    assert any("longa demais" in m for m in r.motivos)
