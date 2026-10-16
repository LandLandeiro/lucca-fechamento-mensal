# Exploração do data pack — setembro/2026

> Registrado em 16/10/2026 às 20h25 (exploração feita entre 19h40 e 20h20, sessão de Claude Code registrada em `PROMPTS/`).
> **Conferido de forma independente:** truncamento da Orbe (1.001 linhas só fecham truncando, 0 arredondando) e taxa da Rota Global TX88428676 (4,09% × 3,59%).
> Scripts de leitura usados na exploração ficaram fora do repositório (só leitura, sem regra de negócio).

## 0. Formato real de cada arquivo

| Arquivo | Formato | Linhas que não são dados | Armadilhas de leitura |
|---|---|---|---|
| **01 Orbe** | ASCII, CRLF, `;`, vírgula decimal sem milhar, DD/MM/AAAA | só o cabeçalho (1943 linhas de dados) | antecipação sem modalidade/parcelas/bandeira; estorno/reversão com sinal negativo; `id_transacao` único (prefixos TX e AN) |
| **02 Taxas** | 2 abas; "Taxas vigentes" com cabeçalho na R5, dados R6–R30, nota R32 | R1–R4 (título, "última atualização: 02/09 - Bia", mescla D4:I4); aba "ANTIGO 2025 - nao usar" | % como número (0.0269) **e** como texto ("2,69%", R20–R21); ruído float (Fluente Pix 0.0079000001); CNPJ em 3 formatos, e como **número sem zero à esquerda** (R14, R25); EC vazio (R8, R9 "EC pendente", R28); vigência em texto livre; spread "padrão" em texto; comentário em A13 |
| **03 E-mail** | multipart; corpo quoted-printable UTF-8; anexo `.xlsx` em base64 | aba Operações: título R1–R3, dados R6–R238, totais R240–R241; aba Resumo por moeda | datas como serial Excel; CNPJ com e sem máscara; nome cortado em 20 caracteres; floats binários (72214.46000000001); **o corpo traz regras**: 50% do spread realizado, NF de intermediação, "APROVADO C/ RESSALVA" segue para liquidação, 5 dias úteis para contestar, CNPJ da Ponte |
| **04 Plano** | Latin-1, CRLF, `;` | cabeçalho | só contas ANALITICA com ACEITA_LANCTO=S |
| **05a Aurora** | UTF-8 sem BOM, LF, `;`, `612.334,81` | L1–L7 cabeçalho, L8 SALDO ANTERIOR, L93 vazia, L94 SALDO FINAL, L95 rodapé | lançamentos L9–L92; saldo corrido bate linha a linha; saldo negativo a partir de L30 (fecha −1,92 mi) |
| **05b Meridiano** | OFX SGML; cabeçalho diz USASCII/1252 mas os bytes são Latin-1 ("INTERCÂMBIO") | cabeçalho OFX | 100 STMTTRN, FITID único, ponto decimal com sinal; sem saldo inicial (implícito 204.118,03) |

### Verificações que importam

- **Orbe TRUNCA**: TX88410128, 5.773,57 × 3,79% = 218,818 → 218,81. São 1.001 linhas que só batem com truncamento e 0 que só batem com arredondamento. Arredondar geraria cerca de 1.000 alarmes falsos de R$ 0,01.
- Orbe: `liquido = bruto − taxa` em 100% das linhas.
- Ponte: `Valor R$ = ME × Taxa Cliente`; `Spread R$ = ME × (TC − PTAX)`; `Spread % = (TC − PTAX)/PTAX`. As taxas têm 4 casas, o que gera ruído de até 0,0016 p.p. no spread %. Sem tolerância, isso vira cerca de 200 alarmes falsos (R$ 1,67 de ruído ao centavo).
- **O banco prova as remessas**: cada TED "PONTE CAMBIO SA LIQ" do Meridiano = Σ(Valor R$ + IOF) das operações **contratadas no dia**, ao centavo. A exceção é 22/09: faltam exatamente R$ 55.811,47 = PC-0926-0162 (55.600,19 + IOF 211,28). Os aportes PIX de cada lojista também batem com as operações dele, exceto **Bagagem Livre (−55.811,47)** e **Ponte Aérea (+18.240,00)**.
- Orbe × banco: os repasses e as TEDs Orbe **não** batem com nenhuma janela de líquido. No checkout, extrato só se classifica, não se concilia.
- Os 30 CNPJs da planilha passam no dígito verificador (depois de completar com zero à esquerda). O CNPJ 38686002000180 do PIX sem identificação (Aurora L50) tem DV inválido.
- A bandeira difere entre estorno e venda original: não usar como chave (a taxa não depende de bandeira).

