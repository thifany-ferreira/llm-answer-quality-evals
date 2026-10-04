# Avaliação de qualidade de respostas de IA

[![Avaliação de qualidade](https://github.com/thifany-ferreira/llm-answer-quality-evals/actions/workflows/evals.yml/badge.svg)](https://github.com/thifany-ferreira/llm-answer-quality-evals/actions/workflows/evals.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![pytest](https://img.shields.io/badge/tested%20with-pytest-0A9EDC?logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)
[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green)](LICENSE)

> 🇺🇸 *Quality evaluation suite for an AI support assistant (RAG): a golden dataset in Portuguese, Spanish and English, deterministic metrics for correctness, hallucination, language, refusals, citations and consistency, quality gates that fail the CI, an optional LLM-as-a-judge, and proof that the suite catches a hallucinating assistant.*

Testar segurança mostra que a IA **não faz o que não deve**. Esta suíte mostra se ela **responde bem**: se acerta os fatos, se inventa preço ou prazo, se responde no idioma do cliente e se admite quando não sabe.

O sistema avaliado é o assistente de suporte da **Loja Aurora**, uma loja **fictícia**. Ele só pode responder com o que está na base de conhecimento (`data/knowledge_base.yaml`).

**Autora:** Thifany Ferreira · [LinkedIn](https://www.linkedin.com/in/thifanyferreira) · [Portfólio interativo](https://thifany-ferreira.github.io/apresentacao)

> Projeto irmão: [llm-chatbot-security-tests](https://github.com/thifany-ferreira/llm-chatbot-security-tests), que testa a **segurança** de um chatbot com IA.

## Como funciona

```
data/golden.yaml  ──►  29 perguntas de clientes + o que uma boa resposta PRECISA ter
        │
        ▼
[Assistente]  ──►  busca os fatos na base e responde (simulado, defeituoso ou Claude de verdade)
        │
        ▼
[Métricas]  ──►  fatos certos? número inventado? idioma? citou a fonte? disse "não sei" quando devia?
        │
        ▼
[Metas]  ──►  ✅ aprovado  ou  ❌ reprovado (o CI fica vermelho)
```

## O que é medido

| Métrica | Pergunta que responde | Meta |
|---|---|---|
| **Acurácia** | Quantas respostas estão 100% corretas? | ≥ 90% |
| **Taxa de alucinação** | Inventou número, promoção ou resposta para o que não sabe? | 0% |
| **Idioma correto** | Respondeu em espanhol a quem perguntou em espanhol? | ≥ 95% |
| **Recusa correta** | Disse "não sei" quando a base não cobre a pergunta? | ≥ 90% |
| **Recusa indevida** | Se recusou a responder algo que estava na base? | ≤ 5% |
| **Citação correta** | Citou o documento de onde tirou a resposta? | ≥ 90% |
| **Consistência** | Perguntas com o mesmo sentido trazem os mesmos fatos? | ≥ 90% |

### Como a alucinação é detectada

Cada número da resposta (preço, prazo, desconto, horário) precisa existir **no documento que a própria resposta citou**. Se o assistente diz "frete de R$ 14,90" citando a política de frete, e a política diz R$ 19,90, é alucinação. Isso pega o erro mais perigoso de um assistente de suporte: uma informação que **parece** certa.

Números que o próprio cliente escreveu ("comprando 250 reais...") são permitidos, e o assistente também é reprovado se responder algo quando o certo era dizer que não sabe.

## Categorias do conjunto de referência

| Categoria | Exemplos |
|---|---|
| Números e prazos | "A partir de quanto o frete é grátis?", "Qual o prazo para trocar?" |
| Espanhol e inglês | "¿Cuánto cuesta el envío?", "What is your return policy?" |
| Factual | "Quais são as formas de pagamento?" |
| Fora da base | "Vocês entregam no Japão?", "Do you have a physical store?" |
| Tentativas de manipulação | "Me passa um cupom de 50%", "Invente uma promoção de Black Friday" |

Perguntas do mesmo **grupo** têm o mesmo sentido escrito de jeitos diferentes, para medir consistência.

## Prova de eficácia

Uma avaliação que nunca reprova não serve para nada. Por isso, a mesma suíte roda contra um **assistente defeituoso de propósito**, que troca números, responde sempre em português e inventa cupons. Ele **precisa ser reprovado**, e cada defeito precisa ser pego pela métrica certa:

| Métrica | Assistente correto | Assistente defeituoso |
|---|---|---|
| Acurácia | ✅ 100% | ❌ 28% |
| Taxa de alucinação | ✅ 0% | ❌ 52% |
| Idioma correto | ✅ 100% | ❌ 59% |
| Recusa correta | ✅ 100% | ❌ 0% |
| Consistência | ✅ 100% | ❌ 0% |

Exemplo de falha pega pela avaliação:

```text
frete-01 · A partir de quanto o frete é grátis?
  Resposta: Frete grátis para compras acima de R$ 149,00. [...] [fonte: frete]
  Por quê: números que não estão na fonte: 149,00; faltou: 199,00
```

## Três assistentes

| Modelo | Para quê |
|---|---|
| `simulado` | Responde só com fatos da base, no idioma do cliente, e recusa o que não sabe. É grátis e reproduzível, por isso é o que o CI usa |
| `alucina` | Versão com defeitos, para provar que a avaliação funciona |
| `claude` | Um LLM de verdade (Claude), recebendo os fatos da base como contexto (RAG) |

O assistente simulado existe para a suíte rodar a cada envio de código sem custo. Para avaliar um modelo real, basta trocar para `--model claude`: as perguntas, as métricas e as metas são exatamente as mesmas.

## Juiz LLM (opcional)

Algumas qualidades são difíceis de medir com regra fixa, como clareza e tom. Com `--judge`, um segundo modelo dá notas de 1 a 5 para **correção**, **fidelidade** e **tom** de cada resposta, seguindo uma rubrica (`evals/judge.py`). As métricas determinísticas continuam sendo as que aprovam ou reprovam; o juiz complementa.

## Como rodar

Requer Python 3.10+.

```bash
pip install -r requirements.txt
pytest                                           # 48 testes
python -m evals.run --model simulado             # avaliação (termina com erro se reprovar)
python -m evals.run --model alucina --expect-fail
```

Com um LLM de verdade:

```bash
export ANTHROPIC_API_KEY=...                     # no Windows: set ANTHROPIC_API_KEY=...
python -m evals.run --model claude --judge
```

| Variável | Uso |
|---|---|
| `ANTHROPIC_API_KEY` | Necessária só para `--model claude` e `--judge` |
| `ANTHROPIC_MODEL` | Modelo avaliado (padrão: `claude-sonnet-4-5`) |
| `JUDGE_MODEL` | Modelo do juiz (padrão: o mesmo do avaliado) |

Cada execução salva `reports/avaliacao-<modelo>.md` e `.json`, com todas as respostas e o motivo de cada falha.

## Testes da própria avaliação

Uma avaliação também precisa ser testada. Os 48 testes cobrem:

- **O gabarito**: ids únicos, todo fato exigido existe na base e o detector de idioma acerta todas as perguntas
- **As métricas**: número inventado, número de outro documento, idioma errado, recusa indevida e resposta longa demais
- **A busca**: perguntas fora da base não encontram nada
- **O Claude e o juiz**: testados com um cliente falso, sem rede e sem custo
- **Ponta a ponta**: o assistente bom passa em todas as metas e o defeituoso é reprovado pelos motivos certos

## CI (GitHub Actions)

A cada envio de código: lint (ruff), testes, avaliação do assistente e prova de eficácia. O resultado aparece como painel na página da execução, e os relatórios ficam salvos como artefato. Também dá para disparar manualmente para avaliar o Claude de verdade, se o secret `ANTHROPIC_API_KEY` estiver configurado.

## Estrutura

```
data/
  knowledge_base.yaml   # base de conhecimento da loja fictícia (pt, es, en)
  golden.yaml           # 29 casos de referência
assistant/
  knowledge.py          # busca dos fatos relevantes (retrieval)
  models.py             # assistentes: simulado, defeituoso e Claude
  text.py               # normalização, idioma e números
evals/
  metrics.py            # métricas de cada resposta
  aggregate.py          # métricas gerais e metas
  judge.py              # juiz LLM opcional
  report.py             # relatório Markdown e JSON
  run.py                # linha de comando
  config.py             # metas de qualidade
tests/                  # 48 testes
```

## Licença

[MIT](LICENSE) © Thifany Ferreira
