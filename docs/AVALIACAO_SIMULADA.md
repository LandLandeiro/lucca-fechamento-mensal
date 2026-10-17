# Avaliação simulada da banca (17/10, ~11h)

Gerada por uma sessão NOVA do Claude Code, sem o contexto de quem construiu, com o papel de avaliador sênior da banca, effort xhigh, só leitura (não alterou arquivo nem fez commit).
O prompt está em PROMPTS/. O texto abaixo é a saída da sessão, sem edição.
As correções feitas a partir dela estão no DECISOES e no DIARIO.

---

Avaliação simulada da banca: Tarvo, fechamento de setembro

Não alterei nenhum arquivo nem fiz commit. Rodei tudo num clone limpo no scratchpad.

Resumo

- Números certos. Recalculei os 15 números com scripts meus, sem usar o código da solução, e todos batem no centavo. O rastro fecha em 100% das saídas.
- Onde a nota cai. O risco está em três lugares: a entrega (repositório privado, PROMPTS/ incompleto, README com [preencher]), duas falhas de formato que a correção automática pode pegar, e uma pendência que falta.
- Estimativa de nota. Hoje fica em ~7,1/10. Com a lista das 18h30, sobe para ~8,3.

1. Execução do zero

- Segui o README: clone, venv com Python 3.12, pip install -e . e python -m tarvo --dados data --saida <pasta>.
- O programa terminou em 0,8 s com código de saída 0 e VALIDADOR: OK.
- Os 8 CSVs gerados são idênticos, byte a byte, aos de saida/.
- pytest no clone: 187 passaram em 6,9 s.
- O resumo na tela sai legível no PowerShell. No Git Bash os acentos saem quebrados (Diverg�ncias); é detalhe.

2. Corrigir antes das 18h30 (por impacto na nota)

┌─────┬─────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────┬──────────────┐
│  #  │          O quê          │                                           Evidência                                            │   Critério   │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│     │ O repositório é         │ api.github.com/repos/LandLandeiro/tarvo-fechamento e a página web dão 404; o usuário dá 200; o │              │
│ 1   │ privado. Sem isso, não  │  main está sincronizado com origin. O case exige repositório público.                          │ Todos        │
│     │ há entrega.             │                                                                                                │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│     │ PROMPTS/ tem 1 de 4     │ PROMPTS/README.md:5,6,8 ainda com [link] e [export]. Faltam: a sessão de 17/10 de manhã (E6b   │ Uso de IA    │
│ 2   │ sessões.                │ parte 2, auditoria, checkpoint), a preparação e o ensaio, e a "outra sessão que recalculou do  │ (20%)        │
│     │                         │ zero" (MOMENTOS.md:20-22), sem export e sem script no repositório. O case pede todas.          │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│     │ As divergências de      │ pendencias.csv não tem Casa (15.397,42), Rota (1.546,28) nem Bridge (29,95). A Helena: "Isso   │              │
│ 3   │ checkout não viraram    │ eu decido, não vai automático" (20:05) e "devolvo ao lojista, junto com o comercial" (20:49).  │ Correção     │
│     │ pendência.              │ A remessa virou pendência (CONTESTACAO_PONTE) e o checkout não; a assimetria salta aos olhos.  │ (25%)        │
│     │                         │ Basta uma pendência por lojista; na da Casa, quem decide é "Helena + comercial".               │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│     │ confianca vazia em      │ O case pede um valor de 0 a 1. Um corretor que leia a coluna como float quebra ou zera essas   │              │
│ 4   │ LAN-AURORA-L28 e L69    │ linhas.                                                                                        │ Correção     │
│     │ (HUMANO).               │                                                                                                │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│     │ ref_origem das          │ PC-0926-0162 (R77), DIV-PC-0926-0011, … e mais 20, 23 operações (contestacao_ponte.csv), NF-…, │              │
│ 5   │ pendências em texto     │  COM-…, EC1076801732. Um casamento automático por ref perde todas. Use ids puros e lista       │ Correção     │
│     │ livre: 7 de 11 não são  │ completa, sem prosa e sem "e mais 20".                                                         │              │
│     │ id de linha de origem.  │                                                                                                │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│ 6   │ README com              │ README.md:7 [NOME DO TIME], :45 problema em 2 frases [preencher], :115 Limitações [preencher]. │ Comunicação  │
│     │ placeholders.           │  Limitações é item obrigatório do case; dá para usar a seção 5 abaixo.                         │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│ 7   │ Números velhos nos      │ O pior é a H02 (HIPOTESES.md:22): diz 1.576,23 de divergência de checkout, e a saída tem       │ Hipóteses    │
│     │ documentos (seção 6).   │ 16.973,65. Também: HIPOTESES.md:262-263 ("Faço:" e "Não faço:" vazios).                        │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│     │ Checkpoints sem         │ Não há texto nem hora dos checkpoints no repositório. O DIARIO foi escrito à mão: E5a "21h45"  │              │
│ 8   │ registro, DIARIO fora   │ contra o commit das 21:38, e entradas fora de ordem (achado do revisor de código).             │ Tempo        │
│     │ da hora do git.         │                                                                                                │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│     │ Bug barato: confiança   │ por_ia.py:412 não quantiza e formatos.py:150 levanta erro. O cache é gravado antes, então      │              │
│ 9   │ com 3 casas derruba a   │ quebra toda execução seguinte. A banca roda sem chave; a Helena, em outubro, roda com chave.   │ Outubro      │
│     │ execução com chave.     │                                                                                                │              │
├─────┼─────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────┤
│     │ (Se sobrar tempo) nota  │                                                                                                │ Correção em  │
│ 10  │ emitida com valor       │ Detalhe na seção 5, item 1.                                                                    │ outubro      │
│     │ parcial.                │                                                                                                │              │
└─────┴─────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┴──────────────┘

