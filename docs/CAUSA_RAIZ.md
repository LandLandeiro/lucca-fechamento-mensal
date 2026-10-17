# Por que o fechamento é lento e erra

**Em uma frase:** o contrato muda e ninguém avisa quem cobra; e as regras vivem em lugares diferentes (a planilha de taxas, os e-mails dos parceiros, a cabeça da Helena), então ninguém compara, mês a mês, o que foi contratado com o que foi cobrado.

## O que setembro mostra

Todos os números abaixo saíram do fechamento de setembro (`saida/`), com a linha de origem no `rastro.csv`.

| Caso | O que aconteceu | Quanto | Onde ver |
|---|---|---|---|
| **Casa do Estudante** | O comercial zerou a tarifa de setembro a dezembro para segurar o cliente. A Orbe não soube e cobrou normalmente. Helena: *"Ninguém avisou a Orbe, então ela cobrou. O que foi cobrado eu devolvo ao lojista"* | R$ 15.397,42 cobrados a mais em 116 transações | `divergencias_taxa.csv`, ex.: `DIV-AN88445802` (contrato 0%, Orbe 2,1%, R$ 1.206,58) |
| **Rota Global** | A partir de 12/09 a Orbe passou a cobrar +0,50 ponto (ex.: 3,59% → 4,09%). Helena: *"Não mudou nada no contrato da Rota este ano."* | R$ 1.546,28 a mais em 79 transações | `divergencias_taxa.csv`, ex.: `DIV-TX88440860` |
| **Escola Bridge** | A planilha tem taxa nova (2,19%) a partir de 15/09; a Orbe seguiu cobrando a antiga (2,59%) até 18/09 | R$ 29,95 a mais em 5 vendas | `divergencias_taxa.csv`, ex.: `DIV-TX88428053` |
| **Mundo Aberto** (remessa) | Helena: *"A Mundo Aberto negociou 1,20% em julho e a Ponte já devia estar aplicando"*; a Ponte seguiu em ~1,5% | R$ 1.418,85 pagos a mais pelo lojista em 23 operações; a nossa metade, R$ 709,46, fica pendente até a Ponte devolver | `divergencias_taxa.csv`, ex.: `DIV-PC-0926-0011`; `pendencias.csv`: `PEN-CONTESTACAO_PONTE-SPREAD_ACIMA_DO_CONTRATADO-17217888000111` e `PEN-EXCESSO_REMESSA-17217888000111` |
| **Atlas Idiomas** | Transaciona desde 10/09 sem contrato na planilha vigente (só aparece na aba antiga). Helena: *"não tenho contrato assinado dela na vigente. Não sei qual taxa vale. Não fatura a Atlas até o comercial confirmar."* Mesmo assim, a Tarvo já repassou dinheiro a ela | R$ 7.876,05 cobrados pela Orbe em 57 transações, sem nota; repasses de R$ 112.220,15 e R$ 137.081,62 | `pendencias.csv`: `PEN-SEM_CONTRATO_VIGENTE-EC1076801732`; `lancamentos_classificados.csv`: `LAN-AURORA-L34`, `LAN-AURORA-L60` |

**A planilha "passa por várias mãos"** (Helena, 20:24), e isso aparece no próprio arquivo: o código de estabelecimento (EC) em branco para Novo Horizonte, Horizonte Viagens e Kiwi Experience (só a Helena sabia qual EC era de quem); CNPJ sem o zero à esquerda (Fluente, Campus Global); taxa ora como número, ora como texto com o sinal de %; spread escrito "padrão" no lugar do número; uma vigência que não dá para ler (Globo Trotter); e a aba "ANTIGO 2025 - nao usar" no mesmo arquivo, que é o único lugar onde a Atlas aparece.

## Por que o processo de hoje não pega isso

- **A conferência é manual.** Comparar contratado com cobrado exige cruzar a planilha (com vigência, texto e EC faltando) com cada linha do relatório da Orbe e da Ponte. Ninguém faz isso linha a linha, então o fechamento confia no que a Orbe e a Ponte informam.
- **A regra está na cabeça de uma pessoa.** A condição da Casa, o mapeamento dos ECs, a Atlas, a taxa da Mundo Aberto: tudo só foi descoberto perguntando à Helena. Se ela não está, o fechamento sai errado ou trava.
- **Não existe a comparação "contratado × cobrado".** O relatório do parceiro entra como verdade. A diferença só aparece quando o lojista reclama, meses depois.

## O que a solução muda

- **Um cadastro único de regras** (`regras.yaml`): cada regra tem valor, fonte (quem disse, quando) e, quando cabe, vigência. A condição da Casa vale de 01/09 a 31/12; o alias de um lojista vale a partir de 01/10. Quando o financeiro corrigiu o arredondamento, mudou uma linha, não o programa.
- **A comparação automática todo mês:** cada transação é recalculada pela taxa contratada na data da venda, e toda diferença vira uma linha em `divergencias_taxa.csv`, com transação e valor, para a Helena decidir. Nada é devolvido ou cobrado sozinho.
- **Pendência com responsável:** o que precisa de alguém vai para `pendencias.csv`, com motivo e quem decide (Helena, comercial, analista). As divergências de checkout entram como uma pendência por lojista (Casa com "Helena + comercial"). Em setembro, 14 pendências.

## O que a solução não resolve (precisa de processo)

O programa mostra a divergência todo mês, mas não impede que ela aconteça. Para isso:

1. **Quando o comercial fecha uma condição, o parceiro fica sabendo no mesmo dia.** O acordo (Casa, Mundo Aberto, Bridge) só vale depois de enviado à Orbe ou à Ponte e confirmado por elas, com cópia para o financeiro, que registra a vigência no cadastro antes da data de início.
2. **A planilha de taxas tem um dono só: o financeiro.** Campos obrigatórios (EC, CNPJ completo, taxa em número, vigência em data), nenhuma aba antiga no mesmo arquivo e lojista novo só entra com contrato. Lojista que transaciona sem contrato (como a Atlas) é sinalizado na primeira semana, não no fechamento.
3. **A divergência vira cobrança com prazo.** No fechamento, a Helena manda à Orbe e à Ponte a lista de divergências (`divergencias_taxa.csv`, `contestacao_ponte.csv`) dentro do prazo de contestação do parceiro (o e-mail da Ponte pede resposta em até 5 dias úteis), e acompanha a devolução no mês seguinte.
