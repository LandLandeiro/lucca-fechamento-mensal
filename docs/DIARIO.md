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

### Textos literais no HIPOTESES
- **Feito:** a seção de perguntas do HIPOTESES mapeia P01–P10 → Q-A…Q-F e acrescenta a P11 (Q-G, Fox AI 20:52). Os 7 blocos de pergunta e resposta foram copiados de `docs/FINANCEIRO_SLACK.md` sem edição, com a nota de autocorreção da Q-F.
- **Verificado:** 0 `[colar do Slack]` restantes; todas as linhas citadas (`>`) do arquivo aparecem idênticas no HIPOTESES. A primeira transação da Atlas na Orbe é de 10/09, o que confere com a Q-C.
- **Commit:** `HIPOTESES com textos literais do financeiro`.

### Fato confirmado × conta assumida (obrigações de 08/2026)
- **Feito:** `contabil.pagamento_de_obrigacao_do_mes_anterior` dividida em `contabil.obrigacoes_mes_anterior_fatos` (CONFIRMADO, Helena 20:49) e `contabil.obrigacoes_mes_anterior_contas` (ASSUMO, Lucca; base: os fatos + o plano de contas), no mesmo padrão dos créditos sem origem. Motivo: no texto literal da Q-F a Helena confirma os fatos e devolve a escolha das contas ("me diga como você lançaria"). HIPOTESES: H22 (fatos) e H24 (contas).
- **Verificado:** `pytest`: 11 passed; 41 regras (CONFIRMADO 19, SEI 11, ASSUMO 8, PENDENTE 3).
- **Commit:** `separa fato confirmado de conta assumida`.

### ~21h10–21h30 · E1 + E2: nível mínimo (comissão CHECKOUT + rastro + validador)
- **Feito:** `formatos.py` (decimal pt-BR, data, CNPJ 14 dígitos com DV, taxa número/texto exata); leitor Orbe (cabeçalho conferido; linha ilegível vira `linhas_invalidas`, nunca corrigida); leitor de taxas (aba e colunas pelo nome; rodapé e linhas fora do bloco viram aviso); cadastro (EC→CNPJ por igualdade exata: planilha + `cadastro.mapeamento_ec_confirmado`; vigência por texto); comissão CHECKOUT por transação (truncada, D09; estorno pela data da venda original; antecipação pela coluna "Antecipação"; reversão = −antecipação referenciada; condição especial da Casa lida do `regras.yaml`); Atlas → pendência; escritor e validador; CLI `python -m tarvo` (código 1 se o validador falhar).
- **Verificado:** `pytest`: 50 passed, com os casos pedidos (TX88428676 374,08 / TX88446419 −374,08; TX88444848 −83,12; Casa; Atlas; EC mapeado; CNPJ sem zero). Teste de mutação: trocar o truncamento por arredondamento derruba 4 testes. Total 207.031,31 = conferência independente da exploração (ver STATUS). Validador OK na saída real: as 1943 linhas da Orbe aparecem exatamente uma vez no rastro.
- **Incidente (registrado para MOMENTOS):** no teste de mutação, usei `git checkout --` para desfazer a troca, mas ele voltou o `comissoes.py` ao esqueleto da E0, que era a última versão commitada. Restaurei pela cópia feita antes da mutação e rodei os testes de novo (50 passed). Lição: mutação só com backup explícito, nunca com `git checkout` em arquivo não commitado.
- **Achado:** a Casa do Estudante fecha em −5,50, não em 0 (estorno de venda de agosto, fora da condição especial). Levado ao Lucca.
- **Commit:** `E1+E2: nível mínimo — comissão checkout com rastro e validador`.
