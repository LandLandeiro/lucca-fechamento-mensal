# Plano — fechamento de setembro/2026 da Tarvo

> Documento vivo. Escrito em 16/10 às 20h, antes de qualquer código. Atualizado nos checkpoints.
> Autor: Lucca Rocha Landeiro. Planejado com apoio de IA (sessão registrada em `PROMPTS/`).

---

## 1. Objetivo em uma frase

Fechar setembro/2026 da Tarvo com **números certos e rastreáveis até a linha de origem**, deixando para uma pessoa só o que de fato exige julgamento — e de um jeito que rode igual em outubro.

## 2. Onde estão os pontos (e o que isso muda no plano)

| Dimensão | Peso | O que fazemos para pontuar |
|---|---|---|
| **Correção dos números** | 25% | Regra de negócio confirmada antes de calcular; `Decimal` em tudo; validador automático (soma do rastro = total); **na dúvida, pendência — nunca alarme falso** |
| **Uso de IA** | 20% | Histórico mostra eu decidindo: plano antes do código, perguntas minhas, conferência manual de amostras, correções registradas em `MOMENTOS.md` quando a IA errar |
| **Causa raiz** | 15% | Explicar *por que* o fechamento leva 8 dias e erra (seção 4), e mostrar que a solução ataca a causa, não só o sintoma |
| **Hipóteses** | 10% | `HIPOTESES.md` com cada premissa marcada SEI / ASSUMO / CONFIRMADO, com fonte |
| **Perguntar antes de construir** | 10% | Perguntas específicas, com linha de origem e impacto em R$, feitas hoje (20h30–22h30) |
| **Raciocínio e comunicação** | 10% | Este plano; checkpoints claros; README e pitch em linguagem de financeiro |
| **Tempo e pontualidade** | 10% | Chegar 7h50; checkpoints no horário; push às 18h15; escopo que cabe no dia |

**O que NÃO vale ponto** (texto do case): capricho visual, elegância de código, escolha de ferramenta, quantidade de funcionalidades. Mockup não conta.

**Regra de ouro do case:** *"É melhor entregar o nível mínimo certo do que o nível extra com números que não fecham."*

## 3. Escopo por nível

| Nível | Entrega | Quando |
|---|---|---|
| **Mínimo** | `comissoes_por_lojista.csv` (só CHECKOUT) + `rastro.csv` correspondente + validador | Hoje até ~0h; ajustado amanhã até 11h |
| **Alvo** | + comissão REMESSA, `divergencias_taxa.csv`, `notas_a_emitir.csv`, `lancamentos_classificados.csv` | Amanhã 11h–15h30 |
| **Extra** | + `pendencias.csv` completo com motivo e quem decide; rastro de 100% dos números; roda em outubro sem mudar código | Amanhã 15h30–17h |
| **Bônus** (só se o extra estiver certo) | Tela simples (Streamlit) lendo `saida/` para a analista | Depois das 16h30, se sobrar |

### Fica de fora (e por quê)

- **Interface elaborada / app web** — não pontua; vira no máximo um visualizador da saída.
- **Banco de dados** — entrada é arquivo, saída é arquivo; 2 mil linhas cabem em memória.
- **Integração com Slack, e-mail, ERP, bancos** — fora do tempo; a solução lê os arquivos como chegam.
- **Casamento de nomes por semelhança** — o case aponta como erro clássico; lojista só se liga por EC ou CNPJ. Sem chave → pendência.
- **IA decidindo regra de negócio ou fazendo conta** — regra vem do financeiro; conta é código.
- **Emissão real de nota fiscal** — geramos a lista do que emitir.

## 4. Causa raiz (hipótese inicial, revisar após a exploração)

O fechamento leva 8 dias úteis e erra porque:

1. **Não existe uma chave comum entre as fontes.** O mesmo lojista aparece com nomes diferentes e CNPJ em formatos diferentes (com máscara, sem máscara, sem zero inicial).
2. **A regra de negócio mora na cabeça de uma pessoa.** A planilha tem "padrão", "ver linha de baixo", "ver c/ comercial"; nada disso é executável.
3. **A planilha de taxas é mantida à mão**, com formatos misturados, renegociação no meio do mês e uma aba antiga que "não é para usar".
4. **Cada fonte chega num formato** (portal, e-mail com anexo, CSV de banco com cabeçalho, OFX), e a conferência é feita fonte por fonte.
5. **Não há rastro**: um total não aponta para as linhas que o compõem, então ninguém consegue auditar sem refazer.

**Como a solução ataca isso:** chave única por CNPJ/EC; regras num arquivo legível (`regras.yaml`) com a origem de cada uma; leitores que aceitam os formatos como vêm; rastro por linha; pendências explícitas para o que exige uma pessoa.

## 5. Arquitetura

