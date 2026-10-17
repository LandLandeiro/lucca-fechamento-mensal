# Divergências de regras: fase 1 (independente) × solução da outra equipe

Comparação de `REGRAS_INDEPENDENTES.md` (gravado antes desta leitura) com `C:\Lucca\tarvo-fechamento\regras.yaml` e `saida\`. Só foi lido o que estava autorizado: o yaml, os 7 CSV e os rascunhos. Os arquivos datam de 17/10 13:34, e nada foi editado. O código e o `HIPOTESES.md` deles **não** foram lidos. Onde a regra pode estar no código e não no yaml, o texto diz isso.

**Critério de gravidade.** Mede o efeito sobre a entrega deles se o lado mais bem sustentado prevalecer:
- **alta**: muda um número entregue;
- **média**: muda texto ou pendência, ou cria risco para outubro;
- **baixa**: só documentação.

Quando o lado mais sustentado é o deles, a linha fica com "—" e o erro é da fase 1, registrado no fim.

**Itens "em andamento" que a outra equipe informou estar aplicando:**
- Bridge como divergência de contrato: **já está na saída** (`natureza=contrato_orbe`, rascunho `orbe_escola_bridge`). Só o comentário em `divergencias.natureza.fonte` ainda diz "A Bridge como condicao_nao_informada é leitura nossa" (D15).
- Pares venda e estorno na lista: **já está na saída** (4 pares da Rota com `liquida_com`).
- Provisão fora do fechamento: **já está no yaml e na saída** (`contabil.provisao_do_mes` e nenhum lançamento de provisão).

## 1. Regra a regra

| # | regra (ref. fase 1) | fase 1 | regras.yaml / saída | status | mais sustentado | impacto R$ | gravidade |
|---|---|---|---|---|---|---|---|
| D01 | Base checkout (R01) | bruto × contratada, por linha | `checkout.base_comissao` | igual | — | 0 | — |
| D02 | Faixas e colunas (R02) | 5 faixas + antecipação | `taxas.coluna_por_produto` | igual | — | 0 | — |
| D03 | >12x vira pendência (R03) | Q-X 3 | implícito em `nota_com_transacao_pendente` ("produto sem coluna"), sem citar a Q-X 3 | igual no efeito | nosso (cita a fonte) | 0 (nenhuma linha) | baixa |
| D04 | Vigência da Bridge (R04) | linhas 6/7, col K | o yaml não tem regra própria; a saída aplica 2,59→2,19% a partir de 15/09 (5 linhas, R$ 29,95) | igual na saída | — | 0 | baixa (doc.) |
| D05 | Data-base estorno/reversão (R05) | `data_venda_original` | `checkout.estorno` | igual | — | 0 | — |
| D06 | Leitura da planilha (R06) | `"1,49%"` + zero à esquerda no CNPJ | `casas_decimais_taxa: 4`; a saída tem CNPJ de 14 dígitos (Fluente 03229837000103, Campus 08780784000120). O zero à esquerda não está documentado | igual na saída | — | 0 | baixa (doc.) |
| D07 | Casar pelo EC (R07) | EC, nunca nome | `lojistas_do_extrato`: "pelo EC (nunca por semelhança)" | igual | — | 0 | — |
| D08 | Arredondamento (R08) | half-up simétrico, por linha | `arredondamento_comissao_contratada` + `orbe.arredondamento_valor_taxa: TRUNCAR` | igual | — | 0 | — |
| D09 | Estorno, inclusive de agosto (R09, R10) | abate em set, taxa da venda | `checkout.estorno` | igual | — | 0 | — |
| D10 | Venda e estorno no mesmo mês (R11, R27) | as duas linhas na lista, Orbe pelo líquido | `estorno_de_venda_divergente` (D77); 4 pares | igual (estava em andamento, concluído) | — | 0 | — |
| D11 | Antecipação e reversão (R12, R13) | mesma nota; reversão anula a original | `composicao_comissao` | igual | — | 0 | — |
| D12 | Isenção da Casa (R14–R16) | MDR + antecipação = 0, venda de 01/09 a 31/12; estorno de 21/08 a 1,49% | `condicoes_especiais[casa_do_estudante_2026]`; saída: 118 isentas, TX88445133 = −5,50 | igual. Nosso R16 (data-base da antecipação) estava como PREMISSA; eles marcam CONFIRMADO pela Q-F 2 | deles (Q-F 2 cobre a antecipação) | 0 | — |
| D13 | Casa separada das divergências de contrato (R17) | pendência própria, custo da Tarvo | valor igual (R$ 15.396,77) e `natureza=condicao_nao_informada`, mas a pendência tem `tipo=DIVERGENCIA_CHECKOUT` (o mesmo das de contrato) e as 118 linhas têm `decisao=Helena`, enquanto a pendência diz "Helena + comercial" | diferente (rótulo) | nosso: Q-N 1 "Deixem separado"; Q-F 2 "junto com o comercial" | 0 | média |
| D14 | Rota +0,50 p.p. (R18) | divergência | `renegociacao_rota_global` | igual (87 linhas, R$ 1.546,28) | — | 0 | — |
| D15 | Bridge = contrato (R19) | Theo 11:37 | saída `contrato_orbe`; o comentário do yaml (`natureza.fonte`) está desatualizado | igual / em andamento (doc.) | — | 0 | baixa |
| D16 | 3 ECs sem cadastro (R20) | Q-C | `mapeamento_ec_confirmado` | igual | — | 0 | — |
| D17 | Atlas (R21, R23) | não fatura, pendência, repasse normal, outubro puxa set | `lojista_sem_contrato_vigente`, `discriminacao.CHECKOUT_COMPLEMENTO_ANTERIOR`, `lojistas_do_extrato` (repasse) | igual | — | 0 | — |
| D18 | Atlas zerada × fora do arquivo (R22) | proposta: linha com 0 | fora do `comissoes_por_lojista.csv`; o yaml não registra a escolha (talvez esteja no HIPOTESES, não lido) | diferente (as duas formas permitidas, Prime 11:41) | empate | 0 | baixa |
| D19 | Divergência: definição, valor, lista (R25–R27) | 92 linhas, R$ 1.576,23 | `criterio_checkout`; saída com 92 linhas idênticas, linha a linha | igual | — | 0 | — |
| D20 | Rótulo `direcao` dos estornos | — | os 5 estornos de linha divergente saem como `COBROU_A_MENOS` | só deles | nosso: o estorno de venda cobrada a mais não é "Orbe abaixo do contrato" (Q-N 7: não houve em set) | 0 | média (pode ser lido como alarme falso) |
| D21 | Valor a recuperar da Orbe (R29) | R$ 1.576,23 = Σ bruto×Δtaxa (Q-H c) | R$ 1.575,80 = valor a devolver (D71: "não se cobra mais do que foi descontado"); rascunhos Rota 1.545,86, Bridge 29,94 | diferente | empate: nenhuma citação fixa a fórmula da cobrança. Q-H c define o valor da divergência; a Lucca 12:50 só cobre a devolução. Os dois lados são PREMISSA | R$ 0,43 | média |
| D22 | Valor a devolver (R29) | `valor_taxa` − contratada | `valor_a_devolver` (D71) | igual (R$ 1.575,80 + Casa) | — | 0 | — |
| D23 | Pendência por lojista e rascunho por contraparte (R31) | Q-X 1, Q-T 2 | `pendencia_por_lojista` + `rascunhos/` | igual | — | 0 | — |
| D24 | Texto do rascunho à Orbe | — | "pede o ressarcimento à Orbe no próximo repasse" | só deles | sem fonte: a forma de pagamento da Orbe não foi respondida | 0 | baixa (Helena revisa o rascunho, Q-T 2) |
| D25 | Base da remessa (R32) | 50% Spread R$, por operação | `participacao_tarvo`, `arredondamento_participacao` | igual (R$ 39.543,45; 14/14 lojistas iguais) | — | 0 | — |
| D26 | Spread padrão (R33) | 1,5% | `spread_padrao` | igual | — | 0 | — |
| D27 | Divergência de spread (R34, R36) | Spread %, valor cheio | `formula_divergencia` | igual (23 ops, iguais operação a operação; R$ 1.418,85) | — | 0 | — |
| D28 | Tolerância da remessa (R35) | 0,01 p.p. | 0,005 p.p. | diferente | empate (os dois autorizados pela Q-G; maior ruído 0,0016 p.p.) | 0 | baixa |
| D29 | Metade do excesso da Mundo Aberto (R37) | R$ 709,43 (metade do total) | R$ 709,46 (Σ por operação) | diferente | **deles** (Q-H d: "Por operação, com o mesmo arredondamento") | R$ 0,03 | — (erro da fase 1) |
| D30 | Spread negativo: tratamento (R38) | fora da comissão e da nota; pendência com os 2 valores | `remessa.spread_negativo`, `valor_contestado`; a pendência traz −1.834,05 e −3.565,98 no texto; o rascunho traz os dois; linha em divergências com `natureza=spread_negativo` (Q-O permite) | igual | — | 0 | — |
| D31 | Spread negativo: diferença por operação | `Spread R$ − r2(contratado×PTAX×ME)` | `r2((Spread % − contratado)×PTAX×ME)`: PC-0926-0326 −1.001,30 (nós −1.001,29), PC-0926-0491 −574,90 (nós −574,91); total igual (−3.565,98) | diferente | **deles** (mesma fórmula da D27, critério da Q-X 4) | R$ 0,01 em 2 linhas, 0 no total | — (erro da fase 1) |
| D32 | Duplicata (R39) | conta 1×, lista para a Ponte | `operacao_duplicata` + pendência DUPLICATA R$ 821,88 | igual | — | 0 | — |
| D33 | Data de contratação e status ressalva (R40, R41) | Q-E b | `liquidacao_no_mes_seguinte`, `status_aprovado_com_ressalva` | igual | — | 0 | — |
| D34 | CNPJ fora da planilha (R42) | Q-P 2 | `cnpj_fora_da_planilha` | igual | — | 0 | — |
| D35 | Conferir o TED, sem prever desconto (R43) | Q-K | `conferencia_repasse` | igual | — | 0 | — |
| D36 | Ajuste de contestação da Ponte em outubro (R44) | linha "AJUSTE REF PC-…" com Spread R$ negativo **abate a nota** do mês (Desbravadores 11:33) | sem regra. Pior: `spread_negativo_por_observacao` manda negativo com observação ≠ "Taxa travada" para a pendência SPREAD_NEGATIVO_SEM_TRAVA, **fora da comissão**, e a nota não abate | só nosso | **nosso** (RESPOSTA literal) | 0 em set; em out a nota da Ponte sai maior que o devido | média (risco alto em outubro) |
| D37 | Notas (R45–R49) | 20 checkout + 1 Ponte; Casa sem nota | `estrutura_nf_checkout`, `tomador_nf_remessa`; saída idêntica | igual | — | 0 | — |
| D38 | Nota bloqueada por transação pendente | — | `nota_com_transacao_pendente` (D57): não emite a nota do lojista com transação pendente | só deles | sem fonte direta; Turma 12:31 ("fecha o que não depende… marca o que é provisório") admite as duas leituras | 0 em set | baixa |
| D39 | Classificação (R50–R59) | 24 combinações conta × banco | 184/184 linhas, as mesmas contas e somas | igual | — | 0 | — |
| D40 | Status das regras de conta | TED Orbe, repasse, aporte e transferência = PREMISSA | `aurora.orbe_recebivel` = **CONFIRMADO** citando a Q-M; todas as linhas com `confianca=1.00` | diferente (documentação) | nosso: a Q-M só diz "Os créditos da Orbe vocês classificam", e a Q-Y diz "Conta por conta eu não valido" | 0 | baixa |
| D41 | Provisão de setembro (R60) | fora | `contabil.provisao_do_mes` | igual (estava em andamento, concluído) | — | 0 | — |
| D42 | Créditos sem origem (R62–R64) | 7.350 → 1.1.09.002; 12.400 → 2.1.01.001; 300 mil em trânsito | regras `pix_sem_identificacao`, `devolucao_pix_lojista` e conferência de transferência; 3 pendências | igual | — | 0 | — |
| D43 | PIX de R$ 18.240 da Ponte Aérea (R65) | 2.1.02.001; recurso de remessa de outubro (Q-N 5) | mesma conta + pendência APORTE_SEM_OPERACAO para Helena, com motivo "recurso do lojista sem operação de câmbio". Não cita a Q-N 5 nem dá próximo passo | diferente (pendência) | nosso: Helena já respondeu; acompanhamento só vale "com motivo e próximo passo" (Org. 11:27 #4) | 0 | média |
| D44 | Alerta de antecipação (R67) | Atlas, pico 15/09, R$ 124.235,32 | `alerta_antecipacao` (D66/D73), o mesmo critério e o mesmo valor | igual | — | 0 | — |
| D45 | Ajustes tardios (R68) | parte de set, obrigatório | lido junto (14 linhas no rastro), mas "opcional (se faltar, segue sem aviso)" | diferente | **nosso**: "Prefiro que a solução avise a que quebre sem ninguém perceber" (Turma 12:31) | 0 em set | média |
| D46 | Arquivo faltando ou layout mudado (R69) | validar, fechar o que não depende, marcar provisório | não há regra no yaml (o código não foi lido; pode tratar) | só nosso | nosso (Turma 12:31) | 0 em set | média |
| D47 | `id_transacao` repetido entre 01 e 06 | sem regra específica | nenhuma das linhas conta + pendência (D75, ASSUMO, pergunta sem resposta) | só deles | empate (os dois sem fonte). Risco: se o 06 corrigir uma linha do 01, perde-se receita | 0 em set | baixa |
| D48 | Saldo negativo do Aurora não é pendência | não tratado | `saldo_negativo_aurora` (Q-M) | só deles | deles | 0 | baixa |
| D49 | Conferências (aporte × operação, FIFO de aplicação, 1 dia útil) | não tratado | `conferencias`, `calendario` (ASSUMO) | só deles | controles a mais, sem efeito em número | 0 | baixa |

## 2. Totais: fase 1 × saída deles

| total | fase 1 | saída deles | diferença |
|---|---|---|---|
| Notas de checkout | R$ 203.740,84 (20 notas) | R$ 203.740,84 (20 notas) | 0; os 21 lojistas iguais centavo a centavo, inclusive a Casa com −5,50 |
| Comissão da remessa (nota da Ponte) | R$ 39.543,45 (228 ops) | R$ 39.543,45 (228 ops) | 0; 14/14 lojistas iguais |
| Valor a devolver aos lojistas | R$ 16.972,57 | R$ 16.972,57 (Rota 1.545,86 + Bridge 29,94 + Casa 15.396,77) | 0 |
| Valor a recuperar da Orbe | R$ 1.576,23 | R$ 1.575,80 | **R$ 0,43** (D21) |
| Custo para a empresa | R$ 15.396,77 | R$ 15.396,77 (pendência da Casa: "custo da Tarvo") | 0 |
| Metade do excesso da Mundo Aberto | R$ 709,43 | R$ 709,46 | R$ 0,03 (D29; o certo é o deles) |
| Divergências (linhas, Σ `diferenca_brl`) | 92 / 1.576,23 + Casa 118 + MA 23 / 1.418,85 + 4 neg. / −3.565,98 | 237 linhas, as mesmas somas | 0 no total; 2 linhas a ±0,01 (D31; o certo é o deles) |
| Lançamentos classificados | 184 linhas; Aurora fecha em −1.920.088,60 | 184 linhas, as mesmas contas e somas | 0 |
| Rastro | — | 0 `id_saida` sem rastro; Σ rastro = valor reportado em 100% dos ids | consistente |

## 3. Erros da fase 1 revelados pela comparação

1. **R37** (metade do excesso): o certo é Σ por operação = R$ 709,43 → **709,46** (Q-H d).
2. **Spread negativo por operação**: o certo é aplicar a mesma fórmula da R34 (PC-0926-0326 −1.001,30; PC-0926-0491 −574,90).
3. **R16**: a isenção da antecipação da Casa é RESPOSTA (Q-F 2), e não PREMISSA. A data-base da antecipação continua sem citação.

A fase 1 não foi editada depois desta leitura, para preservar a independência. As correções valem a partir daqui.
