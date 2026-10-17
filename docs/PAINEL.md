# Painel do fechamento (`saida/painel.html`)

```powershell
python -m tarvo --dados data --saida saida      # o fechamento gera o painel no fim, depois do validador
python -m tarvo.painel --saida saida            # só o painel, sobre uma saída já gerada (padrões: --dados data --regras regras.yaml --hipoteses HIPOTESES.md)
```

O resultado é um arquivo único, `saida/painel.html`, com HTML, CSS e JS puro inline, sem framework e sem build. Abre com duplo clique, sem servidor. Ele lê só o que o fechamento já gerou: `saida/*.csv`, `rastro.csv` e `regras.yaml`. Do `data/` lê duas coisas: o sha256 de cada arquivo, que identifica a versão, e o `valor_taxa` da Orbe (de todo arquivo da Orbe que o rastro cita: o relatório do mês e os ajustes tardios do 06), para a coluna "pela taxa aplicada". O painel não calcula regra nova: cada número exibido é uma soma de linhas da saída, feita em `Decimal`.

Código: `src/tarvo/painel/` (`__init__.py` monta tudo, `estilo.css` e `app.js` entram inline, `__main__.py` é a CLI). Testes: `tests/test_painel.py`.

## As quatro telas e a pergunta da Helena que cada uma responde

| Tela | Âncora | Pergunta | O que mostra |
|---|---|---|---|
| Visão geral | `#visao` | "Quanto eu faturo, e o que está parado esperando por mim?" | "R$ X a faturar em N notas" (de `notas_a_emitir.csv`); o dinheiro que depende de uma decisão, agrupado pelo destino; alertas `ALERTA_*`, se houver; premissas ASSUMO do `regras.yaml` com fonte e motivo, mais a contagem por status; links para cada CSV e para `saida/rascunhos/`; rodapé com o sha256 dos insumos e o número de linhas de rastro |
| Decisões | `#decisoes` | "O que está com quem, e o que o sistema decidiu sozinho?" | Kanban somente leitura (sem arrastar, sem botão de mover). Cada pendência aparece uma vez. Cada coluna tem o total em jogo, e a última traz as decisões tomadas por regra, com a regra e a fonte à vista |
| Contratado × cobrado | `#contratado` | "A Orbe e a Ponte cobraram o que foi contratado?" | Por lojista: vendas, volume bruto, comissão pela planilha, valor pela taxa aplicada, diferença, divergência listada e situação. Abas que filtram de verdade (Todos, Com diferença, Sem contrato, Conferem). Alternância Checkout (Orbe) / Remessa (Ponte); na remessa, o spread negativo tem as duas colunas que a Helena pediu (Q-AA 3: "deixando claro qual é qual"): o do relatório (o que aconteceu) e a diferença até o contrato (o que pedir à Ponte, o valor da pendência). Nota com o resíduo de truncamento da Orbe calculado da saída |
| Notas e rastro | `#notas` | "De onde sai este número?" | As notas a emitir (tomador, valor, discriminação) e a busca por qualquer ID (TX, AN, PC-, L<n>, FITID, NF-, COM-, DIV-, LAN-, PEN-, EXC-, ou uma chave do `regras.yaml`). O resultado é a cadeia em quatro passos: arquivo:linha de origem → regra (status e fonte) → cálculo → destino, com a soma das linhas conferida contra o número reportado |

Os links "Rastro" usam `#notas?id=<ID>`, que abre a tela 4 já com a busca feita.

## Mapeamento: pendência → destino do dinheiro (tela 1)

O grupo sai do `tipo` da pendência e, nas divergências de checkout (`DIVERGENCIA_CHECKOUT` e, desde a D85, `DEVOLUCAO_CONCESSAO_COMERCIAL`), da `natureza`. A `natureza` é lida de `pendencias.csv`, se a coluna existir, ou das linhas de `divergencias_taxa.csv` cujo `ref_origem` está na pendência. Na main isso é a D63, com os valores `contrato_orbe` e `condicao_nao_informada`.