3. Dizer no pitch (defender, não corrigir)

- A IA foi posta de propósito na EduAbroad.
  - A D35 (DECISOES.md:41) e o MOMENTOS.md registram: a união com os nomes da Orbe resolveria as 7 linhas por regra, e a regra foi restrita para o caso passar pela IA.
  - O nome EDU ABROAD CONSULTORIA está no relatório da Orbe para o mesmo EC, e a aba 2025 tem Edu Abroad Consultoria Ltda com o mesmo CNPJ.
  - Defesa possível: ligar nome de banco a CNPJ é decisão de cadastro, não de cálculo, e precisa de prova independente (a soma da Ponte) mais aprovação. A IA sugere, a soma prova e uma pessoa aprova; isso escala para nomes novos em outubro. E admitir que, em setembro, uma regra resolveria.
- L28 e L69 foram decididas pelo desenvolvedor, não pela Helena. Prepare o porquê.
- 5 pares venda+estorno ficaram fora da lista (H15). Recalculei: 210 linhas divergem, a saída lista 200, e as 10 que faltam se anulam no próprio mês. É defensável; se o gabarito listar por linha, custa cerca de 5% do recall.
- Spread negativo tem três números para o mesmo fato:
  - −3.565,98 em divergencias_taxa;
  - −1.834,05 na pendência;
  - −917,03 de participação da Tarvo.
  - No resumo para o CFO, "remessa, cobrado a menos R$ 3.565,98" dá a entender que há dinheiro a cobrar do lojista. Tenha uma frase pronta.
- L65 (devolução de PIX): foi para 2.1.01.001, mas o plano tem 2.1.01.002 "Devoluções e créditos a lojistas". O raciocínio (o repasse voltou, a obrigação volta) é bom; tenha-o pronto. A linha também sai com confiança 1,00 numa regra marcada ASSUMO e com motivo desconhecido.
- "Auditoria independente, 0 violações" (README.md:27) não prova os números. O scripts/auditar_saida.py confere formato, coerência entre arquivos e existência na fonte; não recalcula nada. Meu recálculo (seção 4) é evidência real, se quiser usá-lo.

4. Correção: 15 números recalculados do zero

Scripts meus, sem importar src/tarvo, usando só as regras do Slack.

┌─────┬─────────────────────────────────────────────────────────────┬───────────────────────────────┬───────────────────────────────────────────┐
│  #  │                           Número                            │             Saída             │                Meu cálculo                │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 1   │ Comissão de checkout total                                  │ 207.039,73                    │ ✓ igual (21 lojistas, todos iguais)       │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 2   │ Mundo Aberto, checkout                                      │ 18.522,09                     │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 3   │ Bridge, checkout (vigência muda em 15/09)                   │ 11.916,02                     │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 4   │ Oxford, checkout (taxa como texto, estorno de agosto)       │ 16.077,90                     │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 5   │ Kiwi, checkout (EC em branco, mapa da Helena)               │ 10.711,41                     │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 6   │ Casa, checkout (tarifa zero + estorno de venda de 21/08)    │ −5,50 → NF_NEGATIVA           │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 7   │ Atlas, pendência                                            │ 7.876,05 em 57 transações     │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 8   │ Divergência de checkout                                     │ 16.973,65 em 200 linhas       │ ✓ (todos os 200 valores iguais linha a    │
│     │                                                             │                               │ linha)                                    │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 9   │ Divergência Casa / Rota / Bridge                            │ 15.397,42 / 1.546,28 / 29,95  │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 10  │ Comissão de remessa                                         │ 39.543,45 em 228 operações    │ ✓ (14 lojistas iguais)                    │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 11  │ Divergência Mundo Aberto / metade                           │ 1.418,85 / 709,46             │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 12  │ Spread negativo: Spread R$ / contra o contrato / 50%        │ −1.834,05 / −3.565,98 /       │ ✓                                         │
│     │                                                             │ −917,03                       │                                           │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 13  │ Notas: 20 de checkout + 1 da Ponte (75374179000146)         │ 207.045,23 + 39.543,45        │ ✓                                         │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 14  │ Aporte sem operação (Ponte Aérea) / PIX da EduAbroad =      │ 18.240,00 / 394.222,69        │ ✓                                         │
│     │ operações                                                   │                               │                                           │
├─────┼─────────────────────────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 15  │ Σ Aurora = saldo final − inicial; Σ Meridiano               │ −2.532.423,41; 1.116.335,23   │ ✓                                         │
└─────┴─────────────────────────────────────────────────────────────┴───────────────────────────────┴───────────────────────────────────────────┘

