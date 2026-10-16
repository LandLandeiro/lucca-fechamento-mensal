# Hipóteses, premissas e perguntas

Convenção: **SEI** = está nos dados · **ASSUMO** = premissa minha, sem confirmação · **CONFIRMADO** = o financeiro respondeu · **PENDENTE** = ninguém decidiu ainda (o cálculo dependente vira pendência).
Espelho executável: `regras.yaml` (mesmo status, mesma fonte). Evidências: `docs/EXPLORACAO.md`.

## Premissas

| # | Tema | Premissa | Status | Base (arquivo/linha ou resposta) | Impacto se estiver errada | O que mudou |
|---|---|---|---|---|---|---|
| H01 | Base da comissão checkout | Comissão = bruto × taxa **contratada**, por transação (não o `valor_taxa` cobrado pela Orbe) | CONFIRMADO | Slack Helena 20:05 | Toda a comissão checkout (Σ `valor_taxa` = R$ 231.880,36) | Antes eu assumia Σ `valor_taxa`. Agora a comissão sai da taxa contratada e a diferença vai para divergências |
| H02 | Tratamento da divergência | Taxa cobrada ≠ contratada é divergência listada com transação e valor; nunca devolução automática | CONFIRMADO | Slack Helena 20:05 ("Isso eu decido, não vai automático") | R$ 1.576,23 checkout + R$ 1.418,88 remessa | Divergência não gera devolução nem ajuste de nota; vai para `divergencias_taxa.csv` e a decisão é da Helena |
| H03 | Estorno | Estorno abate a comissão no mês do estorno, pela taxa contratada vigente na data da venda original; agosto não reabre | CONFIRMADO | Slack Helena 20:06 | R$ 941,70 (9 estornos de vendas de agosto) | Estornos de agosto entram em setembro, com a taxa contratada da data da venda original |
| H04 | EC sem cadastro | 1043300981 → "Novo Horizonte Intercambio"; 1043396662 → "Horizonte Viagens" (empresas diferentes); 1038867654 → "Kiwi Experience" | CONFIRMADO | Slack Helena 20:24 | R$ 27.492,62 de comissão/NF | Vínculo EC→linha da planilha vira dado em `regras.yaml` (D07), sem semelhança de nome |
| H05 | Atlas Idiomas (EC 1076801732) | Não faturar até o comercial confirmar → pendência | CONFIRMADO | Slack Helena 20:24 ("Não fatura a Atlas até o comercial confirmar") | R$ 7.876,05 (Σ `valor_taxa` Atlas) | Atlas sai de notas; vira pendência com quem decide = comercial |
| H06 | Arredondamento da Orbe | A Orbe trunca `valor_taxa` em 2 casas | SEI | 01_orbe: 1.001 linhas só fecham truncando, 0 arredondando | ~1.000 alarmes falsos de R$ 0,01 | — |
| H07 | Ruído do spread da Ponte | Diferença de spread % abaixo de 0,005 p.p. é ruído | ASSUMO | Taxas da Ponte com 4 casas, ruído até 0,0016 p.p. | ~200 alarmes falsos (R$ 1,67) | Antes estava como SEI; o limiar é escolha minha |
| H08 | Tomador da NF de remessa | Ponte Câmbio S.A., CNPJ 75374179000146 | ASSUMO | E-mail Ponte: "mediante recebimento da nota fiscal de intermediação" | NF de remessa inteira (~R$ 38,6 mil) | Antes estava como SEI |
| H09 | "APROVADO C/ RESSALVA" | Seguem para liquidação (fato). Entrar na comissão ainda é decisão | SEI (fato) · PENDENTE (regra) | E-mail Ponte | R$ 2.414,69 de comissão | — |
| H10 | Arredondamento de bruto × contratada | Não definido em 20:05 | PENDENTE | — | Centavos em ~1.900 linhas | Lacuna aberta pela resposta de 20:05 |
| H11 | Antecipação e reversão na comissão | Não citadas em 20:05/20:06 | PENDENTE | — | R$ 24.430,72 de antecipação líquida | — |
| H12 | Operação duplicada PC-0926-0162 | Contar uma vez (o banco pagou uma vez) | PENDENTE | Anexo R76/R77; 05b MRD2026090550 | R$ 410,94 de comissão | — |
| H13 | Liquidação em 01/10 | Entra em setembro (TED paga em 30/09) | PENDENTE | Anexo 6 operações; 05b MRD2026090688 | R$ 1.039,36 de comissão | — |
| H14 | Meio centavo no 50% | Por operação ou no total do lojista | PENDENTE | — | < R$ 0,01 por lojista | — |

