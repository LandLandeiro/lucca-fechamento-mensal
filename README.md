# Tarvo · fechamento de setembro/2026

[![CI](https://github.com/LandLandeiro/tarvo-fechamento/actions/workflows/ci.yml/badge.svg)](https://github.com/LandLandeiro/tarvo-fechamento/actions/workflows/ci.yml)

**O que o CI garante (a cada push):** o fechamento roda do zero num ambiente limpo, em Windows e Linux, com Python 3.12 e 3.14; os testes passam; e a saída gerada é idêntica, byte a byte, à commitada em `saida/`, sem chave de API (a IA responde pelo `cache_ia/`).

> Desafio Barte AI · Hackathon de AI Services · 16 e 17/10/2026 · time solo: Lucca Rocha Landeiro

**O problema em 2 frases.** Todo mês o financeiro da Tarvo leva 8 dias úteis para fechar comissões, divergências de taxa, notas e extratos à mão, cruzando a planilha de taxas com os relatórios da Orbe e da Ponte. E erra porque o contrato muda sem ninguém avisar quem cobra: em setembro, R$ 16.972,57 descontados a mais dos lojistas no checkout, dos quais R$ 15.396,77 ficam como custo da Tarvo: a isenção que o comercial deu à Casa do Estudante nunca chegou à Orbe.

## Setembro em números (`saida/`)

| | |
|---|---|
| Notas a emitir | **R$ 243.284,29 em 21 notas** (20 de checkout, R$ 203.740,84; 1 para a Ponte, R$ 39.543,45), já com os 14 ajustes tardios da Orbe (arquivo 06: −R$ 3.304,39) |
| Comissão | checkout R$ 203.735,34 (21 lojistas; a Casa fica em −5,50 e não emite nota); remessa R$ 39.543,45 (14 lojistas) |
| Divergência de checkout | 210 transações (o estorno de venda divergente entra com valor negativo); devolver aos lojistas **R$ 16.972,57**; recuperar da Orbe **R$ 1.575,80** (Rota e Bridge: condição contratada); custo para a Tarvo **R$ 15.396,77** (Casa: concessão do comercial fora do contrato) |
| Remessa | Mundo Aberto R$ 1.418,85 a contestar com a Ponte; 4 spreads negativos: −R$ 1.834,05 no relatório (o que aconteceu), −R$ 3.565,98 até o spread do contrato (o que se pede à Ponte) |
| Lançamentos | 184 dos dois extratos, todos por regra (0 para a IA) |
| Pendências | **15**, cada uma com valor, motivo e quem decide (Helena 11, Helena + comercial 2, comercial 1, analista 1) |
| Rastro | **5.251 linhas**: cada número acima ligado às linhas de origem (relatório da Orbe, ajustes tardios, anexo da Ponte, extratos) |

## Como a banca roda

Com Python 3.12 ou mais novo e Git (num Windows sem Python configurado, veja [Como rodar do zero](#como-rodar-do-zero)):

```
git clone https://github.com/LandLandeiro/tarvo-fechamento.git && cd tarvo-fechamento
python -m pip install -e .
python -m tarvo --dados data --saida saida
```

A saída gerada é idêntica à pasta `saida/` entregue; o CI confere isso a cada commit. Não precisa de chave de API (ver [Chave de API](#chave-de-api)). Para outro mês, troque `--dados data` pela pasta do mês: nada é fixo para setembro. No fim, a tela mostra um resumo do fechamento (comissões, notas, divergências, lançamentos, pendências e onde estão os arquivos).

**Painel:** a mesma execução gera `saida/painel.html`, um arquivo só, sem servidor: abra com duplo clique no navegador. Mostra para onde vai o dinheiro, o que a Helena decide, o contratado × cobrado e a busca no rastro, tudo lido dos CSVs (detalhes em [`docs/PAINEL.md`](docs/PAINEL.md)).

## Para a banca: onde ver cada critério

A tabela é a porta de entrada; os arquivos detalhados são a evidência.

| Critério do case | Onde ver | O que mostra |
|---|---|---|
| Correção dos números (25%) | `saida/` + `docs/AUDITORIA.md` + CI | Os 6 arquivos, cada número com a linha de origem no `rastro.csv`; auditoria independente com 0 violações; o CI refaz a saída do zero em Windows e Linux a cada commit e confere que é idêntica |
| Uso de IA (20%) | `PROMPTS/MOMENTOS.md` + `PROMPTS/` | Onde a IA errou e como foi corrigida, onde ela sugeriu e o código provou antes de aceitar, e o histórico completo das sessões |
| Causa raiz (15%) | `docs/CAUSA_RAIZ.md` | Por que o fechamento erra (o comercial fecha a condição e ninguém avisa a Orbe e a Ponte), com os casos de setembro em reais, o custo (R$ 15.396,77) e o que precisa mudar no processo |
| Hipóteses (10%) | `HIPOTESES.md` + `regras.yaml` | O que é fato, o que é premissa e o que o financeiro confirmou, com fonte; cada regra do cálculo com status SEI/ASSUMO/CONFIRMADO |
| Perguntar antes de construir (10%) | `HIPOTESES.md` (seção "Perguntas ao financeiro") + `docs/FINANCEIRO_SLACK.md` | As perguntas feitas, as respostas literais da Helena e o que cada resposta mudou na solução |
| Raciocínio e comunicação (10%) | este README + `docs/PLANO.md` + `docs/DECISOES.md` | Como rodar, como fechar outubro e onde a IA atua; o plano; cada decisão técnica com alternativa e motivo |
| Tempo e pontualidade (10%) | histórico de commits + `docs/DIARIO.md` + `docs/CHECKPOINTS.md` | O que foi feito em cada etapa, com hora, verificação e commit; os checkpoints com o texto enviado e a resposta |

## Chave de API

**É opcional.** Sem chave, a solução roda inteira e a saída é a mesma.

- **Onde configurar:** num arquivo `.env.local` na raiz do repositório, com a linha `ANTHROPIC_API_KEY=...` (copie o `.env.example`, que é o modelo), **ou** na variável de ambiente `ANTHROPIC_API_KEY`. O `.env.local` está no `.gitignore` e nunca vai para o git; a chave nunca é impressa nem gravada.
- **Sem chave:** a IA usa as respostas guardadas em `cache_ia/` (commitado) e o resultado é idêntico, sem custo. Linhas novas que não estejam no cache ficam para uma pessoa decidir (aparecem em `pendencias.csv`), com aviso, e o programa termina normalmente.
- **Para desligar a IA:** `--sem-ia`.

## O que a solução entrega

Lê os arquivos de `data/` exatamente como chegam e gera, em `saida/`:

| Arquivo | O que é |
|---|---|
| `comissoes_por_lojista.csv` | comissão de cada lojista por linha de negócio |
| `divergencias_taxa.csv` | taxa contratada × aplicada, transação por transação |
| `notas_a_emitir.csv` | notas fiscais a emitir |
| `lancamentos_classificados.csv` | lançamentos dos dois extratos no plano de contas |
| `pendencias.csv` | o que precisa de uma pessoa, com motivo e quem decide |
| `rastro.csv` | cada número de saída ligado às linhas de origem |

Convenções: em `pendencias.csv`, `ref_origem` traz só os ids das linhas de origem (id_transacao, Nº Operação, `L<n>`, FITID) separados por `|`, e a explicação fica em `motivo`. Em `lancamentos_classificados.csv`, `confianca` nunca é vazia: REGRA = 1.00, decisão humana registrada = 1.00, IA = a confiança dela, HUMANO ainda sem decisão = 0.00.

Arquivos **extras** (além dos 6 do case):

| Arquivo | O que é |
|---|---|
| `contestacao_ponte.csv` | uma linha por operação que a Helena contesta com a Ponte (valor e motivo) |
| `sugestoes_regra.csv` | vínculos que a IA acertou e o código provou, propostos como regra para o mês seguinte |
| `rascunhos/` | rascunhos de contestação para a Helena revisar e enviar: um por contraparte e lojista (`orbe_rota_global.md`, `orbe_escola_bridge.md`, `ponte_mundo_aberto.md`, `ponte_spreads_negativos.md`, `ponte_duplicata.md`), cada um com assunto, texto, total e a lista anexa em `.csv`; sem IA. A Casa não tem rascunho para a Orbe (concessão nossa: só devolução ao lojista) |
| `06_orbe_ajustes_tardios_*.csv` (entrada, opcional) | ajustes que a Orbe manda depois do relatório: lidos junto com o 01, cada linha no rastro com o próprio arquivo; se faltar, o fechamento segue |
| `pendencias_resolvidas.csv` | só com `--pendencias-anteriores`: pendências do mês anterior resolvidas neste mês |
| `manifesto.csv` | o que entrou na execução: cada arquivo da pasta de dados com o papel, as linhas lidas, o tamanho e o sha256, e a versão das regras (sha256 do `regras.yaml` e a contagem por status). Determinístico: duas execuções com os mesmos arquivos dão o mesmo manifesto, por isso ele fica no git e o CI compara |

**Manifesto × log da execução.** Data e hora não entram em `saida/`: mudariam a cada execução e quebrariam a comparação do CI. Cada execução da linha de comando grava também `logs/execucao_<AAAAMMDD-HHMMSS>.log`, fora do git (`.gitignore`), com a data e a hora, o comando, o mesmo manifesto e os totais. O manifesto diz **o que** entrou; o log diz **quando** rodou.

## Como rodar do zero

**Pré-requisito:** Python **3.12 ou mais novo** (python.org; testado com 3.12.10) e Git. No Windows, o `python` que vem no PATH sem instalação é só um atalho da Microsoft Store (`Python was not found ...`, código 9009): instale o Python e chame o executável instalado, como abaixo.

No PowerShell, a partir de uma pasta qualquer:

```powershell
git clone <url-do-repositório> tarvo-fechamento
cd tarvo-fechamento

# 1. ambiente (troque o caminho se instalou o Python em outro lugar; com o "py launcher": py -3.12 -m venv .venv)
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv

# 2. o pacote e as dependências (declaradas no pyproject.toml; o requirements.txt traz as mesmas)
.\.venv\Scripts\python.exe -m pip install -e .

# 3. fechamento (comando único) e testes
.\.venv\Scripts\python.exe -m tarvo --dados data --saida saida
.\.venv\Scripts\python.exe -m pytest
```

- `--dados` e `--saida` aceitam qualquer pasta, inclusive com espaço e acento (entre aspas). Sem `--regras`, vale o `regras.yaml` da raiz do repositório, de onde quer que se rode; `--regras <arquivo>` tem prioridade.
- Os comandos usam `.\.venv\Scripts\python.exe` direto, sem `Activate.ps1`: num Windows limpo a política de execução do PowerShell costuma bloquear o script de ativação.
- Saída esperada: o detalhe por lojista, `VALIDADOR: OK` e um resumo do fechamento para o financeiro; código de saída 0 (1 = saída inválida; 2 = erro de entrada). Os CSVs vão para `--saida`; o resultado é determinístico (mesmo hash a cada execução, em qualquer pasta).

Chave de API: opcional; onde configurar e o que acontece sem ela, na seção [Chave de API](#chave-de-api).

## Fechando outubro

Não muda nada no programa. A Helena (ou quem fecha o mês) faz três coisas:

1. **Coloca os arquivos de outubro numa pasta**, do jeito que chegam: o relatório da Orbe, a planilha de taxas, o e-mail da Ponte com o anexo, o plano de contas e os dois extratos. Os nomes podem trazer o mês (`..._out2026...`); o programa acha cada arquivo pelo começo do nome.
2. **Roda o fechamento apontando para essa pasta e para as pendências de setembro**:
   `.\.venv\Scripts\python.exe -m tarvo --dados <pasta de outubro> --saida <pasta de saída> --pendencias-anteriores saida\pendencias.csv --orbe-anterior data\01_orbe_relatorio_comissoes_set2026.csv`
   O que setembro deixou em aberto e outubro resolveu (por exemplo, a transferência de 300 mil que estava em trânsito) aparece como resolvido, e não como pendência nova. Com `--orbe-anterior` (o relatório da Orbe de setembro), um lojista que aguardava contrato e agora tem contrato na planilha (a Atlas, quando o comercial confirmar) tem as linhas de setembro faturadas na nota de outubro, pela taxa confirmada (Q-Q).
3. **Abre o `pendencias.csv`** e decide o que é dela (divergências de taxa por lojista, devoluções, contestações, nota negativa ou bloqueada, lojista sem contrato). O resto (comissões, divergências, notas a emitir e lançamentos) já vem pronto, cada número com a linha de origem no `rastro.csv`.

Se uma regra mudar (taxa nova, nome novo de lojista no extrato, feriado do ano seguinte), a mudança é uma linha no `regras.yaml`, com a fonte; uma condição especial nova do comercial é um item a mais na lista `cadastro.condicoes_especiais` (CNPJ, linhas de negócio, taxa, vigência, fonte). O programa não muda.

## Onde a IA atua e onde não atua

- **Regra primeiro, sempre.** Em setembro a IA não recebe nenhuma linha: os 184 lançamentos casam por regra, inclusive os 7 da EduAbroad, pelo nome que o relatório da Orbe usa para o EC dela (D52). Uma versão anterior restringiu essa regra para a IA ter trabalho; um revisor independente apontou, e foi corrigido.
- **Atua só** nos lançamentos de extrato que nenhuma regra do `regras.yaml` cobre, como um nome novo no extrato que não está na planilha nem na Orbe (o teste de outubro tem um). Ela sugere conta, lojista, justificativa e confiança, a partir de listas fechadas.
- **O código prova antes de aceitar:** conta lançável; CNPJ no cadastro; prova em outra fonte (Meridiano: soma dos PIX do lojista = operações dele na Ponte; Aurora: o lojista tem vendas na Orbe no mês); confiança ≥ 0,8. Falhou qualquer item → vai para uma pessoa, com o motivo.
- **Não atua** em comissão, divergência, nota, remessa ou cadastro: tudo isso é regra determinística. A IA também não cria regra: o que ela acertou vira proposta em `saida/sugestoes_regra.csv` para alguém aprovar no mês seguinte.

### Ver a IA funcionando

Setembro não tem linha para a IA. O outubro sintético (`tests/fixtures/outubro/`, DADO SINTÉTICO) tem uma: um aporte da Nórdica que chega com nome novo, "PIX RECEB NEI EDUCACAO INTERNACIONAL".

```
python -m tarvo --dados tests/fixtures/outubro --saida saida_outubro
```

- **Com a chave no `.env.local`** (ver [Chave de API](#chave-de-api)): o programa chama a API para a linha que não está no cache. Para forçar a chamada de verdade, rode com `--saida` numa pasta qualquer depois de apagar o arquivo do cache dessa linha (`cache_ia/112face5….json`); a tela mostra `1 chamadas à API`, os tokens e o custo (na nossa execução: 2.612 de entrada, 143 de saída, ~US$ 0,0003).
- **Sem chave:** a resposta vem de `cache_ia/` (commitado), com o mesmo resultado; a tela mostra `1 do cache`.
- **O que aparece na tela:** a sugestão da IA (conta 2.1.02.001, lojista Nórdica, confiança 0,9, justificativa) e as 4 checagens do código: (a) conta lançável, (b) CNPJ no cadastro, (c) Σ PIX da Nórdica 473.909,27 (regra 401.420,40 + IA 72.488,87) = Σ das operações dela na Ponte, (d) confiança ≥ 0,8 → aceita.
- **Em `saida_outubro/sugestoes_regra.csv`:** `SUG-001;ALIAS_LOJISTA;MERIDIANO;NEI EDUCACAO INTERNACIONAL;2.1.02.001;PROPOSTA`, com a evidência da soma. Fica PROPOSTA até alguém aprovar o alias no `regras.yaml` (`classificacao_extratos.aliases_lojista`).

## Limitações conhecidas

- **Outubro é dado sintético** (`tests/fixtures/outubro/`): setembro deslocado um mês, com seis novidades (EC novo, estorno da Bridge, TED de 300 mil, PIX da EduAbroad, nome novo da Nórdica, contrato da Atlas). Prova que o código roda sem mudança, não que outubro real não traz caso novo.
- **Perguntas sem resposta** (17/10): se o arquivo de ajustes tardios vem todo mês e o que vale quando ele repete um id do relatório (Lucca, 13:19: hoje vira pendência); e se o Spread R$ do ajuste da Ponte é o spread inteiro ou já a participação (Desbravadores, 12:04). O ajuste da Ponte tem a regra registrada (Q-Z) e vira pendência, mas o abatimento ainda não é calculado (D83).
- **Alerta de antecipação só para lojista sem histórico** (D66, D73). A antecipação pode cobrir recebíveis de meses anteriores, que não estão nos dados; com o critério do mês inteiro, o alerta seria alarme falso em 5 lojistas.
- **Sem agenda de recebíveis da Orbe**: checar a antecipação de todos os lojistas e conciliar a Orbe com o banco exige essa agenda, que não veio no pacote.
- **Conciliação Orbe × banco parcela por parcela fica de fora** (Q-M): os créditos da Orbe no Aurora são só classificados.
- **Dia útil só com os feriados nacionais por lei de 2026** (D59): Carnaval, Sexta-feira Santa e Corpus Christi não entram, e 2027 precisa ser acrescentado no `regras.yaml`.

## Fato, resposta e premissa

Três tipos de afirmação, cada um num lugar:

- **Fato dos dados** → está nos arquivos de `data/` e cada número de saída aponta a linha de origem no `rastro.csv`. Regras do tipo no `regras.yaml`: **SEI** (13).
- **Resposta do financeiro** → texto literal em `docs/FINANCEIRO_SLACK.md` (Q-A a Q-AH); a regra que ela fixa é **CONFIRMADO** no `regras.yaml` (48), com a fala literal na fonte (um teste confere, D90) e quem aprovou (`aprovado_por`, Q-S). Os exemplos concretos dela são testes com o valor que ela afirmou (`docs/TESTE_DAS_REGRAS.md`), e uma auditoria independente das regras conferiu a leitura (`docs/auditoria_regras/`).
- **Premissa nossa** → **ASSUMO** no `regras.yaml` (38), sempre com o motivo; as que a Helena delegou trazem o `aceite`. Em `HIPOTESES.md`, cada premissa diz o que muda se estiver errada.

Nenhuma regra PENDENTE. O que nenhum dos três cobre vira pendência para uma pessoa, não regra.

## Com mais tempo

- **Cadastro único de condições comerciais com aviso automático à Orbe e à Ponte**: o comercial registra a condição uma vez, com vigência, e o aviso sai no mesmo dia. Ataca a causa dos 4 casos de setembro: Casa, Bridge e Mundo Aberto com condição que não chegou à Orbe ou à Ponte, e a Atlas transacionando sem contrato registrado.
- **Checagem diária, quando o relatório da Orbe ou da Ponte chega**, em vez de no fechamento: a divergência aparece no dia, antes de o lojista reclamar.
- **Travas de antecipação e de conta garantida definidas pela Helena** (Q-N 6, Q-W): limite por lojista, com alerta ao passar.
- **Registro de decisões**: quem aprovou cada regra e cada pendência, quando e com qual evidência.
- **Integrações** com a Orbe, a Ponte, os bancos e o ERP, para acabar com os downloads manuais.

Isso exige estado e usuários, então vira uma aplicação com backend e banco de dados.

## Organização do repositório

```
data/      data pack original, sem alteração (ver .gitattributes)
docs/      instruções do case
src/       código
saida/     arquivos gerados
cache_ia/  respostas da IA em cache (reexecução sem chave e sem custo)
scripts/   auditoria independente da saída (auditar_saida.py)
PROMPTS/   histórico das sessões de IA + MOMENTOS.md
HIPOTESES.md
```
