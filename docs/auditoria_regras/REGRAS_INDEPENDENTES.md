# Regras independentes: fechamento Tarvo, setembro/2026 (fase 1)

Auditoria independente, feita **sem abrir nada fora de `C:\Lucca\auditoria-regras`**. Fontes: `case.md`, `data/01` a `data/06`, `FINANCEIRO_SLACK.md` (FS) e `FINANCEIRO_SLACK_tarde.md` (FST). Os horários são de 16/10 (Q-A a Q-M) ou 17/10 (Q-N em diante e FST), em -03.
Os números saem de scripts só de leitura com `Decimal` (ficaram no scratchpad da sessão: `calc.py`, `remessa.py`, `bancos.py`). Base: 01 + 06, com 1.957 linhas Orbe, 233 linhas Ponte e 184 lançamentos bancários.
Tipo: **FATO** = está no dado; **RESPOSTA** = o financeiro (Helena) disse; **PREMISSA** = decisão nossa, sem citação que a sustente.

## 1. Checkout: base, faixas, arredondamento

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R01 | Base da comissão de checkout | `valor_bruto × taxa contratada` da planilha, linha a linha. `valor_taxa` da Orbe não é base | "A gente fatura pela taxa *contratada*: valor bruto × taxa da planilha, linha por linha" (Q-A, 20:05) | RESPOSTA | 1.900 linhas; R$ 203.735,34 líquido (antes da regra de nota) |
| R02 | Faixa da taxa | DEBITO→Débito; CREDITO A VISTA→Créd. à vista; PARCELADO 2–6→2-6x; 7–12→7-12x; PIX→Pix; ANTECIPACAO/REVERSAO→Antecipação | dado: 01 `modalidade`,`qtd_parcelas`; 02 colunas D–I | FATO | 1.957 linhas classificadas |
| R03 | Parcelado >12x | não calcula; vira pendência | "A gente não vende acima de 12x. Se aparecer, é pendência." (Q-X, 11:01) | RESPOSTA | 0 linhas |
| R04 | Vigência da taxa | usar a linha da planilha cuja coluna Vigência cobre a data-base. Bridge: linha 6 "até 14/09/2026" e linha 7 "a partir de 15/09/2026" (só o crédito à vista muda: 2,59→2,19%) | dado: 02 col K/L l.6–7; "A Bridge tem aditivo assinado (2,19% a partir de 15/09)" (Theo, FST 11:37) | FATO + RESPOSTA | Bridge: 57 linhas na tabela antiga, 52 na nova |
| R05 | Data-base da taxa | venda/antecipação: `data_movimento`; estorno/reversão: `data_venda_original` | "A taxa usada é a que valia *na data da venda original*" (Q-B, 20:06); "a faixa sai da própria linha do estorno" (Southlands, FST 11:38) | RESPOSTA | 69 estornos + 9 reversões |
| R06 | Leitura da planilha | percentuais em dois formatos (`0.0149` e `"1,49%"` nas linhas 20–21). CNPJ com 13 dígitos ganha zero à esquerda (Fluente `3229837000103`, Campus `8780784000120`) | dado: 02 l.14, 20, 21, 25 | FATO (formato) / PREMISSA (zero perdido pelo Excel) | Oxford 102 linhas; Sol Nascente 60; 2 CNPJs |
| R07 | Chave lojista ↔ contrato | casar pelo EC Orbe (`cod_estabelecimento`), nunca pelo nome. O nome varia: "Mundo Aberto" tem 3 grafias, EduAbroad 2, Bem-Vindo 2 | dado: 01 `nome_estabelecimento` | FATO (variação) / PREMISSA (chave) | 22 ECs, 0 por nome |
| R08 | Arredondamento | meio-centavo para cima, simétrico no negativo (−0,005 → −0,01), linha a linha e depois soma. A Orbe trunca | "a Orbe trunca os centavos. A gente não trunca. (a) Arredondamento comum… (b) Linha por linha, e depois soma" (Q-H, 21:13) | RESPOSTA | conferido: 1.957/1.957 `valor_taxa` = trunc(bruto×aplicada) |

