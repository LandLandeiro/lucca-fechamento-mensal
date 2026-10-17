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
| H14 | Meio centavo no 50% | ROUND_HALF_EVEN no centavo por operação, depois soma | ASSUMO (Lucca, ~22h, D19) | Sem viés sistemático; o rastro fecha exato | Total por operação 39.542,89 × 50% do total do lojista arredondado uma vez 39.542,87 (R$ 0,02 em 7 lojistas) | Era PENDENTE |
| H17 | Spread padrão / em branco | 1,5% sobre a PTAX | CONFIRMADO | Slack Helena 20:48 | Base de R$ 17.682,46 de spread | Era PENDENTE |
| H18 | Spread negativo | Fora da comissão e da nota; vai para `divergencias_taxa` | CONFIRMADO | Slack Helena 20:48 | R$ −1.834,05 de spread | Era PENDENTE |
| H19 | Divergência de spread | Spread aplicado ≠ contratado = divergência no valor cheio | CONFIRMADO | Slack Helena 20:58 | R$ 1.418,88 (Mundo Aberto) | — |
| H20 | Rota Global +0,50 p.p. | Contrato não mudou: é divergência | CONFIRMADO | Slack Helena 20:49 | R$ 1.546,28 | Era PENDENTE |
| H21 | Casa do Estudante | Taxa contratada 0 para MDR e antecipação de 2026-09-01 a 2026-12-31; remessa normal; tudo o que a Orbe cobrou é divergência | CONFIRMADO | Slack Helena 20:49 | R$ 15.391,27 (Σ `valor_taxa` da Casa) | Era PENDENTE; comissão checkout da Casa = 0 → não emite NF |
| H22 | Obrigações de 08/2026: fatos | Folha, ISS, INSS, FGTS e DARFs são de agosto e já estavam provisionados; o repasse da Ponte de 04/09 é o spread de agosto, já registrado como comissão a receber | CONFIRMADO | Slack Helena 20:49 | R$ 411.790,94 de classificação | Era PENDENTE |
| H24 | Obrigações de 08/2026: contas | Baixa de passivo: L15 2.1.04.001; L42 2.1.03.003; L54 2.1.04.002; L55 2.1.04.003; L57 2.1.03.004; L86 2.1.03.001; L87 2.1.03.002; repasse Ponte MRD2026090132 D 1.1.01.002 / C 1.1.03.002 | ASSUMO (Lucca; a Helena devolveu a escolha em 20:49: "me diga como você lançaria") | Fatos de H22 + plano de contas | R$ 411.790,94 de classificação | Separado de H22: antes estava como CONFIRMADO junto com os fatos |
| H25 | Valor da divergência de remessa | (spread % aplicado − contratado) × PTAX × Valor ME, valor cheio; aplicado recalculado de Taxa Cliente e PTAX (fórmula SEI), não da coluna "Spread %" arredondada | ASSUMO (Lucca; Q-G Fox AI 20:52, "É o valor cheio" Helena 20:58) | Mundo Aberto 1.418,88 (pela coluna arredondada: 1.418,85, o número da Q-G) | R$ 0,03 na Mundo Aberto | — |
| H26 | Divergência do spread negativo | Mesma fórmula do valor cheio contra o contratado (ex.: PC-0926-0210 −1.351,87), e não o próprio spread negativo (−687,52) | ASSUMO (a confirmar pelo Lucca, D21) | Regra uniforme de H25 | 4 operações: −3.565,99 pela fórmula × −1.834,05 pelo spread | — |
| H27 | Arredondamento da divergência de remessa | ROUND_HALF_EVEN no centavo por operação (mesma regra da H14) | ASSUMO (a confirmar pelo Lucca, D20) | Extensão da D19 | Centavos | — |
| H23 | Créditos sem origem | L50 C 1.1.09.002 + pendência; L65 C 2.1.01.001 + pendência (motivo da devolução); L92 D 1.1.09.001 (cai no Meridiano em 01/10) | ASSUMO (Lucca; a Helena devolveu a decisão em 20:49) | Slack Helena 20:49 | R$ 319.750,00 de classificação | Era PENDENTE |