| Grupo | Tipos | Soma no total? |
|---|---|---|
| Devolver ao lojista | **toda** `DIVERGENCIA_CHECKOUT` e a `DEVOLUCAO_CONCESSAO_COMERCIAL` (a Casa, D85: tipo próprio, mesmo valor), pelo Σ `valor_a_devolver_brl` das transações dela em `divergencias_taxa.csv` (sem a coluna: `valor_brl` da pendência) | sim |
| Recuperar da Orbe | a parte das `DIVERGENCIA_CHECKOUT` com natureza `contrato_orbe` (Σ `valor_a_devolver_brl` dessas linhas) | **não**: "é o mesmo valor que volta ao lojista" |
| Repasse que voltou | `DEVOLUCAO_PIX_LOJISTA` | sim |
| Contestar com a Ponte | `CONTESTACAO_PONTE` · `SPREAD_NEGATIVO_SEM_TRAVA` · `EXCESSO_REMESSA` | sim, exceto `EXCESSO_REMESSA` |
| Receita parada | `SEM_CONTRATO_VIGENTE` · `NF_NEGATIVA` · `NOTA_BLOQUEADA` | sim |
| Sem origem | `PIX_SEM_IDENTIFICACAO` · `TRANSFERENCIA_SEM_ORIGEM` · `SEM_REGRA` · `IA_REPROVADA` | sim |
| Em trânsito | `TRANSFERENCIA_EM_TRANSITO` · `ACOMPANHAMENTO_APORTE` (D87; antes `APORTE_SEM_OPERACAO`) · `CONFERENCIA_REPASSE` | não |
| Outras pendências | qualquer tipo novo (outubro não quebra) | sim |
| (Alertas, à parte) | `ALERTA_*` | não, é informativo |
| (fora dos grupos) | pendência sem valor (em setembro não há; a `PROVISAO_DO_MES` saiu das pendências) | aparece só no kanban |

**Custo para a Tarvo**, no topo da visão geral: devolver ao lojista − recuperar da Orbe, só com as divergências de checkout, com o link de rastro de cada pendência que compõe cada parcela. Setembro, com a Bridge como `contrato_orbe` e os ajustes tardios do 06: 16.972,57 − 1.575,80 (Rota Global 1.545,86 + Bridge 29,94) = **15.396,77**, que é a Casa do Estudante (condição especial: custo da Tarvo). É a mesma conta do resumo do `python -m tarvo` e da D71 (`divergencias.valor_a_devolver`).

Aprovado pelo Lucca (17/10):

- **Total em jogo = Σ |valor|.** Somar com sinal deixaria o spread negativo (−3.565,98 até o contrato, prejuízo da Tarvo) abater o spread cobrado a mais (+1.418,85, dinheiro do lojista) e a duplicata (821,88): "Contestar com a Ponte" daria −R$ 1.325,25 em vez de R$ 5.806,71. Cada linha mostra o valor com o sinal do CSV.
- **Toda divergência de checkout é "devolver ao lojista"** (Q-A: "a diferença volta para o lojista e eu cobro a Orbe"; Q-U 4: o lojista já recebeu a menos). "Recuperar da Orbe" é a parte `contrato_orbe` e não soma. Sem a coluna `natureza`, o grupo "recuperar" não aparece: nada se afirma sobre a Orbe.
- **Não somam (`NAO_SOMA`):** em trânsito e aportes; `CONFERENCIA_REPASSE`, porque o valor é a própria nota de remessa e já está no "a faturar"; e `EXCESSO_REMESSA`, porque os 709,46 são a metade da Tarvo dentro dos 1.418,85 contestados.

A validar:

