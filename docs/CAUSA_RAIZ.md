# Por que o fechamento é lento e erra

**Em uma frase:** a causa está antes do financeiro: o comercial fecha uma condição sem registro único e sem avisar a Orbe e a Ponte ("Ninguém tem essa função hoje", Helena, Q-T 1); o financeiro só descobre no fechamento, cruzando à mão, e as regras ficam na cabeça de uma pessoa ("Se eu faltar, ninguém sabe essas regras", Q-U).

## O que setembro mostra

Todos os números abaixo saíram do fechamento de setembro (`saida/`), com a linha de origem no `rastro.csv`.

| Caso | O que aconteceu | Quanto | Onde ver |
|---|---|---|---|
| **Casa do Estudante** | O comercial zerou a tarifa de setembro a dezembro para segurar o cliente. A Orbe não soube e cobrou normalmente. Helena: *"Ninguém avisou a Orbe, então ela cobrou. O que foi cobrado eu devolvo ao lojista"* | R$ 15.397,42 cobrados a mais em 116 transações (a devolver: R$ 15.396,77) | `divergencias_taxa.csv`, ex.: `DIV-AN88445802` (contrato 0%, Orbe 2,1%, R$ 1.206,58) |
| **Rota Global** | A partir de 12/09 a Orbe passou a cobrar +0,50 ponto (ex.: 3,59% → 4,09%). Helena: *"Não mudou nada no contrato da Rota este ano."* | R$ 1.546,28 a mais em 79 transações (a devolver e recuperar da Orbe: R$ 1.545,86) | `divergencias_taxa.csv`, ex.: `DIV-TX88440860` |
| **Escola Bridge** | A planilha tem taxa nova (2,19%) a partir de 15/09; a Orbe seguiu cobrando a antiga (2,59%) até 18/09 e só aplica a nova a partir de 23/09. Helena: *"A Bridge foi avisada alguns dias depois de 15/09"* | R$ 29,95 a mais em 5 vendas (a devolver e recuperar da Orbe: R$ 29,94; há aditivo assinado) | `divergencias_taxa.csv`, ex.: `DIV-TX88428053` |
| **Mundo Aberto** (remessa) | Helena: *"A Mundo Aberto negociou 1,20% em julho e a Ponte já devia estar aplicando"*; a Ponte seguiu em ~1,5% | R$ 1.418,85 pagos a mais pelo lojista em 23 operações; a nossa metade, R$ 709,46, fica pendente até a Ponte devolver | `divergencias_taxa.csv`, ex.: `DIV-PC-0926-0011`; `pendencias.csv`: `PEN-CONTESTACAO_PONTE-SPREAD_ACIMA_DO_CONTRATADO-17217888000111` e `PEN-EXCESSO_REMESSA-17217888000111` |
| **Atlas Idiomas** | Transaciona desde 10/09 sem contrato na planilha vigente (só aparece na aba antiga). Helena: *"não tenho contrato assinado dela na vigente. Não sei qual taxa vale. Não fatura a Atlas até o comercial confirmar."* Mesmo assim, a Tarvo já repassou dinheiro a ela | R$ 7.876,05 cobrados pela Orbe em 57 transações, sem nota; repasses de R$ 112.220,15 e R$ 137.081,62 | `pendencias.csv`: `PEN-SEM_CONTRATO_VIGENTE-EC1076801732`; `lancamentos_classificados.csv`: `LAN-AURORA-L34`, `LAN-AURORA-L60` |

**A planilha "passa por várias mãos"** (Helena, 20:24), e isso aparece no próprio arquivo: o código de estabelecimento (EC) em branco para Novo Horizonte, Horizonte Viagens e Kiwi Experience (só a Helena sabia qual EC era de quem); CNPJ sem o zero à esquerda (Fluente, Campus Global); taxa ora como número, ora como texto com o sinal de %; spread escrito "padrão" no lugar do número; uma vigência que não dá para ler (Globo Trotter); e a aba "ANTIGO 2025 - nao usar" no mesmo arquivo, que é o único lugar onde a Atlas aparece.

## O que a Helena contou em 17/10

- **Ninguém avisa o parceiro.** *"Ninguém tem essa função hoje. O comercial fecha e, quando lembra, manda um e-mail para a Orbe ou a Ponte. A Bridge foi avisada alguns dias depois de 15/09, e a Casa do Estudante e a Mundo Aberto não foram avisadas."* (Q-T 1). É a mesma origem dos três maiores casos acima: Casa R$ 15.397,42, Mundo Aberto R$ 1.418,85, Bridge R$ 29,95.
- **Onde vão os 8 dias úteis** (Q-U): comissão de checkout, uns 3 dias, *"Metade é trabalho manual, casando nome com EC e CNPJ. A outra metade é retrabalho, quando a planilha está desatualizada"*; remessa e Ponte, uns 2 dias, *"A maior parte é espera"*; extratos, uns 2 dias, *"Quase tudo manual, linha por linha"*; o último dia, notas e a revisão dela.
- **A regra está numa pessoa** (Q-U): *"Quase tudo que vocês já descobriram aqui no canal estava só na minha cabeça: as condições que o comercial combinou, quem é quem entre os nomes da Orbe e os CNPJs, o que aceito ou contesto da Ponte e o que já estava provisionado. [...] Se eu faltar, ninguém sabe essas regras."*
- **E o que nem regra é** (Q-W): pagar o lojista antes de a Orbe liquidar, usando a conta garantida: *"Isso não está escrito em lugar nenhum e não tem limite. É mais uma coisa que depende de quem está fazendo."*