```
data/  (exatamente como chegou)
  │
  ├─ 1. LEITORES ............ um por fonte; todo registro nasce com ref_origem
  │                           (id_transacao · Nº Operação · L<linha> no Aurora · FITID no Meridiano)
  ├─ 2. CADASTRO ............ lojistas por CNPJ (14 dígitos) e EC; taxas com vigência
  ├─ 3. REGRAS .............. regras.yaml: cada regra com status (CONFIRMADO/ASSUMO) e fonte
  ├─ 4. CÁLCULOS ............ comissões · divergências · notas  (determinístico, sem IA)
  ├─ 5. CLASSIFICAÇÃO ....... extratos: regra → IA nas sobras (com confiança) → pessoa
  ├─ 6. PENDÊNCIAS .......... tudo que é ambíguo, com motivo e quem decide
  └─ 7. SAÍDA + VALIDADOR ... 6 CSVs no formato fixo + checagem automática
```

### Princípios

- **Regra de negócio é dado, não código.** Resposta do financeiro muda o `regras.yaml`, não o programa.
- **Dinheiro em `Decimal`**, arredondamento explícito e igual ao da fonte (a confirmar: arredonda ou trunca).
- **Chave, nunca semelhança.** Lojista = CNPJ ou EC. Sem chave confiável → pendência.
- **Todo número tem rastro**, desde a leitura. O validador recusa total que não fecha.
- **IA só onde há ambiguidade real**, com `metodo=IA` e `confianca`; abaixo do limiar vira `HUMANO` + pendência.
- **Rodar em outubro**: nenhum valor de setembro fixo no código; período e arquivos detectados pela entrada.

### Complexidade

Cada fonte é lida uma vez; toda junção é busca em dicionário (O(1)). Total **O(n)** no tamanho da entrada — o mínimo possível, porque toda linha precisa ser lida. Duplicidades detectadas com `set` (O(1) por consulta). Rastro e validador também O(n): auditabilidade sem custo de desempenho.

## 6. Stack

| Item | Escolha | Por quê |
|---|---|---|
| Linguagem | Python 3.12 | `email` lê o .eml nativo; `decimal` exato; ecossistema de dados |
| Planilhas | `openpyxl` | lê células mistas (número e texto) sem converter |
| CSV | `csv` (padrão) | controle total de encoding e separador |
| Regras | `PyYAML` | legível pelo financeiro |
| IA | `anthropic` (SDK Python) + `pydantic` | saída estruturada validada; chave só no `.env.local` |
| Testes | `pytest` | casos conferidos à mão |
| Tela (bônus) | `streamlit` | visualizador da saída em ~30 min |

Comando único: `python -m tarvo --dados data --saida saida`

## 7. Lógica por entregável

> As regras de negócio exatas ficam em `HIPOTESES.md` e `regras.yaml`. Aqui está o *como*, não o *qual regra*.

### 7.1 Comissão por lojista (`comissoes_por_lojista.csv`)

- **CHECKOUT:** para cada linha da Orbe, identificar o lojista pelo EC → cadastro; compor a comissão segundo a regra confirmada (quais tipos de lançamento entram — venda, estorno, antecipação, reversão — e com qual sinal). Somar por (CNPJ, CHECKOUT). Cada linha da Orbe que compõe o total vai para o rastro.
- **REMESSA:** extrair o anexo do e-mail da Ponte; para cada operação, aplicar a regra de participação no spread (o e-mail cita 50% — confirmar base e tratamento de duplicadas e spread negativo). Somar por (CNPJ, REMESSA).
- `id_saida` sugerido: `COM-<cnpj>-<CHECKOUT|REMESSA>`.

### 7.2 Divergências de taxa (`divergencias_taxa.csv`)

- Para cada transação: taxa aplicada (Orbe) × taxa contratada vigente (planilha), pela modalidade e faixa de parcelas, na data que a regra disser (venda ou movimento — perguntar).
- `diferenca_brl` calculada com o mesmo arredondamento da Orbe. Só reporta diferença real (≥ R$ 0,01 depois do arredondamento correto) — **alarme falso conta contra**.
- Remessa: spread aplicado × contratado (vazio/"padrão" → regra a confirmar).
- `id_saida`: `DIV-<ref_origem>`.

### 7.3 Notas a emitir (`notas_a_emitir.csv`)

- Uma linha por tomador e linha de negócio, com valor e discriminação.
- Quem é o tomador em cada linha (lojista? Ponte?) — **perguntar**. O e-mail da Ponte cita "nota fiscal de intermediação".
- `id_saida`: `NF-<cnpj_tomador>-<linha>`.

### 7.4 Lançamentos classificados (`lancamentos_classificados.csv`)

