"""O próprio conjunto de referência é testado: um gabarito errado invalida a avaliação inteira."""

from assistant.text import detect_language, numbers_in

CATEGORIAS = {"factual", "numerico", "multilingue", "fora_do_escopo", "manipulacao"}


def test_ids_unicos(casos):
    ids = [c["id"] for c in casos]
    assert len(ids) == len(set(ids))


def test_campos_obrigatorios_e_categorias(casos):
    for c in casos:
        assert {"id", "lang", "categoria", "pergunta"} <= c.keys(), c["id"]
        assert c["lang"] in {"pt", "es", "en"}, c["id"]
        assert c["categoria"] in CATEGORIAS, c["id"]
        if c.get("recusa"):
            assert "deve_conter" not in c, f"{c['id']}: caso de recusa não deve exigir fatos"
        else:
            assert c.get("deve_conter") and c.get("fonte"), f"{c['id']}: faltam deve_conter ou fonte"


def test_tres_idiomas_cobertos(casos):
    assert {c["lang"] for c in casos} == {"pt", "es", "en"}


def test_fatos_exigidos_existem_na_base(casos, facts):
    """Se o gabarito exige um fato que a base não tem, nenhum assistente honesto conseguiria acertar."""
    textos = " ".join(t for f in facts for t in f.texto.values()).lower()
    for c in casos:
        for variacoes in c.get("deve_conter", []):
            assert any(v.lower() in textos for v in variacoes), f"{c['id']}: {variacoes} não está na base"


def test_fontes_exigidas_existem(casos, facts):
    fontes = {f.fonte for f in facts}
    assert {c["fonte"] for c in casos if c.get("fonte")} <= fontes


def test_detector_de_idioma_acerta_todas_as_perguntas(casos):
    erros = [c["id"] for c in casos if detect_language(c["pergunta"]) != c["lang"]]
    assert not erros


def test_mesmo_fato_tem_os_mesmos_numeros_nos_tres_idiomas(facts):
    for f in facts:
        assert numbers_in(f.texto["pt"]) == numbers_in(f.texto["es"]) == numbers_in(f.texto["en"]), f.id
