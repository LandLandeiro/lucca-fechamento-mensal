# Tarvo · fechamento de setembro/2026

[![CI](https://github.com/LandLandeiro/tarvo-fechamento/actions/workflows/ci.yml/badge.svg)](https://github.com/LandLandeiro/tarvo-fechamento/actions/workflows/ci.yml)

**O que o CI garante (a cada push):** o fechamento roda do zero num ambiente limpo, em Windows e Linux, com Python 3.12 e 3.14; os testes passam; e a saída gerada é idêntica, byte a byte, à commitada em `saida/`, sem chave de API (a IA responde pelo `cache_ia/`).

> Desafio Barte AI · Hackathon de AI Services · 16 e 17/10/2026 · time: [NOME DO TIME] (Lucca Rocha Landeiro)

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

## Como rodar do zero

**Pré-requisito:** Python **3.12 ou mais novo** (python.org; testado com 3.12.10) e Git. No Windows, o `python` que vem no PATH sem instalação é só um atalho da Microsoft Store (`Python was not found ...`, código 9009): instale o Python e chame o executável instalado, como abaixo.

No PowerShell, a partir de uma pasta qualquer:

```powershell
git clone <url-do-repositório> tarvo-fechamento
cd tarvo-fechamento

# 1. ambiente (troque o caminho se instalou o Python em outro lugar; com o "py launcher": py -3.12 -m venv .venv)
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv

# 2. dependências + o próprio pacote (o código fica em src/; sem o "-e ." o "python -m tarvo" não acha o módulo)
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .

# 3. fechamento (comando único) e testes
.\.venv\Scripts\python.exe -m tarvo --dados data --saida saida
.\.venv\Scripts\python.exe -m pytest
```

- `--dados` e `--saida` aceitam qualquer pasta, inclusive com espaço e acento (entre aspas). Sem `--regras`, vale o `regras.yaml` da raiz do repositório, de onde quer que se rode; `--regras <arquivo>` tem prioridade.
- Os comandos usam `.\.venv\Scripts\python.exe` direto, sem `Activate.ps1`: num Windows limpo a política de execução do PowerShell costuma bloquear o script de ativação.
- Saída esperada: lista de comissões, divergências, notas, lançamentos e pendências, terminando em `VALIDADOR: OK`, código de saída 0 (1 = saída inválida; 2 = erro de entrada). Os CSVs vão para `--saida`; o resultado é determinístico (mesmo hash a cada execução, em qualquer pasta).

Chaves necessárias: **nenhuma para reproduzir setembro.** As respostas da IA estão em `cache_ia/` (commitado): sem chave, o fechamento usa o cache e dá o mesmo resultado, sem custo. Com arquivos novos (outubro), a IA lê `ANTHROPIC_API_KEY` de `.env.local` (modelo em `.env.example`); sem chave e sem cache, as linhas sem regra ficam para uma pessoa (HUMANO + pendência), com aviso, e o programa termina normalmente. `--sem-ia` desliga a IA.

## Como a analista usa em outubro

[preencher]

## Onde a IA atua e onde não atua

- **Atua só** nos lançamentos de extrato que nenhuma regra do `regras.yaml` cobre (em setembro: 7 de 184). Ela sugere conta, lojista, justificativa e confiança, a partir de listas fechadas.
- **O código prova antes de aceitar:** conta lançável; CNPJ no cadastro; prova em outra fonte (Meridiano: soma dos PIX do lojista = operações dele na Ponte; Aurora: o lojista tem vendas na Orbe no mês); confiança ≥ 0,8. Falhou qualquer item → vai para uma pessoa, com o motivo.
- **Não atua** em comissão, divergência, nota, remessa ou cadastro: tudo isso é regra determinística. A IA também não cria regra: o que ela acertou vira proposta em `saida/sugestoes_regra.csv` para alguém aprovar no mês seguinte.

## Limitações conhecidas

[preencher]

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
