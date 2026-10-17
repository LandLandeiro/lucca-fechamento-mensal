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
| H07 | Ruído do spread da Ponte | Diferença de spread % abaixo de 0,005 p.p. é ruído | ASSUMO | Taxas da Ponte com 4 casas, ruído até 0,0016 p.p.; a Helena aceitou critério nosso escrito com motivo (Slack Helena 20:58) | ~200 alarmes falsos (R$ 1,67) | Antes estava como SEI; o limiar é escolha minha, aceita pela Helena |
| H08 | Tomador da NF de remessa | 1 nota por mês, tomadora Ponte Câmbio S.A. (75374179000146), valor = total da participação do mês; discriminação: serviço + competência | CONFIRMADO | Slack Helena 20:47 | NF de remessa inteira (~R$ 38,6 mil) | Era ASSUMO (só e-mail); agora com quantidade e discriminação |
| H09 | "APROVADO C/ RESSALVA" | Segue para liquidação (fato do e-mail) e não muda nada na comissão | CONFIRMADO | E-mail Ponte; Slack Helena 20:48 | R$ 2.414,69 de comissão | Era PENDENTE; entra como APROVADO |
| H10 | Arredondamento de bruto × contratada | TRUNCAR no centavo por transação, depois somar; nunca truncar o total. Sem tolerância na divergência de checkout | ASSUMO (Lucca, ~20h55, D09) | A Orbe trunca `valor_taxa` (1.001 só truncamento; 0 só arredondamento; 942 ambos) | Centavos em ~1.900 linhas | Era PENDENTE; desbloqueia o mínimo |
| H15 | Divergência × estorno | Divergência por transação, líquida com os estornos dela (`id_referencia`) no mesmo mês; só listada se o líquido ≠ 0; venda e estorno ficam no rastro com a nota "estornada em <data> por <id>"; estorno parcial ou em mês seguinte: listada | ASSUMO (Lucca, ~20h55, D10) | Caso real: 4 estornos da Rota Global (−R$ 98,44) | Alarme falso em vendas estornadas | Era PENDENTE |
| H16 | Uso de IA | Só na classificação de lançamentos sem regra de texto; contas lançáveis em lista fechada; JSON validado por pydantic; o código confere se a conta existe, é ANALITICA e tem ACEITA_LANCTO=S; o lado (D/C) vem do sinal do movimento, não da natureza da conta; confiança ≥ 0,8, senão pendência; cache por hash da linha | ASSUMO (Lucca, ~20h55, D11; corrigida ~21h, D12) | — | Classificação errada ou não reproduzível | Limiar era PENDENTE; checagem de natureza D/C removida (D12) |
| H11 | Antecipação e reversão na comissão | VENDA + ESTORNO (taxa da venda original) + ANTECIPACAO (mesma regra); REVERSAO ANTECIPACAO só anula a taxa da antecipação referenciada (`id_referencia`) | CONFIRMADO | Slack Helena 20:47; dados: a Orbe aplica 2,10% sobre o `valor_bruto` da linha, truncado (27 só truncamento, 17 ambos, 0 só arredondamento); 6 reversões espelham a referenciada | R$ 24.430,72 de antecipação líquida | Era PENDENTE; desbloqueia o mínimo |
| H12 | Operação duplicada PC-0926-0162 | O número da operação é único: conta uma vez | CONFIRMADO | Slack Helena 20:48; anexo R76/R77; 05b MRD2026090550 | R$ 410,94 de comissão | Era PENDENTE |
| H13 | Liquidação em 01/10 | Competência pela data de contratação | CONFIRMADO | Slack Helena 20:48; anexo 6 operações | R$ 1.039,36 de comissão | Era PENDENTE; as 6 entram em setembro |
| H14 | Meio centavo no 50% | Por operação ou no total do lojista | PENDENTE | — | < R$ 0,01 por lojista | — |
| H17 | Spread padrão / em branco | 1,5% sobre a PTAX | CONFIRMADO | Slack Helena 20:48 | Base de R$ 17.682,46 de spread | Era PENDENTE |
| H18 | Spread negativo | Fora da comissão e da nota; vai para `divergencias_taxa` | CONFIRMADO | Slack Helena 20:48 | R$ −1.834,05 de spread | Era PENDENTE |
| H19 | Divergência de spread | Spread aplicado ≠ contratado = divergência no valor cheio | CONFIRMADO | Slack Helena 20:58 | R$ 1.418,88 (Mundo Aberto) | — |
| H20 | Rota Global +0,50 p.p. | Contrato não mudou: é divergência | CONFIRMADO | Slack Helena 20:49 | R$ 1.546,28 | Era PENDENTE |
| H21 | Casa do Estudante | Taxa contratada 0 para MDR e antecipação de 2026-09-01 a 2026-12-31; remessa normal; tudo o que a Orbe cobrou é divergência | CONFIRMADO | Slack Helena 20:49 | R$ 15.391,27 (Σ `valor_taxa` da Casa) | Era PENDENTE; comissão checkout da Casa = 0 → não emite NF |
| H22 | Pagamentos de obrigações de 08/2026 | Baixa de passivo provisionado (L15, L42, L54, L55, L57, L86, L87); repasse Ponte MRD2026090132 D 1.1.01.002 / C 1.1.03.002 | CONFIRMADO | Slack Helena 20:49 | R$ 411.790,94 de classificação | Era PENDENTE |
| H23 | Créditos sem origem | L50 C 1.1.09.002 + pendência; L65 C 2.1.01.001 + pendência (motivo da devolução); L92 D 1.1.09.001 (cai no Meridiano em 01/10) | ASSUMO (Lucca; a Helena devolveu a decisão em 20:49) | Slack Helena 20:49 | R$ 319.750,00 de classificação | Era PENDENTE |

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
