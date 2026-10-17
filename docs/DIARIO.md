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

### 20h36–20h41 · Respostas do financeiro e correção de status
- **Feito:** perguntas foram para `#duvidas-hackathon-ai` (o `#tarvo-financeiro` não existe). Lucca postou 4 itens novos às 20:36 (Rota Global, Casa do Estudante, competência 08/2026, créditos sem origem); o resto já tinha sido perguntado por outros times. `regras.yaml`: status PENDENTE no lugar de null; tolerância de spread e tomador da NF de remessa SEI → ASSUMO; novo SEI "APROVADO C/ RESSALVA segue para liquidação"; CONFIRMADO para Helena 20:05 (base da comissão = contratada; divergência sem devolução automática), 20:06 (estorno) e 20:24 (mapeamento de 3 ECs; Atlas não fatura). `regras.py` passou a carregar e validar a estrutura. `HIPOTESES.md` preenchido (H01–H14, P01–P10). D07 e D08 em DECISOES; regra 3 do CLAUDE.md alinhada com D05.
- **Verificado:** `pytest`: 11 passed (inclui o `regras.yaml` real e as estruturas inválidas recusadas). Contagem: 38 regras (SEI 13, ASSUMO 2, CONFIRMADO 5, PENDENTE 18).
- **Em aberto:** textos literais das perguntas e respostas e quem perguntou estão como `[colar do Slack]` no HIPOTESES (não inventados).
- **Commit:** `registra respostas do financeiro e corrige status de premissas`.

### ~20h55 · Decisões do Lucca (divergência, truncamento, IA)
- **Feito:** D09 (truncar por transação, sem tolerância no checkout), D10 (divergência líquida com os estornos da própria venda no mês) e D11 (escopo e travas da IA, limiar 0,8) em DECISOES, `regras.yaml` (ASSUMO, `autor: Lucca`) e HIPOTESES (H10, H15, H16).
- **Verificado:** `pytest`: 11 passed; `regras.yaml` valida, com 40 regras (SEI 13, ASSUMO 7, CONFIRMADO 5, PENDENTE 15).
- **Commit:** `registra decisões de divergência, truncamento e uso de IA`.

### ~21h00–21h10 · Respostas do financeiro 20:47–20:58 e correção da D11
- **Feito:** `regras.yaml`: CONFIRMADO para a composição da comissão, a estrutura da NF de checkout, o tomador da NF de remessa (20:47), as regras de remessa (20:48 e 20:58), a Rota Global, a Casa do Estudante (taxa 0 com vigência 2026-09-01 a 2026-12-31) e a baixa de obrigações de 08/2026 (20:49). Créditos sem origem L50/L65/L92 como ASSUMO do Lucca. Tolerância de spread segue ASSUMO, aceita pela Helena (20:58). Removida `checkout.comissao_e_valor_taxa_integral`. D12 corrige a D11 (lado do lançamento pelo sinal do movimento; natureza D/C não rejeita). HIPOTESES: H07–H13 atualizadas, H17–H23 novas.
- **Verificado:** nos dados, a Orbe aplica 2,10% sobre o `valor_bruto` da linha de antecipação, truncado (44 linhas: 27 só truncamento, 17 ambos, 0 só arredondamento); as 6 reversões espelham a antecipação referenciada. `pytest`: 11 passed (2 testes que fixavam status antigos foram ajustados). 40 regras: CONFIRMADO 19, SEI 11, ASSUMO 7, PENDENTE 3.
- **Em aberto:** `docs/FINANCEIRO_SLACK.md` não existe no disco; os textos literais e o mapeamento P→Q no HIPOTESES aguardam o arquivo.
- **Commit:** `registra respostas do financeiro 20:47–20:58 e corrige D11`.