## Perguntas ao financeiro

Canal: `#duvidas-hackathon-ai` (o `#tarvo-financeiro` não existe). Outros times já perguntaram parte das minhas; as respostas são públicas.
Numeração P01–P09 = rascunho em `docs/EXPLORACAO.md` §3.

| # | Tema | Situação | Quem perguntou · horário | Pergunta (literal) | Resposta (literal) | O que mudou na solução |
|---|---|---|---|---|---|---|
| P01 | Spread negativo | **aguardando** | pergunta do time MN AI · 20:30 (spread) | [colar do Slack] | — | `remessa.spread_negativo` segue PENDENTE |
| P02 | Competência de folha, impostos e repasse 08/2026 | **minha** · aguardando | Lucca · 20:36 | [colar do Slack] | — | `contabil.pagamento_de_obrigacao_do_mes_anterior` PENDENTE |
| P03 | Base da comissão e NF checkout | **respondida em parte** (base e divergência); estrutura da NF **aguardando** | [time a preencher] · 20:05; MN AI · 20:26 (notas) | [colar do Slack] | Helena 20:05: [colar resposta completa]. Trecho: "Isso eu decido, não vai automático" | H01, H02 → CONFIRMADO; `notas.estrutura_nf_checkout` PENDENTE |
| P04 | Atlas Idiomas sem contrato | **respondida** | [time a preencher] · 20:24 | [colar do Slack] | Helena 20:24: "Não fatura a Atlas até o comercial confirmar" [completar] | H05 → CONFIRMADO; Atlas vira pendência |
| P05 | ECs sem cadastro | **respondida** | [time a preencher] · 20:24 | [colar do Slack] | Helena 20:24: [colar resposta completa] | H04 → CONFIRMADO; `cadastro.mapeamento_ec_confirmado` |
| P06 | Spread "padrão" | **aguardando** | pergunta do time MN AI · 20:30 (spread) | [colar do Slack] | — | `remessa.spread_padrao` segue PENDENTE |
| P07 | Casa do Estudante, condição especial | **minha** · aguardando | Lucca · 20:36 | [colar do Slack] | — | `cadastro.condicao_especial_casa_do_estudante` PENDENTE |
| P08 | Rota Global +0,50 p.p. desde 12/09 | **minha** · aguardando | Lucca · 20:36 | [colar do Slack] | — | `cadastro.renegociacao_rota_global` PENDENTE |
| P09 | Créditos sem origem (PIX 7.350 L50, devolução Mundo Aberto 12.400 L65, transferência 300k L92) | **minha** · aguardando | Lucca · 20:36 | [colar do Slack] | — | `contabil.creditos_sem_origem` PENDENTE |
| P10 | Estorno de venda de mês anterior | **respondida** (não estava no meu rascunho) | [time a preencher] · 20:06 | [colar do Slack] | Helena 20:06: [colar resposta completa] | H03 → CONFIRMADO; `checkout.estorno` |

## Decisões de escopo

- Faço:
- Não faço (e por quê):

## Origem do código

- Alguns utilitários (parsers de valor/data em pt-BR, OFX, XLSX, camada de IA com saída estruturada e cache) vieram do ensaio de preparação de 16/10 à tarde, registrado em `PROMPTS/`.