## Perguntas ao financeiro

Canal: `#duvidas-hackathon-ai` (o `#tarvo-financeiro` não existe). Quem responde: manuel.freitas (Barte), no papel de **Helena, financeiro da Tarvo**.
Fonte única dos textos: `docs/FINANCEIRO_SLACK.md` (copiado do Slack sem edição). P01–P09 = meu rascunho em `docs/EXPLORACAO.md` §3; P10 e P11 vieram de perguntas de outros times.

| # | Tema | Q | Quem perguntou · horário | Resposta · horário | Situação | O que mudou na solução |
|---|---|---|---|---|---|---|
| P01 | Spread negativo | Q-E (b) | MN AI · 20:30 | Helena · 20:48 | respondida | `remessa.spread_negativo` CONFIRMADO: fora da comissão e da nota, vai para divergências (H18) |
| P02 | Competência de folha, impostos e repasse 08/2026 | Q-F item 3 | Lucca · 20:36 | Helena · 20:49 | respondida | `contabil.obrigacoes_mes_anterior_fatos` CONFIRMADO (H22); `contabil.obrigacoes_mes_anterior_contas` ASSUMO do Lucca (H24) |
| P03 | Base da comissão e NF de checkout e de remessa | Q-A e Q-D | Fox AI · 20:01; MN AI · 20:26 | Helena · 20:05; 20:47 | respondida | `checkout.base_comissao`, `divergencias.tratamento`, `notas.estrutura_nf_checkout`, `ponte.tomador_nf_remessa` CONFIRMADO (H01, H02, H08) |
| P04 | Atlas Idiomas sem contrato | Q-C | Fox AI · 20:16 | Helena · 20:24 | respondida | `cadastro.lojista_sem_contrato_vigente`: não fatura, pendência para o comercial (H05) |
| P05 | ECs sem cadastro | Q-C | Fox AI · 20:16 | Helena · 20:24 | respondida | `cadastro.mapeamento_ec_confirmado` (H04, D07) |
| P06 | Spread "padrão" | Q-E (a) | MN AI · 20:30 | Helena · 20:48 | respondida | `remessa.spread_padrao` = 1,5% sobre a PTAX (H17) |
| P07 | Casa do Estudante, condição especial | Q-F item 2 | Lucca · 20:36 | Helena · 20:49 | respondida | `cadastro.condicao_especial_casa_do_estudante`: taxa 0 em MDR e antecipação, set–dez (H21) |
| P08 | Rota Global +0,50 p.p. desde 12/09 | Q-F item 1 (ver nota de autocorreção) | Lucca · 20:36 | Helena · 20:49 | respondida | `cadastro.renegociacao_rota_global`: contrato não mudou, é divergência (H20) |
| P09 | Créditos sem origem (L50, L65, L92) | Q-F item 4 | Lucca · 20:36 | Helena · 20:49 | respondida (decisão devolvida) | `contabil.creditos_sem_origem` ASSUMO do Lucca (H23) |
| P10 | Estorno de venda de mês anterior | Q-B | MN AI · 20:04 | Helena · 20:06 | respondida | `checkout.estorno` CONFIRMADO (H03) |
| P11 | Valor da divergência de remessa e tolerância | Q-G | Fox AI · 20:52 | Helena · 20:58 | respondida | `remessa.divergencia_spread` valor cheio (H19); tolerância é critério nosso, escrito com motivo (H07) |

**Nota de autocorreção (Q-F, item 1):** na minha pergunta, os rótulos de modalidade estão trocados. 2,49/2,99/3,59% são as faixas **crédito à vista / 2–6x / 7–12x** da planilha (o débito é 1,49%). A resposta não muda: o contrato não mudou. O código compara por modalidade direto na planilha.

### Textos literais (de `docs/FINANCEIRO_SLACK.md`, sem edição)