- Classificação: conferi as 184 contas contra o plano e contra as respostas Q-F, Q-I e Q-M; não achei conta errada.
- Alarme falso: não achei. Na remessa, só a Mundo Aberto sai do contrato (EduAbroad 1,30%, Lisboa 1,60%, Nórdica 1,25% e Novo Horizonte 1,40% batem).
- O que deveria ser pendência e não é: o item 3 da seção 2.

5. Código

1. Alta para outubro: nota com valor parcial.
   - notas.py:77 emite a nota se a comissão for maior que zero, sem olhar se o lojista tem transações em pendência (comissoes.py:171 soma só as resolvidas).
   - O revisor de código reproduziu: com uma célula "a confirmar" na taxa da Rota, a nota sai com 13.353,44 em vez de 15.621,27.
2. Média: o casamento por prefixo aceita nome de uma palavra (cadastro.py:153).
   - "VELA TRANSPORTES" vira repasse para a Vela, e "CANGURU MUDANCAS" para a Canguru, por REGRA e com confiança 1,00, em silêncio.
   - Não há teste negativo.
3. Média: feriados ignorados (conferencias.py:42, a docstring admite).
   - 12/10/2026 cai numa segunda. Uma transferência na sexta 09/10 que cai na terça 13/10 gera duas pendências falsas.
4. Média: spread negativo é sempre "trava vencida" (remessa.py:123). A coluna Observação não é lida.
5. Média: condição especial com o nome fixo condicao_especial_casa_do_estudante (cadastro.py:216).
   - Uma segunda condição especial exige mudar o código.
   - Isso contradiz o README ("a mudança é uma linha no regras.yaml").
6. Baixa-média: uma linha da Orbe de outro mês aborta tudo, sem gerar nenhum CSV (__main__.py:126).
7. O teste de outubro foi feito sob medida. É setembro deslocado em um mês, com a mesma planilha, e test_outubro.py:119 lê o saida/pendencias.csv commitado.
8. Caminhos sem teste: taxa indefinida, mais de uma linha vigente, reversão sem antecipação, operação da Ponte fora da competência, feriado, fornecedor com prefixo de lojista.
9. Manutenção:
   - executar() tem cerca de 200 linhas de cola com regra de negócio dentro (__main__.py:81).
   - Ids de pendência são montados como string em 3 arquivos.
   - PREFIXOS_DERIVADOS é uma lista manual no validador.
   - Σ(Valor R$ + IOF) aparece duplicado em por_ia.py e conferencias.py.

Itens 1 a 5 conferi no código. Os demais vêm do revisor de código, que os reproduziu.

6. Contradições entre documentos e saída

┌─────────────────────────┬────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────────┐
│          Onde           │                        Diz                         │                             Real                              │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ HIPOTESES.md:22 (H02)   │ 1.576,23 checkout + 1.418,88 remessa               │ 16.973,65 e 1.418,85                                          │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ HIPOTESES.md:39 (H19)   │ 1.418,88                                           │ 1.418,85                                                      │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ HIPOTESES.md:33 (H11)   │ "24.430,72 de antecipação líquida"                 │ é a soma do valor_taxa da Orbe com a Atlas; na comissão é     │
│                         │                                                    │ 18.931,47 (37 linhas)                                         │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ HIPOTESES.md:24 / :28   │ 27.492,62 / "~38,6 mil"                            │ 27.493,61 / 39.543,45                                         │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ README.md:109           │ a IA atua em "7 de 184"                            │ a execução manda 5 para a IA; L28 e L69 vêm de                │
│                         │                                                    │ decisoes_humanas                                              │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ HIPOTESES.md:32 e       │ sugestão "PROPOSTA"                                │ sugestoes_regra.csv diz APROVADA                              │
│ console                 │                                                    │                                                               │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ CAUSA_RAIZ.md:15 × H39  │ "Mesmo assim, a Tarvo já repassou dinheiro a ela"  │ a H39 diz que o repasse é devido, e não há pendência          │
│                         │ (tom de problema)                                  │                                                               │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ CAUSA_RAIZ.md:28-29     │ "toda diferença… para a Helena decidir", pendência │ as divergências de checkout não estão em pendencias.csv       │
│                         │  com responsável                                   │                                                               │
├─────────────────────────┼────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ README.md:3-5           │ "o CI garante…"                                    │ com o repositório privado, a banca não vê nem o badge         │
└─────────────────────────┴────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────┘