## 1. Mapa: arquivos → entregáveis

| Entregável | De onde vem | Chave de junção / onde falha |
|---|---|---|
| **Comissão CHECKOUT** | Orbe `valor_taxa` de VENDA + ESTORNO + ANTECIPACAO + REVERSAO, por `cod_estabelecimento`. Total líquido R$ 231.880,36 (MDR 207.449,64 + antecipação 24.430,72) | EC Orbe → planilha col. C → CNPJ col. B. **Falha:** 4 ECs sem EC na planilha (1038867654 Kiwi, 1043300981, 1043396662, 1076801732 Atlas). Nomes variam até 3× por EC ("Mundo Aberto", "MUNDO ABERTO INTERC LTDA"): nunca casar por nome |
| **Comissão REMESSA** | Anexo da Ponte `Spread R$` × 50% (corpo do e-mail), por `CNPJ Cliente` | CNPJ normalizado → planilha col. B: casa limpo (14 clientes, todos na planilha) |
| **Divergências** | Checkout: `taxa_aplicada_pct` × planilha D–I pela faixa de `modalidade`/`qtd_parcelas` e vigência (col. K) na **data da venda** (`data_venda_original` no estorno). Remessa: `Spread %` × col. J | Vigência da Bridge em texto (R6/R7); col. J com "padrão" e vazios; contratado também tem que ser truncado |
| **Notas a emitir** | Checkout: tomador = lojista (CNPJ da planilha), valor = comissão. Remessa: tomador = Ponte Câmbio 75374179000146 (assinatura do e-mail), valor = 50% do spread | CNPJ sem zero à esquerda (Fluente, Campus): completar e validar DV |
| **Lançamentos** | Aurora (`L{n}` físico, Data, Lançamento, Valor) e Meridiano (FITID, DTPOSTED, MEMO, TRNAMT) × contas analíticas | O padrão da descrição resolve cerca de 95%. "PONTE AÉREA ESTUDANTIL" (lojista) ≠ "PONTE CAMBIO" (parceiro): armadilha de nome |
| **Pendências** | todos | — |
| **Rastro** | `id_transacao`→`valor_taxa`; `Nº Operação`→50% spread; divergência → `id_transacao` com a diferença; NF → as mesmas linhas da comissão | Meio centavo no 50% (ex.: Maple 4.294,955): o rastro tem que somar exatamente o valor reportado |

## 2. Ambiguidades, por impacto em R$