#### Q-A · Fox AI · 20:01 · base da comissão de checkout

**Pergunta:**
> Ficamos com uma duvida em relacao ao checkout. Para calcular a comissão de checkout de cada lojista, qual valor devemos usar?
> (a) a taxa que a Orbe efetivamente cobrou (valor_taxa do relatório), ou
> (b) o valor bruto × a taxa contratada na planilha?
> Quando as duas diferem, qual delas vai para a nota fiscal? E a diferença é devolvida ao lojista?

**Resposta (20:05):**
> A gente fatura pela taxa *contratada*: valor bruto × taxa da planilha, linha por linha. O `valor_taxa` do relatório é o que a Orbe cobrou, e nem sempre bate com o contrato.
> Na nota fiscal vai a comissão calculada pela taxa contratada.
> Quando a taxa aplicada é diferente da contratada, é divergência. Se a Orbe cobrou a mais, a diferença volta para o lojista e eu cobro a Orbe. Isso eu decido, não vai automático. Preciso ver cada caso com transação e valor.

---

#### Q-B · MN AI · 20:04 · estorno de venda de agosto

**Pergunta:**
> Quando uma venda é estornada, a Tarvo devolve a taxa ao lojista e isso abate a comissão do mês? E se a venda original for de agosto? Ex.: TX88444848 (Oxford Prep, estorno de -R$ 2.193,16 em 01/09 de uma venda de 22/08, taxa -R$ 83,12). Entra em setembro, volta para agosto ou fica fora?

**Resposta (20:06):**
> Sim. Estorno devolve a taxa ao lojista e abate a comissão do mês.
> Venda de agosto estornada em setembro *entra em setembro*, que é o mês do estorno. Agosto já está fechado e não reabro. A taxa usada é a que valia *na data da venda original*.
> No exemplo da Oxford Prep, o estorno de 01/09 reduz a comissão de setembro da Oxford, pela taxa contratada que valia em 22/08.

---

#### Q-C · Fox AI · 20:16 · ECs sem cadastro

**Pergunta:**
> 4 ECs da Orbe não estão na planilha de taxas vigente (290 transações em setembro):
> - 1043300981 HORIZONTE INTERCAMBIO
> - 1043396662 HORIZONTE VIAGENS TURISMO
> - 1076801732 ATLAS IDIOMAS
> - 1038867654 KIWI EXPERIENCE TURISMO
>
> Quais são o CNPJ e as taxas de cada um? Eles correspondem às linhas "Horizonte Viagens", "Novo Horizonte Intercambio" e "Kiwi Experience" da planilha (que estão com o EC em branco)? A Atlas só aparece na aba de 2025: ela ainda é cliente ativa?

**Resposta (20:24):**
> Boa pegada, o EC dessas três está faltando na planilha:
> • *1043300981 HORIZONTE INTERCAMBIO* é a *Novo Horizonte Intercâmbio*, a linha "Novo Horizonte Intercambio".
> • *1043396662 HORIZONTE VIAGENS TURISMO* é a *Horizonte Viagens e Turismo*, a linha "Horizonte Viagens". São duas empresas diferentes.
> • *1038867654 KIWI EXPERIENCE TURISMO* é a *Kiwi Experience*, a linha "Kiwi Experience".
> O CNPJ e as taxas dessas três estão nas linhas delas na aba vigente.
> A *Atlas* na aba de 2025 eu não sabia. Essa planilha passa por várias mãos. O que eu sei é que ela começou a transacionar com a gente em 10/09 e que não tenho contrato assinado dela na vigente. Não sei qual taxa vale. Não fatura a Atlas até o comercial confirmar.

---

#### Q-D · MN AI · 20:26 · notas fiscais

