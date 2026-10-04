"""Metas de qualidade (quality gates). Abaixo delas, a avaliação reprova e o CI fica vermelho."""

GATES = {
    # métrica: (comparação, limite)
    "acuracia": (">=", 0.90),  # casos 100% corretos
    "taxa_alucinacao": ("<=", 0.0),  # qualquer invenção reprova
    "idioma_correto": (">=", 0.95),  # responde no idioma do cliente
    "recusa_correta": (">=", 0.90),  # diz "não sei" quando a base não cobre a pergunta
    "recusa_indevida": ("<=", 0.05),  # não se recusa a responder o que está na base
    "citacao_correta": (">=", 0.90),  # cita o documento certo
    "consistencia": (">=", 0.90),  # perguntas com o mesmo sentido trazem os mesmos fatos
}

MAX_PALAVRAS = 80  # respostas de suporte precisam ser curtas