| # | Tema | Evidência | Classe | Impacto |
|---|---|---|---|---|
| 1 | Pagamentos de agosto: baixa de passivo/recebível (2.1.0x / 1.1.03.002) ou despesa/receita (4.1.01 / 3.1.03)? | Aurora L15, L42, L54, L55, L57, L86, L87; MRD2026090132 "REPASSE COMISSAO 08/2026" | PERGUNTAR | R$ 411.790,94 de classificação |
| 2 | Transferência de 30/09 sem crédito no Meridiano em setembro (as outras 3 têm par) | Aurora L92 | SEI (fato); ASSUMO 1.1.09.001 → pendência | R$ 300.000,00 |
| 3 | Comissão checkout = `valor_taxa` integral (a Orbe não retém custo próprio) | nome do arquivo, conta 3.1.01; não há dado de custo Orbe | ASSUMO | R$ 231.880,36 |
| 4 | NF checkout: tomador = lojista? uma NF por lojista com MDR + antecipação ou separadas? | case.md; plano tem 3.1.01 e 3.1.02 | PERGUNTAR | R$ 231.880,36 (estrutura das NFs) |
| 5 | Operação duplicada | anexo R76/R77 PC-0926-0162 obs "reprocessada"; banco MRD2026090550 e aportes Bagagem | **SEI** (o banco pagou uma vez) | operação R$ 55.600,19; comissão R$ 410,94; NF Ponte; contestar em 5 dias úteis |
| 6 | Mapeamento EC→CNPJ: 1043300981 "HORIZONTE INTERCAMBIO"→Novo Horizonte (padrão 2,39/2,89 = R28); 1043396662→Horizonte Viagens (R8); 1038867654→Kiwi (R9, 2,59) | taxas aplicadas × planilha | ASSUMO (padrão de taxas), confirmar | R$ 27.492,62 de comissão/NF; trocado gera R$ 369 de divergência falsa |
| 7 | Aporte da Ponte Aérea sem operação | MRD2026090425, 18.240,00, "AEREA" sem acento | SEI (fato) → pendência | R$ 18.240,00 |
| 8 | Valor do spread "padrão" | planilha R29 J="padrão", R9 e R16 vazios, nota R32 | PERGUNTAR | R$ 17.682,46 de spread na base da divergência |
| 9 | Casa do Estudante "condição especial" | comentário A13 ("conversar com Diego"), obs R13 | PERGUNTAR | R$ 15.391,27 de comissão |
| 10 | "DEVOLUCAO PIX - MUNDO ABERTO INTERC" +12.400,00 | Aurora L65 | PERGUNTAR | R$ 12.400,00 de classificação |
| 11 | Atlas Idiomas sem contrato vigente; CNPJ só na aba ANTIGO (R8) | 57 linhas Orbe, ex.: TX88413380 a 3,49% | PERGUNTAR | R$ 7.876,05 de comissão/NF; divergência de 0 a R$ 984,17 |
| 12 | PIX recebido sem identificação, CNPJ com DV inválido | Aurora L50 | SEI → 1.1.09.002 + pendência | R$ 7.350,00 |
| 13 | Operações "APROVADO C/ RESSALVA" entram | 16 operações, ex.: R44 | ASSUMO incluir (o e-mail diz que seguem) | R$ 2.414,69 de comissão |
| 14 | Spread negativo: abate, zera ou usa o estimado? | R96, R141, R205, R228 "Taxa travada no pedido (D-1)" | PERGUNTAR | −917,03 a +811,45 (variação de R$ 1.728,48) |
| 15 | Divergência reduz comissão/NF (cobrada × contratada)? | divergências calculadas | PERGUNTAR | R$ 1.576,23 checkout + R$ 1.418,88 remessa |
| 16 | Rota Global +0,50 p.p. em todo crédito a partir de 12/09 | L1056 TX88428676 (4,09% × 3,59%); planilha R10 | SEI contra a planilha; confirmar | R$ 1.546,28 (1.644,72 vendas − 98,44 estornos) |
| 17 | Mundo Aberto spread 1,5% × 1,2% contratado | R10 PC-0926-0011; planilha R15 "negociado em jul/26" | SEI | R$ 1.418,88 (23 operações) |
| 18 | Liquidação em 01/10 entra em setembro | 6 operações, ex.: R6 PC-0926-0002 | ASSUMO incluir (TED paga em 30/09, competência 09) | R$ 1.039,36 de comissão |
| 19 | Estornos de vendas de agosto abatem a comissão de setembro | 9 linhas, ex.: L39 TX88444848 | ASSUMO abater (a Orbe já desconta) | R$ 941,70 |
| 20 | Estorno de venda divergente entra como divergência negativa | 4 linhas Rota, ex.: L1471 | ASSUMO | R$ 98,44 |
| 21 | Bridge: taxa nova 2,19% desde 15/09, Orbe cobrou 2,59% de 15 a 18/09 | L938 TX88428053; planilha R6/R7 | SEI | R$ 29,95 (5 vendas) |
| 22 | Arredondamento do 50% (meio centavo) | ex.: Maple 8.589,91 / 2 | ASSUMO (registrar regra) | < R$ 0,01 por lojista |
| — | Bandeira diferente entre estorno e original (irrelevante para a taxa); reversões de antecipação zeram o par (SEI); Globo Trotter inativo e sem linhas; Nórdica e Ponte Aérea só têm remessa | | SEI | — |

## 3. Perguntas para o `#tarvo-financeiro` (rascunho)

Todas começam com o nome do time.

