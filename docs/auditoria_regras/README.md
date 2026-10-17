# Auditoria independente das regras

Resposta ao ponto 2 do Manuel Freitas no Checkpoint 1 ("garanta que a conferência independente testa as regras, não só a conta, porque duas IAs partindo do mesmo `regras.yaml` erram juntas"). Ver `docs/CHECKPOINTS.md`.

Os dois arquivos desta pasta foram copiados sem edição de `C:\Lucca\auditoria-regras` (conferidos byte a byte com `cmp`):

- `REGRAS_INDEPENDENTES.md`: fase 1, as regras e os totais de setembro levantados do zero;
- `DIVERGENCIAS_REGRAS.md`: fase 2, a comparação regra a regra com a nossa solução.

## Como foi feita

1. **Sessão nova de IA, numa pasta separada**, com só quatro coisas: o `case.md`, os arquivos `data/01` a `data/06` e as falas da Helena copiadas do canal (`FINANCEIRO_SLACK.md` e `FINANCEIRO_SLACK_tarde.md`). Ela **não** teve acesso ao `regras.yaml`, ao código, ao `HIPOTESES.md` nem à `saida/`.
2. Ela escreveu cada regra com a fonte e o tipo (FATO = está no dado; RESPOSTA = a Helena disse; PREMISSA = decisão sem citação) e recalculou os totais com `Decimal`, em scripts só de leitura.
3. **Só depois de gravada a fase 1** ela leu o nosso `regras.yaml` e a `saida/` e comparou. A fase 1 não foi editada depois da leitura, para não perder a independência.
4. Gravidade das diferenças: **alta** se o lado mais bem sustentado muda um número entregue; **média** se muda texto ou pendência, ou cria risco para outubro; **baixa** se é só documentação.

## Resultado

Nenhuma diferença alta: a auditoria chegou aos mesmos números que entregamos, centavo a centavo.

| total | auditoria | nossa saída |
|---|---|---|
| Notas a emitir | R$ 243.284,29 (20 de checkout, R$ 203.740,84; 1 da Ponte) | igual |
| Nota da Ponte (remessa) | R$ 39.543,45 | igual, nos 14 lojistas |
| Valor a devolver aos lojistas | R$ 16.972,57 | igual |
| Custo para a Tarvo (Casa) | R$ 15.396,77 | igual |
| Lançamentos classificados | 184, mesmas contas e somas | igual |

Diferenças de centavos que a comparação revelou, todas resolvidas:
- **Valor a recuperar da Orbe:** a auditoria usou a fórmula da Q-H c (R$ 1.576,23) e nós o valor descontado de fato (R$ 1.575,80). Ver D21 na tabela abaixo.
- **Metade do excesso da Mundo Aberto (R$ 0,03):** a auditoria somou antes de arredondar. O certo é o nosso, por operação (Q-H d).
- **Duas linhas de spread negativo (R$ 0,01 cada, total igual):** o certo é o nosso, com a mesma fórmula da divergência.

## O que fizemos com cada diferença média

| # na auditoria | o que ela apontou | o que fizemos |
|---|---|---|
| D13 | A pendência da Casa tinha o mesmo tipo das divergências de contrato; as linhas diziam "Helena", a pendência dizia "Helena + comercial" | **D85**: tipo próprio `DEVOLUCAO_CONCESSAO_COMERCIAL`; as 118 linhas passam a "Helena + comercial" |
| D20 | O estorno de venda cobrada a mais saía como `COBROU_A_MENOS`, o que pode ser lido como a Orbe abaixo do contrato (Q-N 7: não houve) | **D86**: `ESTORNO_DE_VENDA_ACIMA_DO_CONTRATO` e motivo "estorno de venda cobrada acima do contrato" |
| D21 | Valor a recuperar: fórmula da Q-H c × valor descontado (R$ 0,43); nenhuma fala fixa a fórmula da cobrança | **D88**: o rascunho pede o descontado (Rota 1.545,86 / Bridge 29,94) e mostra ao lado a fórmula (1.546,28 / 29,95), com a diferença explicada; a Helena escolhe |
| D36 | Ajuste "AJUSTE REF PC-…" da Ponte em outubro deve abater a nota (Desbravadores 11:33) | Já tratado em parte antes da comparação (**D83**): a linha vira pendência `AJUSTE_PONTE` explícita, e não spread negativo sem trava. O abatimento automático ficou para depois: depende da pergunta dos Desbravadores (12:04) sobre o valor do ajuste, ainda sem resposta |
| D43 | O PIX de R$ 18.240 virava pendência para a Helena, sem citar a Q-N 5 nem dar o próximo passo | **D87**: acompanhamento `ACOMPANHAMENTO_APORTE`, com a fala da Q-N 5 e o próximo passo (conferir a operação no relatório da Ponte de outubro) |
| D45 | Sem o 06, a solução seguia sem aviso | **D89**: aviso informativo "sem arquivo de ajustes tardios da Orbe neste mês" |
| D46 | Arquivo faltando ou layout mudado (a auditoria não leu o código) | Já existia: um arquivo obrigatório que falta ou se repete, ou uma coluna renomeada, para o fechamento com mensagem clara. Faltava o leitor do Aurora, que lia por posição: **D84** (aviso de cabeçalho). Fechar parcialmente sem uma fonte ficou para "com mais tempo" (README) |

Das baixas, corrigimos o comentário desatualizado da Bridge em `divergencias.natureza.fonte` (D15 da auditoria).