## Por que o processo de hoje não pega isso

- **A conferência é manual.** Comparar contratado com cobrado exige cruzar a planilha (com vigência, texto e EC faltando) com cada linha do relatório da Orbe e da Ponte. Ninguém faz isso linha a linha, então o fechamento confia no que a Orbe e a Ponte informam.
- **A regra está na cabeça de uma pessoa.** A condição da Casa, o mapeamento dos ECs, a Atlas, a taxa da Mundo Aberto: tudo só foi descoberto perguntando à Helena. Se ela não está, o fechamento sai errado ou trava.
- **Não existe a comparação "contratado × cobrado".** O relatório do parceiro entra como verdade. A diferença só aparece quando o lojista reclama, meses depois.

## O que a solução muda

- **Um cadastro único de regras** (`regras.yaml`): cada regra tem valor, fonte (quem disse, quando) e, quando cabe, vigência. A condição da Casa vale de 01/09 a 31/12; o alias de um lojista vale a partir de 01/10. Quando o financeiro corrigiu o arredondamento, mudou uma linha, não o programa.
- **A comparação automática todo mês:** cada transação é recalculada pela taxa contratada na data da venda, e toda diferença vira uma linha em `divergencias_taxa.csv`, com transação, valor e natureza. Toda divergência de checkout é devolução ao lojista, porque a Orbe liquida o líquido e o lojista já recebeu a menos (Q-U 4); a parte que tem contrato se recupera da Orbe, com ou sem aviso (Rota e Bridge: "O que decide é o contrato, não o aviso", Helena, Q-AA 1). Nada é devolvido ou cobrado sozinho; os rascunhos de contestação (`saida/rascunhos/`) saem prontos para a Helena revisar.
- **Os 8 dias:** casar nome com EC e CNPJ e recalcular a comissão (os 3 dias do checkout) e classificar os extratos linha a linha (2 dias) passam a ser o programa; sobra para as pessoas o que é decisão, em `pendencias.csv`.
- **Pendência com responsável:** o que precisa de alguém vai para `pendencias.csv`, com motivo e quem decide (Helena, comercial, analista). As divergências de checkout entram como uma pendência por lojista (Casa e Bridge com "Helena + comercial"), e a antecipação da Atlas acima do que ela vendeu vira alerta para a Helena e o comercial. Em setembro, 16 pendências.

**O que fica com a Tarvo, em setembro** (valor descontado pela Orbe − comissão contratada, transação por transação):

| | R$ |
|---|---:|
| Devolver aos lojistas (Casa 15.396,77 + Rota 1.545,86 + Bridge 29,94) | 16.972,57 |
| Recuperar da Orbe (Rota 1.545,86 + Bridge 29,94: condição contratada) | 1.575,80 |
| **Custo para a Tarvo: devolver − recuperar** (a Casa: concessão do comercial fora do contrato, "Quem abriu mão da receita fomos nós") | **15.396,77** |

## O que a solução não resolve (precisa de processo)

O programa mostra a divergência todo mês, mas não impede que ela aconteça. Para isso:

1. **Alguém tem a função de avisar o parceiro, no mesmo dia em que o comercial fecha a condição** (hoje "ninguém tem essa função", Q-T 1). O acordo (Casa, Mundo Aberto, Bridge) só vale depois de enviado à Orbe ou à Ponte e confirmado por elas, com cópia para o financeiro, que registra a vigência no cadastro antes da data de início.
2. **A planilha de taxas tem um registro só:** o comercial aprova a taxa e o financeiro registra (Q-S). Campos obrigatórios (EC, CNPJ completo, taxa em número, vigência em data), nenhuma aba antiga no mesmo arquivo e lojista novo só entra com contrato. Lojista que transaciona sem contrato (como a Atlas) é sinalizado na primeira semana, não no fechamento. O mesmo vale para o que hoje não está escrito, como o pagamento antes da liquidação pela conta garantida (Q-W): vira regra com limite, ou não se faz.
3. **A divergência vira cobrança com prazo.** No fechamento, a Helena manda à Orbe e à Ponte a lista de divergências (`divergencias_taxa.csv`, `contestacao_ponte.csv`) dentro do prazo de contestação do parceiro (o e-mail da Ponte pede resposta em até 5 dias úteis), e acompanha a devolução no mês seguinte.