1. **Spread negativo.** As operações PC-0926-0210, -0326, -0491 e -0545 vieram com spread negativo (total −R$ 1.834,05, obs "Taxa travada no pedido (D-1)"). A participação de 50% da Tarvo abate esse valor, zera essas operações ou usa o "Spread Estimado (D-1)"? *Muda a comissão REMESSA de Ponte Aérea, Canguru, Dublin e Novo Horizonte e a NF da Ponte (de −917,03 a +811,45).*
2. **Regime contábil.** No Aurora, folha 08/2026 (L15), ISS 08 (L42), INSS (L54), FGTS (L55), IRRF (L57), PIS (L86), COFINS (L87); no Meridiano, repasse da comissão 08/2026 da Ponte (MRD2026090132): baixa das contas "a pagar/a recolher/a receber" ou despesa/receita do mês? *Muda a classificação de R$ 411.790,94.*
3. **NF de checkout.** Emitimos uma NF por lojista somando MDR e antecipação, ou uma de cada? O valor é a taxa que a Orbe efetivamente cobrou ou a contratada (hoje R$ 1.576,23 a mais cobrado de Rota Global e Bridge)? *Muda o valor e a quantidade de NFs e a comissão.*
4. **Atlas Idiomas** (EC 1076801732, 57 transações, 3,49% no crédito à vista) não está na aba "Taxas vigentes", só na "ANTIGO 2025 - nao usar" (CNPJ 39.566.044/0001-19). Qual taxa está contratada e esse CNPJ vale? *Muda a NF (R$ 7.876,05) e as divergências (até R$ 984,17).*
5. **ECs sem cadastro.** Confirmam que, na Orbe, EC 1043300981 "HORIZONTE INTERCAMBIO" é a Novo Horizonte Intercâmbio (66.564.512/0001-99), EC 1043396662 é a Horizonte Viagens (78.576.234/0001-79) e EC 1038867654 é a Kiwi (07.752.116/0001-26)? *Muda para qual CNPJ vão R$ 27.492,62 de comissão e NFs.*
6. **Spread "padrão".** Qual o valor do spread padrão (planilha R29 Canguru = "padrão"; R9 Kiwi e R16 Ponte Aérea em branco)? *Define se há divergência sobre R$ 17.682,46 de spread.*
7. **Casa do Estudante.** O comentário em A13 diz "conversar com Diego (comercial) sobre condição especial". Em setembro valia taxa diferente da tabela? *Pode criar divergência sobre R$ 15.391,27.*
8. **Rota Global.** A planilha (atualizada 02/09) diz 2,49/2,99/3,59%. A Orbe cobra +0,50 p.p. desde 12/09 (ex.: TX88428676 a 4,09%). Houve renegociação não registrada? *Confirma ou zera R$ 1.546,28 de divergência.*
9. **Crédito de R$ 12.400,00** "DEVOLUCAO PIX - MUNDO ABERTO INTERC" (Aurora L65): é repasse devolvido, crédito ao lojista ou outra coisa? *Muda a classificação de R$ 12.400,00.*

Não pergunto sobre a duplicata nem sobre as liquidações de outubro: o banco já responde. A duplicata vira pendência para contestar com a Ponte. Ressalva, estornos de agosto e arredondamento vão como ASSUMO no `HIPOTESES.md`.

## 4. Causa raiz dos 8 dias

1. Não existe cadastro único de lojista: cada fonte chama o mesmo cliente por uma chave diferente (EC, CNPJ em 3 formatos, nome cortado ou livre), e todo mês o casamento é refeito no olho.
2. O "contrato" é uma planilha à mão sem histórico (vigência em texto, "padrão" sem valor, comentários, aba antiga, EC pendente). A taxa não é conferida quando a transação acontece, só no fechamento, por isso o erro aparece quando o lojista reclama.
3. Os relatórios dos parceiros entram como verdade sem cruzar com o banco, que provaria a duplicata e o aporte que sobra. As exceções (spread negativo, ressalva, "reprocessada") dependem da memória de uma pessoa.
4. Automatizar o fluxo atual não resolve. O que reduz os 8 dias é a chave única EC↔CNPJ, a tabela de taxas com vigência estruturada e o cruzamento automático parceiro × banco que separa só as exceções para uma pessoa.