## 2. Estornos, antecipação, reversão

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R09 | Estorno abate comissão | comissão negativa, na taxa e faixa da venda original | "Estorno devolve a taxa ao lojista e abate a comissão do mês" (Q-B, 20:06) | RESPOSTA | 69 linhas; −R$ 7.851,02 |
| R10 | Estorno de venda de mês anterior | entra em setembro (mês do estorno), na taxa de agosto | "Venda de agosto estornada em setembro *entra em setembro*… Agosto já está fechado e não reabro" (Q-B, 20:06) | RESPOSTA | 9 linhas; −R$ 941,72 |
| R11 | Venda e estorno no mesmo mês | cada linha calcula a própria comissão. Na divergência, as duas linhas entram na lista e a cobrança à Orbe é líquida | "A venda e o estorno se anulam. Cobro da Orbe só o que sobrou de diferença líquida." (Q-N 3, 09:44); "é transação por transação. O estorno… também entra, com valor negativo" (Southlands, FST 11:38) | RESPOSTA | 59 estornos de venda de set (−R$ 6.909,30); 4 pares divergentes da Rota (estornos −R$ 98,44) |
| R12 | Antecipação | `bruto × taxa Antecipação` (2,10%), na mesma nota do lojista | "A antecipação *entra na mesma nota*" (Q-D a, 20:47) | RESPOSTA | 33 linhas; +R$ 22.709,25 (sem Atlas) |
| R13 | Reversão de antecipação | anula só a taxa da antecipação referenciada (`id_referencia`), na taxa da original | "a reversão só anula a taxa da antecipação que ela reverte" (Q-D a, 20:47) | RESPOSTA | 7 linhas; −R$ 6.389,21 (sem Atlas) |

## 3. Isenção e condições especiais

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R14 | Casa do Estudante: tarifa zero | MDR e antecipação = 0 para venda com data de 01/09 a 31/12. Remessa segue normal | "tarifa zerada no checkout de setembro a dezembro… Vale para MDR e antecipação. Remessa segue normal." (Q-F 2, 20:49) | RESPOSTA | 118 de 119 linhas da Casa com comissão 0 |
| R15 | Data-base da isenção | data da venda. O estorno de venda anterior a 01/09 mantém a taxa da venda | "a isenção vale para venda a partir de 01/09, e estorno de venda anterior segue a taxa da venda" (Prime, FST 11:41); "Em 21/08 a isenção ainda não valia" (Q-N 4) | RESPOSTA | TX88445133: −R$ 5,50 → comissão da Casa = **−R$ 5,50** |
| R16 | Data-base da antecipação isenta | a data da própria antecipação (setembro), então fica isenta | não há citação sobre a data-base da antecipação; só "Vale para MDR e antecipação" | PREMISSA | 4 antecipações da Casa; R$ 2.827,56 cobrados |
| R17 | Devolução da Casa ≠ divergência | pendência para Helena e comercial com o total e o detalhe por transação, fora da cobrança à Orbe. É custo da Tarvo | "Não há o que cobrar da Orbe: é devolução ao lojista… Deixem separado" (Q-N 1); "a devolução sai do nosso bolso" (Theo, FST 11:37); "Basta a pendência" (Datarmos, FST 11:49) | RESPOSTA | **R$ 15.396,77** descontados pela Orbe (pela fórmula bruto×taxa: R$ 15.397,42) |
| R18 | Rota Global +0,50 p.p. a partir de 12/09 | é divergência; o contrato não mudou | "Não mudou nada no contrato da Rota este ano." (Q-F 1, 20:49) | RESPOSTA | 87 linhas; R$ 1.546,28 |
| R19 | Bridge a 2,59% de 15 a 18/09 | é divergência de contrato, mesmo com o aviso atrasado à Orbe | "O que decide é o contrato, não o aviso… Isso é divergência: eu contesto com a Orbe" (Theo, FST 11:37) | RESPOSTA | 5 linhas; R$ 29,95 |

