# Tarvo · fechamento de setembro/2026

[![CI](https://github.com/LandLandeiro/tarvo-fechamento/actions/workflows/ci.yml/badge.svg)](https://github.com/LandLandeiro/tarvo-fechamento/actions/workflows/ci.yml)

**O que o CI garante (a cada push):** o fechamento roda do zero num ambiente limpo, em Windows e Linux, com Python 3.12 e 3.14; os testes passam; e a saída gerada é idêntica, byte a byte, à commitada em `saida/`, sem chave de API (a IA responde pelo `cache_ia/`).

> Desafio Barte AI · Hackathon de AI Services · 16 e 17/10/2026 · time: [NOME DO TIME] (Lucca Rocha Landeiro)

## Como a banca roda

Com Python 3.12 ou mais novo e Git (num Windows sem Python configurado, veja [Como rodar do zero](#como-rodar-do-zero)):

```
git clone https://github.com/LandLandeiro/tarvo-fechamento.git && cd tarvo-fechamento
python -m pip install -e .
python -m tarvo --dados data --saida saida
```

A saída gerada é idêntica à pasta `saida/` entregue; o CI confere isso a cada commit. Não precisa de chave de API (ver [Chave de API](#chave-de-api)). Para outro mês, troque `--dados data` pela pasta do mês: nada é fixo para setembro. No fim, a tela mostra um resumo do fechamento (comissões, notas, divergências, lançamentos, pendências e onde estão os arquivos).

## Para a banca: onde ver cada critério

A tabela é a porta de entrada; os arquivos detalhados são a evidência.

| Critério do case | Onde ver | O que mostra |
|---|---|---|
| Correção dos números (25%) | `saida/` + `docs/AUDITORIA.md` + CI | Os 6 arquivos, cada número com a linha de origem no `rastro.csv`; auditoria independente com 0 violações; o CI refaz a saída do zero em Windows e Linux a cada commit e confere que é idêntica |
| Uso de IA (20%) | `PROMPTS/MOMENTOS.md` + `PROMPTS/` | Onde a IA errou e como foi corrigida, onde ela sugeriu e o código provou antes de aceitar, e o histórico completo das sessões |
| Causa raiz (15%) | `docs/CAUSA_RAIZ.md` | Por que o fechamento erra (o contrato muda e ninguém avisa quem cobra), com os casos de setembro em reais e o que precisa mudar no processo |
| Hipóteses (10%) | `HIPOTESES.md` + `regras.yaml` | O que é fato, o que é premissa e o que o financeiro confirmou, com fonte; cada regra do cálculo com status SEI/ASSUMO/CONFIRMADO |
| Perguntar antes de construir (10%) | `HIPOTESES.md` (seção "Perguntas ao financeiro") + `docs/FINANCEIRO_SLACK.md` | As perguntas feitas, as respostas literais da Helena e o que cada resposta mudou na solução |
| Raciocínio e comunicação (10%) | este README + `docs/PLANO.md` + `docs/DECISOES.md` | Como rodar, como fechar outubro e onde a IA atua; o plano; cada decisão técnica com alternativa e motivo |
| Tempo e pontualidade (10%) | histórico de commits + `docs/DIARIO.md` | O que foi feito em cada etapa, com hora, verificação e commit |

## Chave de API

**É opcional.** Sem chave, a solução roda inteira e a saída é a mesma.

- **Onde configurar:** num arquivo `.env.local` na raiz do repositório, com a linha `ANTHROPIC_API_KEY=...` (copie o `.env.example`, que é o modelo), **ou** na variável de ambiente `ANTHROPIC_API_KEY`. O `.env.local` está no `.gitignore` e nunca vai para o git; a chave nunca é impressa nem gravada.
- **Sem chave:** a IA usa as respostas guardadas em `cache_ia/` (commitado) e o resultado é idêntico, sem custo. Linhas novas que não estejam no cache ficam para uma pessoa decidir (aparecem em `pendencias.csv`), com aviso, e o programa termina normalmente.
- **Para desligar a IA:** `--sem-ia`.

## O problema (em 2 frases)

[preencher]

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
| `pendencias_resolvidas.csv` | só com `--pendencias-anteriores`: pendências do mês anterior resolvidas neste mês |

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
   `.\.venv\Scripts\python.exe -m tarvo --dados <pasta de outubro> --saida <pasta de saída> --pendencias-anteriores saida\pendencias.csv`
   O que setembro deixou em aberto e outubro resolveu (por exemplo, a transferência de 300 mil que estava em trânsito) aparece como resolvido, e não como pendência nova.
3. **Abre o `pendencias.csv`** e decide o que é dela (divergências de taxa por lojista, devoluções, contestações, nota negativa ou bloqueada, lojista sem contrato). O resto (comissões, divergências, notas a emitir e lançamentos) já vem pronto, cada número com a linha de origem no `rastro.csv`.

Se uma regra mudar (taxa nova, nome novo de lojista no extrato, feriado do ano seguinte), a mudança é uma linha no `regras.yaml`, com a fonte; uma condição especial nova do comercial é um item a mais na lista `cadastro.condicoes_especiais` (CNPJ, linhas de negócio, taxa, vigência, fonte). O programa não muda.

## Onde a IA atua e onde não atua

- **Regra primeiro, sempre.** Em setembro a IA não recebe nenhuma linha: os 184 lançamentos casam por regra, inclusive os 7 da EduAbroad, pelo nome que o relatório da Orbe usa para o EC dela (D52). Uma versão anterior restringiu essa regra para a IA ter trabalho; um revisor independente apontou, e foi corrigido.
- **Atua só** nos lançamentos de extrato que nenhuma regra do `regras.yaml` cobre, como um nome novo no extrato que não está na planilha nem na Orbe (o teste de outubro tem um). Ela sugere conta, lojista, justificativa e confiança, a partir de listas fechadas.
- **O código prova antes de aceitar:** conta lançável; CNPJ no cadastro; prova em outra fonte (Meridiano: soma dos PIX do lojista = operações dele na Ponte; Aurora: o lojista tem vendas na Orbe no mês); confiança ≥ 0,8. Falhou qualquer item → vai para uma pessoa, com o motivo.
- **Não atua** em comissão, divergência, nota, remessa ou cadastro: tudo isso é regra determinística. A IA também não cria regra: o que ela acertou vira proposta em `saida/sugestoes_regra.csv` para alguém aprovar no mês seguinte.

## Limitações conhecidas

- **Alerta de antecipação só para lojista sem histórico** (D66). A antecipação pode cobrir recebíveis de meses anteriores, que não estão nos dados; checar todos os lojistas exige a agenda de recebíveis da Orbe. Com o critério do mês inteiro, o alerta seria alarme falso em 5 lojistas. Com mais tempo: ler a agenda de recebíveis. Se a pergunta do Theo (11:16) for respondida, o critério é revisto.
- **Conciliação Orbe × banco parcela por parcela fica de fora** (Q-M): os créditos da Orbe no Aurora são só classificados, até haver a agenda de recebíveis.
- **Dia útil só com os feriados nacionais por lei de 2026** (D59): Carnaval, Sexta-feira Santa e Corpus Christi não entram, e 2027 precisa ser acrescentado no `regras.yaml`.

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