- **`DEVOLUCAO_PIX_LOJISTA` (12.400,00, L65) saiu de "devolver ao lojista"** para um grupo próprio, "Repasse que voltou". Ela não é divergência de taxa: é dinheiro do lojista que o banco devolveu, com motivo ainda desconhecido (Q-F 4b). Se continuasse no grupo, "devolver" daria 29.372,57 e o custo para a Tarvo ficaria errado.
- **`SEM_CONTRATO_VIGENTE`** (Atlas) entra em "receita parada" com o rótulo "taxa cobrada pela Orbe (referência); comissão a definir pelo comercial" (`ROTULO_VALOR`), na visão, no kanban e na tela 3.
- O aporte de 18.240 da Ponte Aérea (`ACOMPANHAMENTO_APORTE` desde a D87) está em "em trânsito" pela Q-N 5 / Q-P 1: "dinheiro de uma remessa que sai em outubro".

## Premissas: de onde vem cada contagem (tela 1)

- **"Premissas do HIPOTESES.md"**: linhas `H..` da tabela Premissas, contadas pela 1ª palavra da coluna Status ("ASSUMO com aceite" conta como ASSUMO). Ao lado, a frase do Resumo de lá, literal. A tabela do Histórico conta como substituída. O teste confere que tabela e Resumo dizem o mesmo (setembro: 28 CONFIRMADO, 25 ASSUMO, 1 SEI, 1 substituída = 55). A lista que espera aprovação são as **25 ASSUMO do HIPOTESES**, com premissa, status, base e impacto.
- **"Regras no regras.yaml"**: cada regra do YAML (chave com `status`), sem as decisões marcadas `substituida`. Uma premissa vira várias regras (ex.: a H35 são várias regras de `classificacao_extratos`), por isso os números não coincidem. Setembro, com a main em 3fc4a53: 49 CONFIRMADO, 13 SEI, 35 ASSUMO, 0 PENDENTE, 2 decisões substituídas. No `HIPOTESES.md`: 31 CONFIRMADO, 23 ASSUMO, 2 SEI e 1 substituída (57 no Resumo).
- Sem `HIPOTESES.md` (`--hipoteses` aponta para outro caminho), a seção cai na lista ASSUMO do `regras.yaml`.

## Mapeamento: pendência → coluna do kanban (tela 2)

A ordem de avaliação é: `tipo` primeiro, depois `quem_decide`.

| Coluna | Regra |
|---|---|
| Com a {quem fecha} | `quem_decide` contém o nome de quem fecha (lido de `regras.yaml` → `divergencias.pendencia_por_lojista.valor.quem_decide`; senão, o `quem_decide` mais frequente). Também é o destino de tudo que nenhuma outra regra pega (Q-U 2: "eu confiro, decido as exceções") |
| Com o comercial | `quem_decide` contém "comercial" e não contém quem fecha (ex.: `comercial`). "Helena + comercial" fica com a Helena, porque ela conduz: "pendência minha com o comercial" (Q-N 1) |
| Com uma contraparte | tipo `CONTESTACAO_PONTE` ou `EXCESSO_REMESSA`, que dependem da Ponte |
| Acompanhar | tipo `TRANSFERENCIA_EM_TRANSITO`, `CONFERENCIA_REPASSE`, `ACOMPANHAMENTO_APORTE` ou `APORTE_SEM_OPERACAO`; ou `quem_decide` com "analista"/"conferir" |
| Fechadas por regra | não é pendência. Um cartão por grupo do que o sistema decidiu sozinho: **um por extrato** (lançamentos com `metodo` REGRA, e um cartão "IA" se houver), listando cada regra com status, contagem e um exemplo; **um por exclusão `EXC-*`** do rastro (duplicata, spread negativo), com regra, status, fonte e exemplo; **um por condição especial** aplicada (nota do rastro `regras.yaml cadastro.condicoes_especiais[<id>]`). A chave da regra abre a busca, que mostra a fonte e os números que ela decide. Não soma ao total. Setembro: 5 cartões (Aurora 84 lançamentos em 17 regras, Meridiano 100 em 10, duplicata 1, spread negativo 4, Casa do Estudante 118 linhas) |

O total de cada coluna é Σ |valor| das pendências que somam. O que não soma aparece como "+ R$ x à parte (n)", com o selo "não entra no total" no cartão.

## Por que HTML estático

