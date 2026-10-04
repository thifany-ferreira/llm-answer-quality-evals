import pytest

from assistant.knowledge import retrieve
from assistant.text import contains_term, detect_language, normalize, numbers_in


def test_normalize_remove_acentos_e_maiusculas():
    assert normalize("Devolução GRÁTIS") == "devolucao gratis"


def test_termo_casa_so_palavra_inteira():
    assert contains_term("qual o prazo de entrega", "entrega")
    assert not contains_term("voces entregam no japao", "entrega")


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Frete de R$ 19,90 em até 7 dias", {"19,90", "7"}),
        ("das 9h às 18h", {"9", "18"}),
        ("use o cupom AURORA50", set()),  # número colado em letras não conta
        ("suporte@lojaaurora.exemplo", set()),
    ],
)
def test_numeros_no_texto(texto, esperado):
    assert numbers_in(texto) == esperado


@pytest.mark.parametrize(
    ("texto", "idioma"),
    [
        ("Você pode trocar o produto em até 30 dias.", "pt"),
        ("Puedes cambiar el producto hasta 30 días después.", "es"),
        ("You can return the product within 30 days.", "en"),
    ],
)
def test_detecta_idioma_das_respostas(texto, idioma):
    assert detect_language(texto) == idioma


def test_busca_encontra_a_fonte_esperada(casos, facts):
    for c in casos:
        if c.get("recusa"):
            continue
        fontes = {f.fonte for f in retrieve(c["pergunta"], facts)}
        assert c["fonte"] in fontes, c["id"]


def test_busca_nao_encontra_nada_para_perguntas_fora_da_base(casos, facts):
    for c in casos:
        if c.get("recusa"):
            assert retrieve(c["pergunta"], facts) == [], c["id"]


def test_busca_descarta_fatos_pouco_relevantes(facts):
    ids = [f.id for f in retrieve("Qual o prazo para trocar um produto?", facts)]
    assert ids == ["troca-prazo"]