- Toda linha dos dois extratos (Aurora: `L<n>` da linha física; Meridiano: `FITID`) recebe uma conta **analítica** do plano de contas (`ACEITA_LANCTO = S`).
- Ordem: **REGRA** (padrões de descrição/CNPJ, confiança 1) → **IA** nas sobras (confiança informada) → **HUMANO** abaixo do limiar, com pendência.
- Linhas que não são lançamento (saldo anterior, cabeçalhos) ficam fora, documentadas.

### 7.5 Pendências (`pendencias.csv`)

Tudo que exige uma pessoa: lojista sem EC/CNPJ confiável, taxa ambígua ("padrão", vigência), operação duplicada, spread negativo, lançamento sem classificação segura, lojista inativo com movimento. Cada uma com `motivo` e `quem_decide` (financeiro, comercial, fiscal, contabilidade).

### 7.6 Rastro (`rastro.csv`)

Uma linha por (número de saída, linha de origem que o compõe). **A soma de `valor` por `id_saida` tem que bater com o número reportado.** O validador checa isso para todos os arquivos.

## 8. Arquivos de controle

| Arquivo | Para quê | Quem atualiza |
|---|---|---|
| `docs/PLANO.md` | este plano | eu, nos checkpoints |
| `docs/STATUS.md` | painel: nível atual, checklist por entregável, números atuais, próximo passo | Claude Code, ao fim de cada etapa |
| `docs/DIARIO.md` | log cronológico: hora, etapa, o que foi feito, como foi verificado, commit | Claude Code, ao fim de cada etapa |
| `docs/DECISOES.md` | decisões técnicas: alternativa considerada e motivo | Claude Code, quando houver decisão; eu reviso |
| `HIPOTESES.md` | premissas e perguntas ao financeiro (exigido) | eu |
| `PROMPTS/` + `MOMENTOS.md` | histórico de IA (exigido) | eu, no fim |
| `regras.yaml` | regras de negócio executáveis, com status e fonte | eu decido; Claude Code edita |

## 9. Etapas e cronograma

| # | Quando | Etapa | Pronto quando |
|---|---|---|---|
| E0 | 16/10 20h | Estrutura, CLAUDE.md, controles, Python | `python -m tarvo --help` roda; commit |
| E1 | 20h30–22h30 | **Perguntas ao financeiro** + leitores (Orbe, taxas) e cadastro | perguntas postadas; leitores com testes |
| E2 | 22h30–0h | **Mínimo**: comissão CHECKOUT + rastro + validador | CSV gerado; validador passa; 2 lojistas conferidos à mão |
| — | 0h | dormir | |
| E3 | 17/10 9h30–11h | Ajustar mínimo às respostas; perguntar o que faltou | `STATUS.md` atualizado |
| ✓ | **até 11h** | **Checkpoint 1** no thread: o que ataco, hipóteses principais, o que fica de fora | postado |
| E4 | 11h–12h30 | Comissão REMESSA (e-mail da Ponte) | validador passa |
| E5 | 13h–14h | Divergências de taxa | amostra conferida à mão; zero alarme falso conhecido |
| E6 | 14h–15h | Notas a emitir + lançamentos classificados (regra + IA) | todas as linhas dos extratos classificadas ou pendentes |
| ✓ | **até 15h30** | **Checkpoint 2**: o que funciona, o que mudou | postado |
| E7 | 15h30–17h | Pendências completas; rastro 100%; rodar com novos dados se chegarem | validador passa em tudo |
| — | **17h** | **congela features** | |
| E8 | 17h–18h15 | README, HIPOTESES, PROMPTS + MOMENTOS, conferência final | push 18h15 |
| E9 | 18h30–19h | Pitch | link enviado até 19h |

Atenção: **novos dados podem chegar durante o dia** (`#hackathon-avisos`). Como a solução roda com um comando, basta colocar o arquivo e rodar de novo.

## 10. Como verifico o que a IA entrega

1. **Teste antes da correção** para todo bug encontrado.
2. **Conferência manual** de 2–3 lojistas por entregável (no Excel, linha por linha) contra a saída.
3. **Validador** em toda execução: formato, CNPJ com 14 dígitos, datas ISO, soma do rastro.
4. **Auditoria só leitura** depois do alvo (outra sessão, sem alterar código).
5. Todo erro relevante da IA vai para `PROMPTS/MOMENTOS.md`.

## 11. Riscos

| Risco | Mitigação |
|---|---|
| Regra assumida errada | Perguntar hoje; premissa explícita; trocar em `regras.yaml` sem mexer no código |
| Arredondamento diferente da Orbe gera alarmes falsos | Descobrir o critério nos dados antes de calcular divergência |
| Lojista sem chave confiável | Pendência, nunca semelhança de nome |
| Tempo | Mínimo certo antes de tudo; corte pela ordem: bônus → extra → classificação por IA (fica só regra + humano) |
| Notebook emprestado / ambiente | Push a cada etapa; repositório no GitHub desde o início |