## 4. Cadastro: sem contrato, sem EC

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R20 | ECs sem cadastro (3) | 1043300981→Novo Horizonte Intercambio; 1043396662→Horizonte Viagens; 1038867654→Kiwi Experience, com CNPJ e taxa da aba vigente | "o EC dessas três está faltando na planilha" (Q-C, 20:24) | RESPOSTA | 234 linhas; R$ 27.668,42 |
| R21 | Lojista sem contrato (Atlas, EC 1076801732) | não fatura e não calcula divergência. Pendência para o comercial. O repasse continua. CNPJ 39566044000119 da aba "ANTIGO 2025" só para identificar | "Não fatura a Atlas até o comercial confirmar" (Q-C); "o repasse não para" (Q-Y, 11:03); "Só a taxa daquela aba é que não vale" (Prime, FST 11:41) | RESPOSTA | 57 linhas; bruto R$ 262.138,61; a Orbe cobrou R$ 7.876,05; faturado R$ 0 |
| R22 | Atlas: zero × fora do arquivo | escolher uma forma e registrar. Proposta: linha com R$ 0 mais pendência | "Zerada com pendência ou fora do arquivo, as duas formas servem" (Prime, FST 11:41) | RESPOSTA (opção) / PREMISSA (escolha) | texto |
| R23 | Atlas em outubro | quando o comercial confirmar, a taxa vale desde 10/09 e outubro puxa as 57 linhas de setembro | "a taxa vale desde o começo (10/09) e eu faturo setembro junto com outubro" (Q-Q, 09:47) | RESPOSTA | pendência |
| R24 | Quem decide | taxa, condição, cadastro e contrato: comercial. Regra de fechamento e exceções: Helena | "Taxa e condição comercial, quem aprova é o comercial… Regra de como fechar, aprovo eu" (Q-S, 09:49); "Cadastro e contrato quem decide é o comercial" (Q-X 1) | RESPOSTA | `quem_decide` |

## 5. Divergência de taxa (checkout)

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R25 | Definição | taxa aplicada ≠ contratada na faixa e data-base. Centavo de truncamento não é divergência. Tolerância 0 p.p., porque as taxas têm 2 casas | "Divergência é quando a taxa aplicada é diferente da contratada. Diferença de centavo por causa do truncamento da Orbe não é divergência" (Q-H c) | RESPOSTA | 92 linhas (88 vendas + 4 estornos) |
| R26 | Valor | `r2(bruto × (aplicada − contratada))` | "O valor da divergência eu quero como valor bruto × (taxa aplicada − contratada)" (Q-H c) | RESPOSTA | R$ 1.576,23 |
| R27 | Lista | transação por transação, inclusive o estorno de venda divergente (negativo) | Southlands (FST 11:38), citado em R11 | RESPOSTA | 92 linhas |
| R28 | Quem paga | a Orbe, quando cobrou acima do contrato. O lojista é ressarcido. Decisão de Helena, não automática | "Se a Orbe cobrou a mais, a diferença volta para o lojista e eu cobro a Orbe. Isso eu decido, não vai automático." (Q-A, 20:05) | RESPOSTA | Rota R$ 1.546,28 + Bridge R$ 29,95 |
| R29 | Devolver × recuperar | **devolver** = `valor_taxa − comissão contratada` (o que saiu do bolso do lojista). **Recuperar da Orbe** = soma líquida da R26 | "Devolvo o que saiu do bolso do lojista, o que foi descontado de fato. A diferença para a fórmula é centavo" (Lucca, FST 12:50) | RESPOSTA | devolver R$ 1.575,80; recuperar R$ 1.576,23 |
| R30 | Orbe cobrando abaixo | é divergência e Helena decide caso a caso | "Também é divergência e eu decido caso a caso. Não aconteceu em setembro" (Q-N 7) | RESPOSTA | 0 linhas (conferido) |
| R31 | Forma da pendência | uma por contraparte e por lojista, com as transações anexadas (vira rascunho de contestação) | "uma pendência por contraparte e por lojista, com o detalhe das transações anexado" (Q-X 1, 11:01); Q-T 2 | RESPOSTA | Orbe/Rota, Orbe/Bridge, Casa (comercial) |

