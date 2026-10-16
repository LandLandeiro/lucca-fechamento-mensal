# Diário

Log cronológico: hora, etapa, o que foi feito, como foi verificado, commit.

## 16/10/2026

### 19h40–20h20 · Exploração do data pack
- **Feito:** leitura dos 6 arquivos e do anexo do .eml, com scripts só de leitura fora do repositório. Formato, armadilhas, mapa arquivo→entregável, 22 ambiguidades ordenadas por R$, 9 perguntas, causa raiz.
- **Verificado:** truncamento da Orbe (1.001 linhas só fecham truncando, 0 arredondando) e taxa da Rota Global TX88428676 (4,09% × 3,59%), conferidos de forma independente pelo Lucca. Cruzamento banco × Ponte ao centavo (prova a duplicata PC-0926-0162).
- **Registro:** `docs/EXPLORACAO.md`.

### 20h20–20h30 · E0 — estrutura
- **Feito:** `.venv` (Python 3.12.10), `requirements.txt`, `pyproject.toml` (pacote em `src/`, pytest com `pythonpath=src`), esqueleto `src/tarvo/` (leitores com as armadilhas na docstring, cadastro, regras, cálculos, classificação, pendências, saída, modelo), CLI `python -m tarvo`, `regras.yaml` (só fatos SEI preenchidos), controles (`STATUS`, `DIARIO`, `DECISOES`), `CLAUDE.md` atualizado, comandos em `.claude/commands/`.
- **Verificado:** `python -m tarvo --help` ok; `python -m tarvo --dados data --saida saida` lista os 7 arquivos; `pytest`: 3 passed.
- **Commit:** `E0: estrutura, exploração registrada e controles`.