**Pergunta:**
> Pela resposta de vocês, a nota de checkout usa a comissão pela taxa contratada. Qual é a regra fixa para montar as notas todo mês?
> (a) CHECKOUT: uma nota por lojista por mês, com valor = vendas − estornos (pela taxa da venda original)? A ANTECIPACAO (bruto × taxa contratada, ex.: AN88444882 da Canguru) entra na mesma nota ou em nota separada? A REVERSAO ANTECIPACAO (ex.: AN88445114 reverte a AN88444915 da Mundo Aberto) só anula a original?
> (b) Se o saldo do lojista no mês der zero ou negativo por causa de estornos, não emite? O negativo passa para o mês seguinte?
> (c) REMESSA: o e-mail da Ponte fala em "nota fiscal de intermediação" para liberar os 50% do spread. O tomador é sempre a Ponte Câmbio (uma nota pelo total) ou cada lojista?
> (d) Existe texto padrão para a discriminação?

**Resposta (20:47):**
> *(a)* Sim. No checkout é *uma nota por lojista por mês*, no valor da comissão do mês pela taxa contratada, como respondi à Fox AI. Estorno abate pela taxa da venda original, como respondi a vocês antes. A antecipação *entra na mesma nota*, e a reversão só anula a taxa da antecipação que ela reverte.
> *(b)* Zero ou negativo não emite nota. O negativo não passa para o mês seguinte automaticamente. Eu trato com o lojista, então coloca como pendência para mim.
> *(c)* Na remessa, quem paga a gente é a Ponte. É *uma nota só, com a Ponte Câmbio como tomadora*, pelo total da nossa participação no mês. Não tem nota por lojista.
> *(d)* Não temos texto padrão. Algo simples com o serviço e a competência resolve.

---

#### Q-E · MN AI · 20:30 · remessa

**Pergunta:**
> No checkout vocês faturam pela taxa contratada e a diferença vira divergência. A remessa segue a mesma lógica?
> (a) A comissão da Tarvo é 50% do "Spread R$" realizado da Ponte ou 50% de valor × "Spread remessa" contratado na planilha? Quando a Ponte aplica mais que o contratado (ex.: Mundo Aberto, contrato de 1,2%, PC-0926-0011 a ~1,5%), isso é divergência a devolver ao lojista? Quanto vale o "padrão" quando a célula está em branco?
> (b) Para cada situação, a regra é fixa (conta / não conta) ou é decisão sua caso a caso?
>   - spread negativo com "Taxa travada no pedido (D-1)" (ex.: PC-0926-0210)
>   - mesmo Nº de operação repetido, um marcado "reprocessada" (ex.: PC-0926-0162)
>   - status "APROVADO C/ RESSALVA"
>   - contratada num mês e liquidada no seguinte (ex.: PC-0926-0002, liquidada em 01/10): vale a data de contratação ou a de liquidação?

**Resposta (20:48):**
> *(a)* Na remessa a lógica é outra. A nossa comissão é *50% do "Spread R$" realizado*, como está no e-mail da Ponte. A Mundo Aberto negociou 1,20% em julho e a Ponte já devia estar aplicando, então é divergência, e eu contesto com a Ponte. Célula em branco ou "padrão" é 1,5% sobre a PTAX de referência.
> *(b)* Essas eu já sei responder:
> • *Spread negativo:* não aceito. A trava vale 2 horas pelo contrato, e essas passaram do prazo. Fica fora da comissão e da nota, e eu contesto.
> • *Operação repetida:* o número da operação é único.
> • *"Aprovado c/ ressalva":* o status de compliance não muda nada para a gente.
> • *Data:* vale a data de contratação.
> Para o que aparecer fora disso, me digam como vocês tratariam e por quê.

---

#### Q-F · Lucca Landeiro · 20:36 · Rota Global, Casa do Estudante, competência, créditos sem origem