## 6. Remessa (Ponte Câmbio)

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R32 | Base | 50% do `Spread R$` **realizado** de cada operação, arredondado por operação | "A nossa comissão é *50% do "Spread R$" realizado*" (Q-E a, 20:48); e-mail 03: "participação de 50%… do spread realizado"; "(d) Por operação, com o mesmo arredondamento" (Q-H, 21:13; a pergunta não está copiada) | RESPOSTA + FATO | 228 ops; **R$ 39.543,45** (pela soma: R$ 39.542,88) |
| R33 | Spread contratado | planilha col J. Célula em branco ou "padrão" = 1,5% | "Célula em branco ou "padrão" é 1,5% sobre a PTAX de referência" (Q-E a) | RESPOSTA | Canguru ("padrão"), Kiwi e Ponte Aérea (em branco) |
| R34 | Divergência de spread | o lojista pagou spread diferente do contratado. Valor cheio = (Spread % − contratado) × PTAX × Valor ME. Contesta-se com a Ponte | "A divergência na remessa é quando o lojista paga um spread diferente do contratado" (Q-N 2); "É o valor cheio" (Q-G, 20:58) | RESPOSTA | Mundo Aberto, 23 ops, **R$ 1.418,85** (pelo Spread R$: 1.418,88) |
| R35 | Tolerância da remessa | ignorar \|Spread % − contratado\| ≤ 0,01 p.p. O maior desvio dos outros lojistas é 0,0016 p.p.; o da Mundo Aberto é 0,30 p.p. | "O critério de tolerância é de vocês. Se ele estiver escrito, com o motivo, eu sigo" (Q-G) | PREMISSA autorizada | separa 23 de 228 |
| R36 | Critério Spread % × Spread R$ | usar Spread % (a fórmula da Q-G) | "São três centavos. Escolham um critério e escrevam qual." (Q-X 4) | PREMISSA autorizada | R$ 0,03 |
| R37 | Excesso na nota | a nota sai pelo realizado, com o excesso. Se a Ponte devolver, a metade da Tarvo sai no mês do ajuste. Pendência | "Entra. A nota de setembro sai pelo realizado… Deixar como pendência para mim é o caminho certo." (Q-J, 21:45) | RESPOSTA | metade potencial: R$ 709,43 |
| R38 | Spread negativo | fora da comissão e da nota. Pendência de contestação com **dois** valores: o Spread R$ do relatório e a diferença até o contratado. Não é divergência de lojista; pode ser listado se a natureza ficar marcada | "Spread negativo: não aceito… Fica fora da comissão e da nota" (Q-E b); "o prejuízo é nosso com a Ponte, então é pendência de contestação" (Q-O); "Coloquem os dois na pendência" (Theo, FST 11:37 #3) | RESPOSTA | 4 ops: −R$ 1.834,05 no relatório / −R$ 3.565,98 até o contrato |
| R39 | Operação duplicada | Nº de operação único: conta uma vez e entra na lista para a Ponte corrigir | "o número da operação é único" (Q-E b); "A duplicada vocês contam uma vez… e ela também entra na lista para a Ponte" (Q-L, 22:34) | RESPOSTA | PC-0926-0162 "reprocessada": R$ 821,88 de spread (R$ 410,94 de comissão) excluídos |
| R40 | Data | data de contratação | "*Data:* vale a data de contratação." (Q-E b) | RESPOSTA | 6 ops contratadas em 30/09 e liquidadas em 01/10 entram (R$ 1.039,37) |
| R41 | Status "APROVADO C/ RESSALVA" | não muda nada | "o status de compliance não muda nada para a gente" (Q-E b); e-mail 03 | RESPOSTA + FATO | 16 ops; R$ 2.414,73 |
| R42 | CNPJ fora da planilha | calcula 50% do spread mesmo assim e abre pendência de cadastro | "Não aconteceu em setembro… o tratamento que vocês propuseram é razoável. Registrem como premissa." (Q-P 2) | PREMISSA autorizada | 0 ops (conferido) |
| R43 | Repasse da Ponte | não presumir desconto da contestação. Conferir o TED de 06/10 é pendência de Helena | "Não conte que ela vai descontar nada do repasse. • Conferir o TED quando ele cair é uma pendência boa" (Q-K, 22:33) | RESPOSTA | R$ 39.543,45 a conferir |
| R44 | Ajuste de contestação futuro | linha nova com Spread R$ negativo e "AJUSTE REF PC-…". Abate a nota do mês em que aparece | Desbravadores (FST 11:33) | RESPOSTA | 0 em setembro |

## 7. Notas fiscais

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R45 | Nota de checkout | uma por lojista (CNPJ) no mês: MDR + antecipação − estornos − reversões. Bridge: duas linhas da planilha, mesmo CNPJ, uma nota | "uma nota por lojista por mês" (Q-D a) | RESPOSTA | **20 notas, R$ 203.740,84** |
| R46 | Saldo zero ou negativo | não emite. Pendência para Helena; o negativo não passa para o mês seguinte | "Zero ou negativo não emite nota. O negativo não passa para o mês seguinte automaticamente" (Q-D b) | RESPOSTA | Casa −R$ 5,50 sem nota |
| R47 | Nota da remessa | uma só, tomadora Ponte Câmbio S.A. (CNPJ 75374179000146), pelo total da participação | "*uma nota só, com a Ponte Câmbio como tomadora*" (Q-D c); CNPJ no e-mail 03 | RESPOSTA + FATO | **R$ 39.543,45** |
| R48 | Discriminação | texto simples: serviço e competência | "Algo simples com o serviço e a competência resolve." (Q-D d) | RESPOSTA | 21 notas |
| R49 | Atlas | sem nota | R21 | RESPOSTA | R$ 0 |

## 8. Classificação contábil dos extratos

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R50 | Critério geral | contrapartida do movimento. O que já estava registrado baixa a conta onde estava; o resto vai para a conta da natureza | "Se o valor já estava registrado, o pagamento ou recebimento baixa a conta onde ele estava" (Q-I a, 21:14); Q-X 2 | RESPOSTA | 184 linhas |
| R51 | Folha e tributos de agosto pagos em setembro | baixa do passivo: 2.1.04.001/.002/.003 e 2.1.03.001/.002/.003/.004 | "A folha, o ISS, o INSS, o FGTS e os DARFs são de agosto e já estavam provisionados" (Q-F 3); Q-R 3 "Sempre." | RESPOSTA | 7 linhas Aurora; R$ 349.906,82 |
| R52 | Repasse Ponte 08/2026 (MRD2026090132) | baixa 1.1.03.002, não é receita | "O repasse da Ponte de 04/09 é o spread de agosto, que já estava como comissão a receber" (Q-F 3) | RESPOSTA | R$ 61.884,12 |
| R53 | Despesas sem provisão | despesa do mês: tarifas 4.2.01; condomínio 4.2.02; AWS 4.2.03; Google 4.2.04; contabilidade 4.2.06 | "tarifas, aluguel, cloud, assinaturas e serviços entram direto na despesa do mês" (Q-I b) | RESPOSTA | 8 linhas (6 Aurora + 2 Meridiano); −R$ 79.825,17 |
| R54 | Seguro, IOF, rendimento | 4.2.05; 4.3.01; 3.2.01 | não estão listados na Q-I b; vão pela natureza da conta | PREMISSA | R$ 1.830,44; R$ 48,21; +R$ 3.912,66 |
| R55 | TED da Orbe no Aurora | 1.1.03.001 (baixa de recebível de adquirente) | "Os créditos da Orbe vocês classificam" (Q-M); "Conta por conta eu não valido" (Q-Y) | PREMISSA | 21 linhas; R$ 3.557.246,29 |
| R56 | PIX enviado a lojista (repasse) | 2.1.01.001, inclusive os da Atlas | Q-Y: "o repasse não para"; conta: Q-Y, sem validação | PREMISSA | 45 linhas; −R$ 4.217.867,61 |
| R57 | Meridiano: PIX de lojista e TED à Ponte "LIQ OPERACOES" | 2.1.02.001 (recursos de lojista para remessa) | Q-Y, sem validação | PREMISSA | 85 linhas; saldo líquido +R$ 18.240,00 |
| R58 | Transferências entre contas próprias | 1.1.09.001 | Q-Y, sem validação | PREMISSA | Aurora −R$ 1.450.000 (4); Meridiano +R$ 1.150.000 (3) |
| R59 | Aplicação e resgate CDB | 1.1.02.001 | pela natureza da conta | PREMISSA | 6 linhas; −R$ 115.243,00 |
| R60 | Provisão de setembro | fora do fechamento. Não gerar provisão de folha e impostos de set | "Fica fora do fechamento de vocês… O fechamento de vocês classifica o que passou nos extratos." (Datarmos, FST 11:49) | RESPOSTA | 0 lançamentos |
| R61 | Conciliação Orbe × banco parcela a parcela | fora do escopo | "Conciliar a Orbe contra o banco, parcela por parcela, não é o que eu preciso neste fechamento" (Q-M) | RESPOSTA | 0 |

## 9. Créditos sem origem, competência, alerta, ajustes, falhas de arquivo

| # | regra | como aplicar | fonte | tipo | impacto set/26 |
|---|---|---|---|---|---|
| R62 | PIX R$ 7.350 sem identificação (Aurora L50) | 1.1.09.002, não é receita. Pendência para Helena | "Não sei de quem é o Pix de R$ 7.350. Não é receita até alguém identificar." (Q-F 4a) | RESPOSTA | R$ 7.350,00 |
| R63 | Devolução PIX Mundo Aberto (L65) | 2.1.01.001, com o mesmo critério dos repasses. Pendência sobre o motivo | "A devolução é um Pix de repasse que voltou, e ainda não sei o motivo" (Q-F 4b); "As duas contas fazem sentido. Escolham uma" (Q-R 2) | RESPOSTA + PREMISSA (conta) | +R$ 12.400,00 |
| R64 | Transferência de R$ 300 mil em 30/09 (L92) | 1.1.09.001 em trânsito. Pendência de acompanhamento: crédito no Meridiano em 01/10 | "A transferência saiu do Aurora em 30/09 e cai no Meridiano em 01/10" (Q-F 4c) | RESPOSTA | R$ 300.000,00 |
| R65 | PIX R$ 18.240 da Ponte Aérea (MRD2026090425) | 2.1.02.001: recurso de remessa de outubro. Não é a Ponte Câmbio nem receita | "É a Ponte Aérea mandando dinheiro de uma remessa que ainda não foi feita. A operação sai em outubro." (Q-N 5) | RESPOSTA | R$ 18.240,00 |
| R66 | Competência | Orbe: `data_movimento` em set (01+06). Ponte: data de contratação. Estorno de agosto entra em set. Pagamento de agosto baixa passivo | Q-B, Q-E b, Q-F 3 | RESPOSTA | ver R10, R40, R51 |
| R67 | Alerta de antecipação | sinal só informativo, não muda número. Critério nosso: lojista sem histórico ou sem contrato, com antecipação acumulada maior que as vendas acumuladas na data (pico) | "Coloquem como alerta" (Q-N 6); "O que me preocupa é lojista novo, sem histórico, antecipando alto… O critério é de vocês" (Theo, FST 11:37); Fox (FST 12:50) | RESPOSTA (alerta) / PREMISSA (critério) | 1 alerta: Atlas, pico 15/09, R$ 179.592,82 antecipados × R$ 55.357,50 vendidos (excesso R$ 124.235,32; reversões em 17/09 e 26/09). Pela regra ingênua acenderiam também Oxford, Dublin, Mundo Aberto, Kiwi e Canguru (todos com histórico) |
| R68 | Ajustes tardios (06) | fazem parte de setembro: mesmo formato do 01, processar junto, sem `id_transacao` repetido | "O fechamento entregue às 18h30 precisa considerar esse arquivo." (Org., FST 13:10) | RESPOSTA + FATO | 14 linhas (10 estornos, 3 reversões, 1 venda Kiwi); comissão −R$ 3.304,39; divergência 0 |
| R69 | Arquivo faltando ou layout mudado | validar presença e cabeçalho de cada fonte. Se falhar: fecha o que não depende, marca provisório e diz o que está bloqueado e por quê. Quem libera é Helena; taxa e cadastro, o comercial antes | "Prefiro que a solução avise a que quebre… Fecha o que não depende daquilo, marca o que é provisório e deixa claro o que está bloqueado" (Turma do Barulho, FST 12:31) | RESPOSTA | 0 em set (7 fontes presentes) |

---

## Totais independentes de setembro (01 + 06)

### Notas de checkout por lojista (R01, R45, R46)

| lojista (planilha) | CNPJ | linhas | antecipação líq. | comissão | nota |
|---|---|---|---|---|---|
| Andes Expedições Ltda | 85694108000184 | 41 | 0,00 | 3.819,35 | sim |
| Bagagem Livre Turismo Ltda | 50900987000179 | 74 | 0,00 | 7.703,98 | sim |
| Bem-Vindo Exchange Ltda | 67869675000142 | 76 | 0,00 | 9.259,74 | sim |
| Escola Bridge de Idiomas Ltda (2 linhas de vigência) | 22224579000109 | 109 | 0,00 | 11.769,74 | sim |
| Campus Global Ltda | 08780784000120 | 79 | 0,00 | 9.336,06 | sim |
| Canguru | 53857560000123 | 80 | 2.761,65 | 11.679,43 | sim |
| Casa do Estudante Viagens Ltda | 00520815000100 | 119 | 0,00 | **−5,50** | **não** (pendência) |
| Dublin Hub Intercâmbio Ltda | 68567965000102 | 112 | 2.515,81 | 11.876,37 | sim |
| EduAbroad | 16181276000153 | 102 | 1.757,87 | 11.858,16 | sim |
| Fluente Idiomas Online Ltda | 03229837000103 | 82 | 0,00 | 7.316,07 | sim |
| Horizonte Viagens | 78576234000179 | 75 | 0,00 | 9.014,42 | sim |
| Kiwi Experience | 07752116000126 | 86 | 503,02 | 10.886,22 | sim |
| Lisboa Cursos e Viagens Ltda | 61720397000180 | 76 | 0,00 | 8.470,78 | sim |
| Maple Study Assessoria Educacional Ltda | 34671260000100 | 108 | 1.766,29 | 14.165,77 | sim |
| Mundo Aberto | 17217888000111 | 169 | 1.185,02 | 18.508,09 | sim |
| Novo Horizonte Intercambio | 66564512000199 | 73 | 0,00 | 7.767,78 | sim |
| Oxford Prep Cursos Ltda | 23109187000161 | 102 | 4.704,73 | 13.845,71 | sim |
| Rota Global Intercâmbio Ltda | 95927868000148 | 159 | 1.125,65 | 15.621,27 | sim |
| Sol Nascente Viagens Ltda | 89779285000114 | 60 | 0,00 | 5.898,02 | sim |
| Trilha Jovem Turismo Ltda | 21394880000106 | 67 | 0,00 | 5.628,57 | sim |
| Vela | 20987545000140 | 51 | 0,00 | 9.315,31 | sim |
| Atlas Idiomas (sem contrato) | 39566044000119 | 57 | — | 0,00 | não (pendência comercial) |
| **Total notas de checkout** | | | | **R$ 203.740,84 (20 notas)** | |
| Soma algébrica, com a Casa | | 1.900 | 16.320,04 | R$ 203.735,34 | |

### Demais totais

| total | valor | composição |
|---|---|---|
| Comissão da remessa (nota única para a Ponte) | **R$ 39.543,45** | 228 ops = 233 − 1 duplicata − 4 spreads negativos; 50% por operação |
| Valor a devolver aos lojistas (checkout, pela Tarvo) | **R$ 16.972,57** | divergência de contrato R$ 1.575,80 (Rota 1.545,86 + Bridge 29,94; `valor_taxa` − contratada) + Casa R$ 15.396,77 |
| Valor a recuperar da Orbe | **R$ 1.576,23** | Rota 1.546,28 + Bridge 29,95 (bruto × Δtaxa, líquido dos 4 estornos). Por `valor_taxa`: R$ 1.575,80 |
| Custo para a empresa | **R$ 15.396,77** firme | devolução da Casa (concessão comercial; a Orbe não reembolsa) |
| Contingências (fora do custo firme) | R$ 865,98 / R$ 709,43 / R$ 7.876,05 | a) 50% do spread contratado das 4 ops negativas, se a Ponte não honrar a trava; b) metade da Tarvo no excesso da Mundo Aberto, se a Ponte devolver; c) receita da Atlas diferida (não é custo) |
| Contestação com a Ponte (a lojista e à Tarvo) | R$ 1.418,85 + 4 ops negativas (−1.834,05 / −3.565,98) + duplicata PC-0926-0162 | R34, R38, R39 |

Checagens de fechamento: o saldo do Aurora fecha (612.334,81 − 2.532.423,41 = −1.920.088,60, igual ao extrato). O Spread R$ total da Ponte (78.073,59) = válidas 79.085,76 + duplicata 821,88 − negativas 1.834,05. O líquido do Meridiano em 2.1.02.001 = +18.240,00, exatamente o PIX da Ponte Aérea para outubro.