7. Notas por critério

┌──────────────┬──────┬───────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────┐
│  Critério    │ Nota │                                 Evidência                                 │              O que faz subir               │
│    (peso)    │      │                                                                           │                                            │
├──────────────┼──────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ Correção     │ 8    │ 15/15 batem; rastro 100%; nenhum alarme falso achado                      │ Itens 3, 4 e 5 da seção 2 → 9              │
│ (25)         │      │                                                                           │                                            │
├──────────────┼──────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ Uso de IA    │      │ O transcript da noite mostra direção forte (valores esperados dados antes │ Exportar as sessões; responder a D35 de    │
│ (20)         │ 6    │  do código; erro do git checkout -- pego). Mas falta 3/4 do histórico, e  │ frente → 7,5                               │
│              │      │ a D35 mostra IA "fabricada"                                               │                                            │
├──────────────┼──────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ Causa raiz   │ 8    │ CAUSA_RAIZ.md:3 vai além de automatizar ("o contrato muda e ninguém avisa │ Onde vão os 8 dias úteis e um total do     │
│ (15)         │      │  quem cobra"), com casos em R$ e processo (:35-37)                        │ dinheiro em jogo                           │
├──────────────┼──────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ Hipóteses    │ 7    │ Estrutura excelente (status, fonte, impacto, regras.yaml como espelho     │ Item 7 → 9                                 │
│ (10)         │      │ executável), mas números velhos logo na tabela e escopo vazio             │                                            │
├──────────────┼──────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ Perguntas    │      │ A Q-F (20:36) é ótima: 4 itens, antes de construir, com EC, valores e     │ Colar a Q-K; a Helena atende até 17h30:    │
│ (10)         │ 7    │ datas. Mas foram só 2 perguntas próprias, e o texto da Q-K não foi        │ uma pergunta sobre a H15 (netting) ou a    │
│              │      │ transcrito (HIPOTESES.md:241)                                             │ L65 ainda dá tempo                         │
├──────────────┼──────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ Comunicação  │ 6    │ O resumo na tela é bom para o CFO; o README tem 3 placeholders, um deles  │ Item 6 → 8                                 │
│ (10)         │      │ obrigatório                                                               │                                            │
├──────────────┼──────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ Tempo (10)   │ 7    │ Mínimo às 21:22 do dia 16, alvo às 08:43 do dia 17. Repositório privado e │ Tornar público e registrar os checkpoints  │
│              │      │  checkpoints sem registro                                                 │ → 8                                        │
└──────────────┴──────┴───────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────┘

8. As 5 perguntas mais difíceis da banca

1. "Vocês dizem 'IA só onde há ambiguidade real', mas a D35 desligou o nome da Orbe que resolveria a EduAbroad por regra. A IA errou 2 de 7 e o desenvolvedor decidiu. Isso não é IA de enfeite?"
2. "A Helena disse que decide cada divergência e devolve à Casa com o comercial. Por que os R$ 16.973,65 não estão em pendências, e a remessa está?" (se o item 3 não for feito)
3. "Em outubro a planilha traz 'a confirmar' na taxa da Rota. A Helena recebe uma nota de 13 mil no lugar de 15,6 mil. Isso não é número inventado?"
4. "Spread negativo: 3.565,98, 1.834,05 ou 917,03. Quanto dinheiro está em jogo, e de quem?"
5. "A 'auditoria independente' foi escrita pela mesma IA e não recalcula nada, e a sessão que recalculou não está no repositório. Mostre um número que você verificou fora da IA."

O ponto fraco que mais preocupa é o Uso de IA, que pesa 20%. As sessões que provariam a verificação feita de manhã (auditoria, correção do checkpoint, recálculo independente) não estão no repositório. E o que está documentado sobre a IA no produto (D35) depõe contra. O repositório privado é mais urgente, mas se resolve em um clique.

Arquivos que criei, todos em C:\Users\<usuario>\AppData\Local\Temp\claude\C--Lucca-tarvo-fechamento\2b33409b-838f-4a30-aff1-e0f7c80446a0\scratchpad\meu\:
- recalc_checkout.py
- recalc_remessa.py
- checa_rastro.py

O clone limpo usado na execução está em C:\Users\<usuario>\AppData\Local\Temp\claude\C--Lucca-tarvo-fechamento\2b33409b-838f-4a30-aff1-e0f7c80446a0\scratchpad\clone.

✻ Cogitated for 13m 34s · done 11:15