- **Sai do mesmo código e da mesma execução que a `saida/`.** Não é uma segunda fonte de verdade: lê os CSVs que o validador já conferiu.
- **É determinístico.** Não tem data/hora nem hash de commit; a versão é o sha256 dos insumos. Gerar duas vezes dá os mesmos bytes (testado, inclusive com CSS/JS em CRLF, como sai do checkout com `autocrlf` no Windows).
- **É versionado junto com os CSVs**, então o diff do painel no git acompanha o diff dos números.
- **Abre sem servidor** (duplo clique, `file://`). A única URL externa é a fonte Inter do Google Fonts; offline, cai em `system-ui` e continua legível.
- **A banca vê no navegador o mesmo número do arquivo.** Os totais estão em `data-*` e no JSON embutido, e o teste confere esses valores contra os CSVs.

## Integração ao `python -m tarvo` (feita na `relatorio`)

1. **`pyproject.toml`:** `painel/*.css` e `painel/*.js` em `[tool.setuptools.package-data]`, ao lado de `prompts/*.md`. Com `pip install -e .` já funcionava; um wheel normal não levaria os dois arquivos.
2. **Mesma execução:** `__main__.py` chama `gerar_painel(saida, dados, regras)` depois do `VALIDADOR: OK`, só sobre saída validada (com erro de validação, o `painel.html` de uma execução anterior é apagado, para não ficar ao lado de CSVs inválidos), e o resumo final diz onde está o painel. O CI (`git diff --exit-code saida/`) passa a cobrir também o `painel.html`.
3. **Mesmos bytes no Linux e no Windows:** o CI roda nos dois e compara byte a byte. `.gitattributes` ganhou `saida/painel.html text eol=lf`, e o sha256 do `regras.yaml` e do `HIPOTESES.md` é calculado com CRLF trocado por LF, porque o autocrlf do Windows muda esses dois no checkout (o `data/` é `-text` e fica como chegou). Testes: `test_python_m_tarvo_gera_o_painel_e_a_saida_continua_deterministica` (duas execuções em pastas diferentes dão os mesmos bytes em todos os arquivos, e o painel é igual ao versionado) e `test_fim_de_linha_do_regras_e_do_hipoteses_nao_muda_o_painel`.
4. **README:** uma linha dizendo que a execução gera `saida/painel.html` e que ele abre com duplo clique.
5. **`test_cli.py`:** a lista de arquivos da saída inclui `painel.html`.
6. **`natureza`, `valor_a_devolver_brl`, `ALERTA_*` e `saida/rascunhos/`** são lidos quando existem e, sem eles, a seção some (testes `test_campos_opcionais_aparecem_quando_existem` e `test_sem_campos_opcionais_as_secoes_somem`). Se a main gravar `natureza` também em `pendencias.csv`, ela tem prioridade sobre a de `divergencias_taxa.csv`. Natureza nova entra em "devolver ao lojista" e só vira "recuperar" se for `NATUREZA_RECUPERAR`.
7. **Ambiente:** o `.venv` tem install editável apontando para o `src` da main. No worktree, rode com `PYTHONPATH=src`, senão `python -m tarvo` (inclusive o subprocesso de `test_cli.py`) importa o código da main.

## Com mais tempo

- **Registro de decisões:** quem aprovou, quando e com qual evidência. É aqui que o kanban ganha função: mover um cartão passa a ser registrar uma decisão (Q-S: "Registrar quem aprovou e quando é ótimo"), e uma premissa ASSUMO aprovada vira CONFIRMADO com autor e data.
- **Cadastro de condições comerciais** com aviso automático à Orbe e à Ponte quando o comercial fecha uma condição nova (Q-T 1: "Ninguém tem essa função hoje").
- **Checagem diária quando o relatório chega**, em vez de uma vez no fim do mês: a divergência aparece no dia em que a Orbe cobra, não oito dias úteis depois.
- **Login por papel** (analista, Helena, comercial) e **integrações** (portal da Orbe, e-mail da Ponte, extratos, ERP Fênix).

Tudo isso exige estado e usuários, então o painel vira uma aplicação com backend e banco (ex.: Postgres e um frontend React).
