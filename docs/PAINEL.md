# Painel do fechamento (`saida/painel.html`)

```powershell
python -m tarvo.painel --saida saida            # padrões: --dados data --regras regras.yaml
```

O resultado é um arquivo único, `saida/painel.html`, com HTML, CSS e JS puro inline, sem framework e sem build. Abre com duplo clique, sem servidor. Ele lê só o que o fechamento já gerou: `saida/*.csv`, `rastro.csv` e `regras.yaml`. Do `data/` lê duas coisas: o sha256 de cada arquivo, que identifica a versão, e o `valor_taxa` da Orbe, para a coluna "pela taxa aplicada". O painel não calcula regra nova: cada número exibido é uma soma de linhas da saída, feita em `Decimal`.

Código: `src/tarvo/painel/` (`__init__.py` monta tudo, `estilo.css` e `app.js` entram inline, `__main__.py` é a CLI). Testes: `tests/test_painel.py`.

## As quatro telas e a pergunta da Helena que cada uma responde

| Tela | Âncora | Pergunta | O que mostra |
|---|---|---|---|
| Visão geral | `#visao` | "Quanto eu faturo, e o que está parado esperando por mim?" | "R$ X a faturar em N notas" (de `notas_a_emitir.csv`); o dinheiro que depende de uma decisão, agrupado pelo destino; alertas `ALERTA_*`, se houver; premissas ASSUMO do `regras.yaml` com fonte e motivo, mais a contagem por status; links para cada CSV e para `saida/rascunhos/`; rodapé com o sha256 dos insumos e o número de linhas de rastro |
| Decisões | `#decisoes` | "O que está com quem, e o que o sistema decidiu sozinho?" | Kanban somente leitura (sem arrastar, sem botão de mover). Cada pendência aparece uma vez. Cada coluna tem o total em jogo, e a última traz as decisões tomadas por regra, com a regra e a fonte à vista |
| Contratado × cobrado | `#contratado` | "A Orbe e a Ponte cobraram o que foi contratado?" | Por lojista: vendas, volume bruto, comissão pela planilha, valor pela taxa aplicada, diferença, divergência listada e situação. Abas que filtram de verdade (Todos, Com diferença, Sem contrato, Conferem). Alternância Checkout (Orbe) / Remessa (Ponte). Nota com o resíduo de truncamento da Orbe calculado da saída |
| Notas e rastro | `#notas` | "De onde sai este número?" | As notas a emitir (tomador, valor, discriminação) e a busca por qualquer ID (TX, AN, PC-, L<n>, FITID, NF-, COM-, DIV-, LAN-, PEN-, EXC-, ou uma chave do `regras.yaml`). O resultado é a cadeia em quatro passos: arquivo:linha de origem → regra (status e fonte) → cálculo → destino, com a soma das linhas conferida contra o número reportado |

Os links "Rastro" usam `#notas?id=<ID>`, que abre a tela 4 já com a busca feita.

## Mapeamento: pendência → destino do dinheiro (tela 1)

O grupo sai do `tipo` da pendência e, em `DIVERGENCIA_CHECKOUT`, da `natureza`. A `natureza` é lida de `pendencias.csv`, se a coluna existir, ou das linhas de `divergencias_taxa.csv` cujo `ref_origem` está na pendência. Na main isso é a D63, com os valores `contrato_orbe` e `condicao_nao_informada`.

| Grupo | Tipos | Soma no total? |
|---|---|---|
| Devolver ao lojista | `DIVERGENCIA_CHECKOUT` com natureza `condicao_nao_informada` **ou sem natureza** · `DEVOLUCAO_PIX_LOJISTA` | sim |
| Cobrar da Orbe | `DIVERGENCIA_CHECKOUT` com natureza `contrato_orbe` | sim |
| Contestar com a Ponte | `CONTESTACAO_PONTE` · `SPREAD_NEGATIVO_SEM_TRAVA` · `EXCESSO_REMESSA` | sim, exceto `EXCESSO_REMESSA` |
| Receita parada | `SEM_CONTRATO_VIGENTE` · `NF_NEGATIVA` · `NOTA_BLOQUEADA` | sim |
| Sem origem | `PIX_SEM_IDENTIFICACAO` · `TRANSFERENCIA_SEM_ORIGEM` · `SEM_REGRA` · `IA_REPROVADA` | sim |
| Em trânsito | `TRANSFERENCIA_EM_TRANSITO` · `APORTE_SEM_OPERACAO` · `CONFERENCIA_REPASSE` | não |
| Outras pendências | qualquer tipo novo (outubro não quebra) | sim |
| (Alertas, à parte) | `ALERTA_*` | não, é informativo |

Escolhas que o Lucca precisa validar:

- **Total em jogo = Σ |valor_brl|.** Somar com sinal deixaria o spread negativo (−1.834,05, prejuízo da Tarvo) abater o spread cobrado a mais (+1.418,85, dinheiro do lojista): "Contestar com a Ponte" daria R$ 406,68. Cada linha mostra o valor com o sinal do CSV.
- **`DIVERGENCIA_CHECKOUT` sem natureza vai para "devolver ao lojista"**, porque é a única afirmação verdadeira nos dois casos. Pela Q-U 4, quando a Orbe cobra a mais o lojista já recebeu a menos, e a Tarvo devolve. "Cobrar da Orbe" só aparece quando a saída diz `contrato_orbe`. Pela Q-N 1 e pela Q-V, a Casa do Estudante não é cobrança da Orbe.
- **Não somam (`NAO_SOMA`):** em trânsito e aportes, como foi pedido. Somei mais dois a essa lista: `CONFERENCIA_REPASSE`, porque o valor é a própria nota de remessa e já está no "a faturar", e `EXCESSO_REMESSA`, porque os 709,46 são a metade da Tarvo dentro dos 1.418,85 contestados.
- **`SEM_CONTRATO_VIGENTE`** (Atlas) entra em "receita parada" com o valor que a pendência traz. Esse valor é a taxa cobrada pela Orbe, informativa, conforme o próprio `motivo`. A comissão contratada não existe enquanto o comercial não confirmar.
- O `APORTE_SEM_OPERACAO` da Ponte Aérea está em "em trânsito" pela Q-N 5 / Q-P 1: "dinheiro de uma remessa que sai em outubro".