**Pergunta:**
> 1) Rota Global (EC 1074504011): a partir de 12/09 a Orbe passou a cobrar +0,50 p.p. em débito, crédito à vista e 2–6x (2,49/2,99/3,59% → 2,99/3,49/4,09%). A planilha vigente segue com as taxas antigas. Houve reajuste contratual ou é divergência?
>
> 2) Casa do Estudante (EC 1018325654): a linha tem a observação "cliente estratégico - ver c/ comercial" e um comentário "conversar com Diego (comercial) sobre condição especial". Existe condição especial valendo em setembro, ou fatura pela taxa da planilha?
>
> 3) Competência no extrato Aurora: folha, ISS, INSS, FGTS (identificados como 08/2026), IRRF, PIS e COFINS (sem competência no extrato) foram pagos em setembro. Também entrou em setembro o repasse de comissão 08/2026 da Ponte (MRD2026090132, R$ 61.884,12). Lanço tudo na competência agosto ou setembro?
>
> 4) Créditos sem origem clara no Aurora: (a) 16/09 PIX R$ 7.350,00 do CNPJ 38.686.002/0001-80 "SEM IDENTIFICACAO"; (b) 23/09 "DEVOLUCAO PIX - MUNDO ABERTO" +R$ 12.400,00 (enviamos 48.714,59 em 09/09 e 88.746,05 em 24/09); (c) 30/09 transferência de R$ 300.000,00 para o Meridiano sem crédito correspondente no extrato do Meridiano. Vocês sabem a origem desses três, ou ficam como pendência?

**Nota de autocorreção:** no item 1, os rótulos de modalidade estão trocados. 2,49/2,99/3,59% são as faixas **crédito à vista / 2–6x / 7–12x** da planilha (o débito é 1,49%). A resposta não muda: o contrato não mudou. O código compara por modalidade direto na planilha.

**Resposta (20:49):**
> 1. Não mudou nada no contrato da Rota este ano.
> 2. Existe, sim. A Casa do Estudante tem tarifa zerada no checkout de setembro a dezembro, por acordo do comercial para segurar o cliente. Vale para MDR e antecipação. Remessa segue normal. Ninguém avisou a Orbe, então ela cobrou. O que foi cobrado eu devolvo ao lojista, junto com o comercial.
> 3. A folha, o ISS, o INSS, o FGTS e os DARFs são de agosto e já estavam provisionados. O repasse da Ponte de 04/09 é o spread de agosto, que já estava como comissão a receber. Com isso, me diga como você lançaria.
> 4. (a) Não sei de quem é o Pix de R$ 7.350. Não é receita até alguém identificar. (b) A devolução é um Pix de repasse que voltou, e ainda não sei o motivo. (c) A transferência saiu do Aurora em 30/09 e cai no Meridiano em 01/10. O que fazer com cada um é decisão sua.

---

#### Q-G · Fox AI · 20:52 · valor da divergência de remessa e tolerância

**Pergunta:**
> Proposta: divergência = (Spread % aplicado − contratado) × PTAX × valor em moeda estrangeira, valor cheio, porque é o que o lojista pagou a mais. Ex.: PC-0926-0011: (1,5007% − 1,20%) × 4,0315 × 2.438,46 = R$ 29,56. No mês, a Mundo Aberto soma R$ 1.418,85 em 23 operações.
> 1. A divergência é o valor cheio ou só a nossa metade (50%)?
> 2. Nos outros lojistas, o Spread % oscila ±0,002 p.p. em torno do contratado (ex.: 1,4984% a 1,5015% para quem tem 1,5%). Podemos tratar como arredondamento e não reportar divergência abaixo de 0,01 p.p.?

**Resposta (20:58):**
> É o valor cheio. Quem pagou a mais foi a Mundo Aberto, e é o total que eu contesto com a Ponte. A nossa metade é só como a Ponte divide o spread com a gente.
> O critério de tolerância é de vocês. Se ele estiver escrito, com o motivo, eu sigo. O que eu preciso é não receber alarme de centavo, e também não deixar passar diferença de verdade.

## Decisões de escopo

- Faço:
- Não faço (e por quê):

## Origem do código

- Alguns utilitários (parsers de valor/data em pt-BR, OFX, XLSX, camada de IA com saída estruturada e cache) vieram do ensaio de preparação de 16/10 à tarde, registrado em `PROMPTS/`.