## Mapeamento: pendência → coluna do kanban (tela 2)

A ordem de avaliação é: `tipo` primeiro, depois `quem_decide`.

| Coluna | Regra |
|---|---|
| Com a {quem fecha} | `quem_decide` contém o nome de quem fecha (lido de `regras.yaml` → `divergencias.pendencia_por_lojista.valor.quem_decide`; senão, o `quem_decide` mais frequente). Também é o destino de tudo que nenhuma outra regra pega (Q-U 2: "eu confiro, decido as exceções") |
| Com o comercial | `quem_decide` contém "comercial" e não contém quem fecha (ex.: `comercial`). "Helena + comercial" fica com a Helena, porque ela conduz: "pendência minha com o comercial" (Q-N 1) |
| Com uma contraparte | tipo `CONTESTACAO_PONTE` ou `EXCESSO_REMESSA`, que dependem da Ponte |
| Acompanhar | tipo `TRANSFERENCIA_EM_TRANSITO`, `CONFERENCIA_REPASSE` ou `APORTE_SEM_OPERACAO`; ou `quem_decide` com "analista"/"conferir" |
| Fechadas por regra | não é pendência. São cartões por regra que decidiu sozinha: lançamentos classificados (`metodo` REGRA ou IA, agrupados por `regra_aplicada`), exclusões `EXC-*` do rastro (duplicata, spread negativo) e condições especiais aplicadas (nota do rastro `regras.yaml cadastro.condicoes_especiais[<id>]`). Cada cartão mostra a chave, o status, a fonte, o número de linhas e o link de rastro. Não soma ao total |

O total de cada coluna é Σ |valor| das pendências que somam. O que não soma aparece como "+ R$ x à parte (n)", com o selo "não entra no total" no cartão.

## Por que HTML estático

- **Sai do mesmo código e da mesma execução que a `saida/`.** Não é uma segunda fonte de verdade: lê os CSVs que o validador já conferiu.
- **É determinístico.** Não tem data/hora nem hash de commit; a versão é o sha256 dos insumos. Gerar duas vezes dá os mesmos bytes (testado, inclusive com CSS/JS em CRLF, como sai do checkout com `autocrlf` no Windows).
- **É versionado junto com os CSVs**, então o diff do painel no git acompanha o diff dos números.
- **Abre sem servidor** (duplo clique, `file://`). A única URL externa é a fonte Inter do Google Fonts; offline, cai em `system-ui` e continua legível.
- **A banca vê no navegador o mesmo número do arquivo.** Os totais estão em `data-*` e no JSON embutido, e o teste confere esses valores contra os CSVs.

## Para o merge na main

1. **`pyproject.toml`:** incluir `painel/*.css` e `painel/*.js` em `[tool.setuptools.package-data]` (hoje só há `prompts/*.md`). Com `pip install -e .` funciona sem isso; um wheel normal não levaria os dois arquivos.
2. **Gerar na mesma execução:** chamar `tarvo.painel.gerar_painel(saida, dados, regras)` no fim do `__main__.py`, depois do validador, para que `python -m tarvo` já entregue o painel e o CI (`git diff --exit-code saida/`) cubra também o `painel.html`. Enquanto isso não for feito, o `painel.html` versionado só é atualizado quando alguém roda `python -m tarvo.painel`.
3. **README:** uma linha com o comando e o que o painel é.
4. **`natureza`, `ALERTA_*` e `saida/rascunhos/`** já são lidos quando existirem (teste `test_campos_opcionais_aparecem_quando_existem`). Se a main gravar `natureza` também em `pendencias.csv`, ela tem prioridade sobre a de `divergencias_taxa.csv`. Valores novos de natureza caem em "devolver ao lojista" até entrarem em `GRUPO_POR_NATUREZA`.
5. **Ambiente:** o `.venv` tem install editável apontando para o `src` da main. No worktree, rode com `PYTHONPATH=src`, senão `python -m tarvo` (inclusive o subprocesso de `test_cli.py`) importa o código da main.

## Com mais tempo

- **Registro de decisões:** quem aprovou, quando e com qual evidência. É aqui que o kanban ganha função: mover um cartão passa a ser registrar uma decisão (Q-S: "Registrar quem aprovou e quando é ótimo"), e uma premissa ASSUMO aprovada vira CONFIRMADO com autor e data.
- **Cadastro de condições comerciais** com aviso automático à Orbe e à Ponte quando o comercial fecha uma condição nova (Q-T 1: "Ninguém tem essa função hoje").
- **Checagem diária quando o relatório chega**, em vez de uma vez no fim do mês: a divergência aparece no dia em que a Orbe cobra, não oito dias úteis depois.
- **Login por papel** (analista, Helena, comercial) e **integrações** (portal da Orbe, e-mail da Ponte, extratos, ERP Fênix).

Tudo isso exige estado e usuários, então o painel vira uma aplicação com backend e banco (ex.: Postgres e um frontend React).
