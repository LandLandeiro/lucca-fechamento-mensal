# Diário

Log cronológico: hora, etapa, o que foi feito, como foi verificado, commit.

## 16/10/2026

Horários de cada etapa: do commit anterior até o último commit da etapa (`git log --date=format:%H:%M`), alinhados em 17/10 13h. Antes, algumas entradas tinham hora estimada à mão.

### 16/10 ~19:40–20:20 (sem commit: scripts só de leitura fora do repositório) · Exploração do data pack
- **Feito:** leitura dos 6 arquivos e do anexo do .eml, com scripts só de leitura fora do repositório. Formato, armadilhas, mapa arquivo→entregável, 22 ambiguidades ordenadas por R$, 9 perguntas, causa raiz.
- **Verificado:** truncamento da Orbe (1.001 linhas só fecham truncando, 0 arredondando) e taxa da Rota Global TX88428676 (4,09% × 3,59%), conferidos de forma independente pelo Lucca. Cruzamento banco × Ponte ao centavo (prova a duplicata PC-0926-0162).
- **Registro:** `docs/EXPLORACAO.md`.

### 16/10 19:39–20:32 · E0 — estrutura
- **Feito:** `.venv` (Python 3.12.10), `requirements.txt`, `pyproject.toml` (pacote em `src/`, pytest com `pythonpath=src`), esqueleto `src/tarvo/` (leitores com as armadilhas na docstring, cadastro, regras, cálculos, classificação, pendências, saída, modelo), CLI `python -m tarvo`, `regras.yaml` (só fatos SEI preenchidos), controles (`STATUS`, `DIARIO`, `DECISOES`), `CLAUDE.md` atualizado, comandos em `.claude/commands/`.
- **Verificado:** `python -m tarvo --help` ok; `python -m tarvo --dados data --saida saida` lista os 7 arquivos; `pytest`: 3 passed.
- **Commit:** `E0: estrutura, exploração registrada e controles`.

### 16/10 20:32–20:41 · Respostas do financeiro e correção de status
- **Feito:** perguntas foram para `#duvidas-hackathon-ai` (o `#tarvo-financeiro` não existe). Lucca postou 4 itens novos às 20:36 (Rota Global, Casa do Estudante, competência 08/2026, créditos sem origem); o resto já tinha sido perguntado por outros times. `regras.yaml`: status PENDENTE no lugar de null; tolerância de spread e tomador da NF de remessa SEI → ASSUMO; novo SEI "APROVADO C/ RESSALVA segue para liquidação"; CONFIRMADO para Helena 20:05 (base da comissão = contratada; divergência sem devolução automática), 20:06 (estorno) e 20:24 (mapeamento de 3 ECs; Atlas não fatura). `regras.py` passou a carregar e validar a estrutura. `HIPOTESES.md` preenchido (H01–H14, P01–P10). D07 e D08 em DECISOES; regra 3 do CLAUDE.md alinhada com D05.
- **Verificado:** `pytest`: 11 passed (inclui o `regras.yaml` real e as estruturas inválidas recusadas). Contagem: 38 regras (SEI 13, ASSUMO 2, CONFIRMADO 5, PENDENTE 18).
- **Em aberto:** textos literais das perguntas e respostas e quem perguntou estão como `[colar do Slack]` no HIPOTESES (não inventados).
- **Commit:** `registra respostas do financeiro e corrige status de premissas`.

### 16/10 20:41–20:58 · Decisões do Lucca (divergência, truncamento, IA)
- **Feito:** D09 (truncar por transação, sem tolerância no checkout), D10 (divergência líquida com os estornos da própria venda no mês) e D11 (escopo e travas da IA, limiar 0,8) em DECISOES, `regras.yaml` (ASSUMO, `autor: Lucca`) e HIPOTESES (H10, H15, H16).
- **Verificado:** `pytest`: 11 passed; `regras.yaml` valida, com 40 regras (SEI 13, ASSUMO 7, CONFIRMADO 5, PENDENTE 15).
- **Commit:** `registra decisões de divergência, truncamento e uso de IA`.

### 16/10 20:58–21:09 · Respostas do financeiro 20:47–20:58 e correção da D11
- **Feito:** `regras.yaml`: CONFIRMADO para a composição da comissão, a estrutura da NF de checkout, o tomador da NF de remessa (20:47), as regras de remessa (20:48 e 20:58), a Rota Global, a Casa do Estudante (taxa 0 com vigência 2026-09-01 a 2026-12-31) e a baixa de obrigações de 08/2026 (20:49). Créditos sem origem L50/L65/L92 como ASSUMO do Lucca. Tolerância de spread segue ASSUMO, aceita pela Helena (20:58). Removida `checkout.comissao_e_valor_taxa_integral`. D12 corrige a D11 (lado do lançamento pelo sinal do movimento; natureza D/C não rejeita). HIPOTESES: H07–H13 atualizadas, H17–H23 novas.
- **Verificado:** nos dados, a Orbe aplica 2,10% sobre o `valor_bruto` da linha de antecipação, truncado (44 linhas: 27 só truncamento, 17 ambos, 0 só arredondamento); as 6 reversões espelham a antecipação referenciada. `pytest`: 11 passed (2 testes que fixavam status antigos foram ajustados). 40 regras: CONFIRMADO 19, SEI 11, ASSUMO 7, PENDENTE 3.
- **Em aberto:** `docs/FINANCEIRO_SLACK.md` não existe no disco; os textos literais e o mapeamento P→Q no HIPOTESES aguardam o arquivo.
- **Commit:** `registra respostas do financeiro 20:47–20:58 e corrige D11`.

### 16/10 21:09–21:12 · Textos literais no HIPOTESES
- **Feito:** a seção de perguntas do HIPOTESES mapeia P01–P10 → Q-A…Q-F e acrescenta a P11 (Q-G, Fox AI 20:52). Os 7 blocos de pergunta e resposta foram copiados de `docs/FINANCEIRO_SLACK.md` sem edição, com a nota de autocorreção da Q-F.
- **Verificado:** 0 `[colar do Slack]` restantes; todas as linhas citadas (`>`) do arquivo aparecem idênticas no HIPOTESES. A primeira transação da Atlas na Orbe é de 10/09, o que confere com a Q-C.
- **Commit:** `HIPOTESES com textos literais do financeiro`.

### 16/10 21:12–21:13 · Fato confirmado × conta assumida (obrigações de 08/2026)
- **Feito:** `contabil.pagamento_de_obrigacao_do_mes_anterior` dividida em `contabil.obrigacoes_mes_anterior_fatos` (CONFIRMADO, Helena 20:49) e `contabil.obrigacoes_mes_anterior_contas` (ASSUMO, Lucca; base: os fatos + o plano de contas), no mesmo padrão dos créditos sem origem. Motivo: no texto literal da Q-F a Helena confirma os fatos e devolve a escolha das contas ("me diga como você lançaria"). HIPOTESES: H22 (fatos) e H24 (contas).
- **Verificado:** `pytest`: 11 passed; 41 regras (CONFIRMADO 19, SEI 11, ASSUMO 8, PENDENTE 3).
- **Commit:** `separa fato confirmado de conta assumida`.

### 16/10 21:13–21:22 · E1 + E2: nível mínimo (comissão CHECKOUT + rastro + validador)
- **Feito:** `formatos.py` (decimal pt-BR, data, CNPJ 14 dígitos com DV, taxa número/texto exata); leitor Orbe (cabeçalho conferido; linha ilegível vira `linhas_invalidas`, nunca corrigida); leitor de taxas (aba e colunas pelo nome; rodapé e linhas fora do bloco viram aviso); cadastro (EC→CNPJ por igualdade exata: planilha + `cadastro.mapeamento_ec_confirmado`; vigência por texto); comissão CHECKOUT por transação (truncada, D09; estorno pela data da venda original; antecipação pela coluna "Antecipação"; reversão = −antecipação referenciada; condição especial da Casa lida do `regras.yaml`); Atlas → pendência; escritor e validador; CLI `python -m tarvo` (código 1 se o validador falhar).
- **Verificado:** `pytest`: 50 passed, com os casos pedidos (TX88428676 374,08 / TX88446419 −374,08; TX88444848 −83,12; Casa; Atlas; EC mapeado; CNPJ sem zero). Teste de mutação: trocar o truncamento por arredondamento derruba 4 testes. Total 207.031,31 = conferência independente da exploração (ver STATUS). Validador OK na saída real: as 1943 linhas da Orbe aparecem exatamente uma vez no rastro.
- **Incidente (registrado para MOMENTOS):** no teste de mutação, usei `git checkout --` para desfazer a troca, mas ele voltou o `comissoes.py` ao esqueleto da E0, que era a última versão commitada. Restaurei pela cópia feita antes da mutação e rodei os testes de novo (50 passed). Lição: mutação só com backup explícito, nunca com `git checkout` em arquivo não commitado.
- **Achado:** a Casa do Estudante fecha em −5,50, não em 0 (estorno de venda de agosto, fora da condição especial). Levado ao Lucca.
- **Commit:** `E1+E2: nível mínimo — comissão checkout com rastro e validador`.

### 16/10 21:22–21:34 · Decisões do mínimo e momentos de IA
- **Feito:** Lucca manteve Casa −5,50 e aprovou `COM-<cnpj>-CHECKOUT` e as colunas extras. Saída em ordem determinística (comissão decrescente, depois CNPJ; rastro por `id_saida` e linha). Registrada a conferência independente do Lucca (outra sessão, sem ver o código: 21 lojistas no centavo, 207.031,31, 57 pendentes, 1.943 linhas). `PROMPTS/MOMENTOS.md` com 3 entradas. A separação fatos/contas das obrigações de 08/2026 já estava feita (commit `56da90a`).
- **Verificado:** `pytest`: 51 passed (novo teste de ordem); duas execuções seguidas geram `rastro.csv` com o mesmo hash.
- **Commit:** `decisões do mínimo e momentos de IA`.

### 16/10 21:34–21:38 · E5a: divergências de checkout
- **Feito:** `calculos/divergencias.py`: diferença = `valor_taxa` Orbe − comissão contratada (a mesma da E2, com a mesma taxa e fonte). Venda líquida com os estornos dela (D10) e reversão líquida com a antecipação (D17, a confirmar); só lista se ≠ 0 (tolerância 0, D09). Casa entra, Atlas fica fora. `divergencias_taxa.csv` com as colunas do case e extras (lojista, data, valor_bruto, comissao_contratada, valor_taxa_orbe, direcao, liquida_com, motivo com a fonte da taxa, decisao=Helena). Validador: conservação (Σ `valor_taxa` = Σ comissão + Σ divergências), divergência só aponta linha que está numa comissão, e cobertura contando só COM-/PEN-.
- **Verificado:** 200 divergências, R$ 16.973,00; conservação 224.004,31 = 207.031,31 + 16.973,00, igual à previsão independente. Rota 1.546,28 e Bridge 29,95 iguais à exploração. Hand-check: TX88423647 (66,28), TX88428053 (4,49), AN88445802 (1.206,58). `pytest`: 65 passed.
- **Bugs achados e corrigidos (teste antes da correção):** (1) zero negativo (`-0.00`) no rastro da Casa (−1.021,01 × 0): o formatador agora escreve `0.00`; (2) a CLI caía com código 1 num console cp1252 por causa do "Σ" (só tinha passado porque eu forcei UTF-8 no terminal): D18.
- **Commit:** `E5a: divergências de checkout com conservação validada`.

### 16/10 21:38–21:50 · E4: comissão e divergências de REMESSA
- **Feito:** leitor do .eml (stdlib `email`) e do anexo (aba pelo cabeçalho "Nº Operação", colunas pelo nome, competência lida do relatório, totais declarados conferidos). `calculos/remessa.py`: destino de cada linha (competência pela contratação → duplicata → spread negativo → cadastro → elegível) e comissão 50% × Spread R$ com ROUND_HALF_EVEN por operação (D19). Divergência de remessa no valor cheio, com o aplicado recalculado de TC e PTAX (D22), padrão 1,5% e tolerância 0,005 p.p. Exclusões anotadas no rastro como EXC- (D23). Validador com cobertura por (ref, linha) e conservação da remessa. Correção de bug latente: condição especial da Casa não vale para o spread de remessa (D24).
- **Verificado:** 233 linhas = 228 elegíveis + 1 duplicata + 4 negativos; Σ Spread 78.073,59 = declarado. Comissão 39.542,89. Hand-check PC-0926-0011: (4,0920 − 4,0315) × 2.438,46 − 1,2% × 4,0315 × 2.438,46 = 147,5268 − 117,9666 = 29,56. PC-0926-0002: 50% × 262,01 = 131,005 → 131,00 (meio → par). `pytest`: 83 passed.
- **A confirmar com o Lucca:** D21 (divergência do spread negativo pela fórmula: −3.565,99; pelo spread: −1.834,05), D20 (arredondamento da divergência).
- **Commit:** `E4: comissão e divergências de remessa`.

### 16/10 21:50–22:00 · Decisões D17/D20/D21/D22 e E6a: notas a emitir
- **Feito:** D22: divergência de remessa = Spread R$ − contratado × PTAX × ME (mesma base da comissão). D21: `impacto_repasse_tarvo` = 50% × Spread R$ nos negativos, motivo novo. D17 e D20 confirmadas (D17 virou a regra `divergencias.reversao_liquida_com_antecipacao`, lida pelo código). `calculos/notas.py`: 1 nota por lojista com comissão CHECKOUT > 0, 1 nota REMESSA para a Ponte; discriminação em `notas.discriminacao` com a competência dos dados; nota negativa → pendência NF_NEGATIVA; pendência CONFERENCIA_REPASSE calculada (participação × total declarado × nota, decomposta pelas exclusões; data do TED lida do e-mail). Validador: notas = comissões e nenhuma nota ≤ 0; pendências derivadas fora da cobertura.
- **Verificado:** Mundo Aberto 1.418,88; negativos −3.565,98 (Canguru −1.001,29); impacto −917,03; 21 notas (207.036,81 + 39.542,89); conferência 39.036,80 × 39.542,89 = 506,09 = 917,03 − 410,94, todos iguais aos números previstos pelo Lucca. `pytest`: 91 passed.
- **Bugs achados e corrigidos:** (1) o validador dava exceção (InvalidOperation) com vírgula decimal em vez de reportar erro: D26; (2) uma substituição em lote quebrou duas f-strings da CLI (`
` virou quebra de linha real); a CLI não rodava e foi corrigida antes do commit.
- **Commit:** `D21/D22 e E6a: notas a emitir com conferência do repasse`.

### 16/10 22:00–22:13 · Respostas Q-H/Q-I/Q-J: arredondamento comum
- **Feito:** Q-H, Q-I e Q-J em `docs/FINANCEIRO_SLACK.md` (literal). `regras.yaml`: arredondamento comum (ROUND_HALF_UP) por linha CONFIRMADO para a comissão de checkout, as divergências e os 50% da remessa, **corrigindo o ASSUMO de truncar (D09)** e o HALF_EVEN (D19/D20) → D27; tolerância 0 do checkout removida, divergência de checkout = round(bruto × (aplicada − contratada)) só onde as taxas diferem; divergência de remessa volta à coluna "Spread %" (D28); Q-I CONFIRMADO (obrigações de agosto e despesas diretas); Q-J pendência EXCESSO_REMESSA (D30). Arredondamento num só lugar (`formatos.modo_arredondamento`, lido do `regras.yaml`). Validador: divergência recalculada da fonte, resíduo de truncamento por linha (D29). Conferência do repasse com o terceiro componente (arredondamento).
- **Verificado:** todos os números bateram no centavo com a previsão independente do Lucca antes do commit: checkout 207.039,73 (Bridge 11.916,02; Casa −5,50); divergências checkout 200 · 16.973,65 (Casa 15.397,42; Rota 1.546,28; Bridge 29,95); resíduo −9,07; remessa 39.543,45; Mundo Aberto 1.418,85; negativos −3.565,98; notas CHECKOUT 20 · 207.045,23; nota REMESSA 39.543,45; conferência 506,65 = 917,03 − 410,94 + 0,56. `pytest`: 94 passed.
- **Ponto levado ao Lucca:** o pedido dizia "|resíduo por linha| < 0,01"; truncar × arredondar dá exatamente 0,01 em 969 linhas, então o critério implementado é ≤ 0,01 (D29). Um teste novo errou o exemplo (escolhi uma linha da Casa, que tem taxa 0) e foi corrigido para a L6 TX88410316.
- **Commit:** `Q-H/Q-I/Q-J: arredondamento comum, resíduo de truncamento e excesso da remessa`.

### 16/10 22:13–22:24 · E6b parte 1: extratos classificados só por regra
- **Feito:** leitores do Aurora (UTF-8 com fallback Latin-1, linhas de dado pelo conteúdo, saldos e saldo corrido), do Meridiano (OFX pelo CHARSET do cabeçalho, FITID e linha física) e do plano de contas (lançáveis = ANALITICA + ACEITA_LANCTO=S). `classificacao_extratos` no `regras.yaml`: 26 regras por padrão de descrição, com sinal, sem número de linha (D32); as regras antigas por linha saíram. Lojista no extrato por prefixo exato (D31). Conferências: transferências entre contas, aportes × Ponte, aplicação × resgate em FIFO. Validador: cada lançamento uma vez, Σ Aurora = final − inicial, contas lançáveis, HUMANO sem conta.
- **Verificado:** 184 lançamentos (84 + 100), 174 por regra, 10 HUMANO; Σ Aurora −2.532.423,41 = saldo final − saldo anterior; 3 transferências casadas no mesmo dia e L92 sem par; Ponte Aérea 18.240,00 sem operação; resgate de 09/09 com excesso de 392,00. `pytest`: 143 passed (cada regra com um caso de setembro).
- **Alarme falso evitado:** a 1ª execução acusou divergência de aportes de −394.222,69 da EduAbroad, mas os aportes dela só não tinham sido identificados (nome do banco "EDU ABROAD"); somados à mão, batem com as operações. Lojista sem aporte identificado, havendo PIX RECEB sem regra, agora fica "não conferido" (D33).
- **Commit:** `E6b parte 1: extratos classificados por regra, com conferências`.

### 16/10 22:24–22:27 · Decisões da E6b parte 1
- **Feito:** H36: EduAbroad sem alias; plano da parte 2 registrado (D37). H37: regra RENDIMENTO APLIC → 3.2.01. H38: resgate de 392,00 acima do aplicado fica em 1.1.02.001, sem pendência (saldo aplicado anterior a 01/09, D36). Atlas: lojistas do extrato = planilha vigente ∪ nomes da Orbe dos ECs sem vínculo (D35); L34 e L60 → 2.1.01.001 por regra; pendência de faturamento mantida.
- **Verificado:** 7 linhas sem regra (só EduAbroad), como esperado. `pytest`: 148 passed. Validador OK.
- **Diferenças levadas ao Lucca:** (1) a união com **todos** os nomes da Orbe resolveria também a EduAbroad ("EDU ABROAD CONSULTORIA" é o nome da Orbe do EC dela), contra a D37 e o esperado; restringi aos ECs sem vínculo. (2) Pendências: **15**, não 16 (eram 19; saíram 3 SEM_REGRA — L34, L60, MRD2026090680 — e a do resgate).
- **Commit:** `decisões da E6b parte 1: rendimento, resgate, Atlas e plano da EduAbroad`.

### 16/10 22:27 – 17/10 00:28 · Respostas Q-K, Q-L, Q-M
- **Feito:** Q-K, Q-L e Q-M no FINANCEIRO_SLACK, no HIPOTESES (P15–P17, H40–H42, H26, "Fica de fora") e no `regras.yaml`. Q-K: CONFERENCIA_REPASSE reescrita sem prever desconto (valor = faturado, rastro = linhas da nota REMESSA); coluna `participacao_tarvo_no_spread` (D38). Q-L: módulo `calculos/contestacao.py`, 3 pendências CONTESTACAO_PONTE e extra `saida/contestacao_ponte.csv` (D39); validador confere Σ por pendência. Q-M: `orbe_recebivel` CONFIRMADO; saldo negativo e conciliação por parcela fora.
- **Verificado:** Mundo Aberto 23 ops = 1.418,85 (mesmo número da divergência); negativos 4 ops = −1.834,05 (Σ Spread R$; −3.565,98 contra o contrato); duplicata R77 = 821,88; a R76 continua em COM- e a R77 em EXC- (conta uma vez). Pendências 15 → 18. `pytest`: 151 passed (testes novos: TED sem desconto, coluna renomeada, contestação por motivo, validador recusa contestação que não fecha). Validador OK.
- **Commit:** `Q-K/Q-L/Q-M: conferência do TED sem desconto, contestação com a Ponte e créditos da Orbe`.

### 17/10 00:28–00:34 · Teste de reprodutibilidade
- **Feito:** clone em `%TEMP%\tarvo-repro`, seguindo o README como avaliador num Windows sem Python no PATH. Achados: (1) a seção "Como rodar do zero" do README estava vazia (`[preencher]`); (2) `python` do PATH = atalho da Store (código 9009); (3) sem `pip install -e .` → "No module named tarvo"; (4) fora da raiz sem `--regras` → código 2 (`regras.yaml` relativo à pasta atual); (5) `Activate.ps1` costuma estar bloqueado num Windows limpo; (6) o README não dizia se roda sem chave (roda: a IA ainda não está ligada). README corrigido com pré-requisito, passos, comando único, saída esperada e esses avisos (D40). Código não mudou.
- **Verificado:** duas execuções no clone + `saida/` commitada no clone + `saida/` do projeto: SHA-256 idêntico nos 7 CSVs. Com `--dados "%TEMP%\teste ação\dados"` e `--saida "%TEMP%\teste ação\saída com espaço"` rodando de fora do repo (com `--regras`): código 0, validador OK, 7 CSVs idênticos. Segundo clone seguindo o README novo ao pé da letra: código 0, `pytest` 151 passed, `git status` sem mudança em `saida/`.
- **Commit:** `teste de reprodutibilidade`.

### 17/10 00:34–00:37 · regras.yaml padrão relativo ao repositório
- **Feito:** padrão de `--regras` resolvido a partir do pacote (raiz do repo), não da pasta atual; `--regras` explícito continua com prioridade (D41). Aviso de "rodar na raiz" removido do README.
- **Verificado:** teste novo primeiro (falhou: código 2), depois a correção: rodar de fora do repo sem `--regras`, com `--saida` com espaço e acento, dá código 0 e validador OK; `--regras` explícito inexistente dá código 2 (prioridade). `pytest`: 153 passed.
- **Commit:** `regras.yaml padrão relativo ao repositório`.

### 17/10 00:40–08:37 · E6b parte 2: IA nas sobras
- **Feito:** conferi o SDK instalado (`anthropic` 1.15.0, pydantic 2.14.1) e a forma documentada de saída estruturada (`messages.parse(output_format=<BaseModel>)` → `.parsed_output`; junta `output_config` com o formato). `classificacao/por_ia.py`: prompt versionado (`src/tarvo/prompts/classificar_lancamento.md`, D43), chave do `.env.local` (nunca impressa), cache `cache_ia/`, verificação (a)–(d), aplicação nas linhas e pendências, aportes aceitos na conferência, `sugestoes_regra.csv`; `--sem-ia`; regras `classificacao.modelo_ia` e `classificacao.verificacao_ia` (D42).
- **Testes sem rede (`tests/test_ia.py`):** cliente mockado (i) válido → IA + cache + reexecução sem chamadas; (ii) conta inexistente → HUMANO (a); (iii) confiança 0,5 → HUMANO (d); (iv) aportes atribuídos à Mundo Aberto → Σ não bate → HUMANO (c); conta de aporte sem lojista → HUMANO (b); sem chave e sem cache → HUMANO + aviso; `--sem-ia` → exit 0; chave lida do arquivo e nunca impressa. `conftest` liga `TARVO_SEM_REDE`.
- **Execução real (uma vez):** 7 chamadas, 18.118 + 2.379 tokens, ~US$ 0,003. 5 aportes EduAbroad aceitos (Σ 394.222,69 = Ponte); L28 e L69 recusados: a IA não ligou "EDU ABROAD CONSULTORIA LTD" à EduAbroad (confiança 0,5 e 0,4). Não mexi no prompt para forçar outra resposta.
- **Verificado:** segunda execução 0 chamadas (cache), SHA-256 dos 8 CSVs iguais; a chave não aparece em `cache_ia/` nem em `saida/`; validador OK (agora também exige confiança em linha IA); pendências 18 → 13; `pytest`: 161 passed.
- **Commit:** `E6b parte 2: IA nas sobras, verificada pelo código, com cache`.

### 17/10 08:37–08:43 · Decisões da E6b parte 2
- **Feito:** L28 e L69 por decisão humana do Lucca (`decisoes_humanas` no `regras.yaml`, uma por linha, aplicadas só à linha exata e antes da IA): 2.1.01.001 EduAbroad, metodo HUMANO, confiança vazia; pendências IA_REPROVADA saíram. SUG-001 aprovada: `classificacao_extratos.aliases_lojista` "EDU ABROAD CONSULTORIA" → 16181276000153, Aurora e Meridiano, vigência 2026-10-01; `sugestoes_regra.csv` marca APROVADA. Validador: HUMANO com conta só com decisão explícita; HUMANO sem confiança (D44).
- **Verificado:** alias casa por REGRA com data de outubro (Aurora e Meridiano) e não casa em setembro; decisão com valor diferente não se aplica (vira aviso); validador recusa HUMANO com conta sem decisão. Setembro: 5 IA + 2 decisão humana; pendências 13 → 11; IA com 5 sobras, 0 chamadas. Reexecução: SHA-256 dos 8 CSVs iguais. `pytest`: 168 passed.
- **Commit:** `decisões da E6b parte 2: L28/L69 por decisão humana e alias da EduAbroad para outubro`.

### 17/10 08:43–09:07 · Auditoria antes do Checkpoint 1
- **Feito:** `scripts/auditar_saida.py`, que lê só `saida/` e `data/` (stdlib + openpyxl, sem o pacote): formato contra o case, coerência entre arquivos e origem de cada linha do rastro. `docs/CONFORMIDADE.md`: matriz Q-A…Q-M (trecho literal → regra → saída → teste). `docs/AUDITORIA.md`: itens 1–5. Impacto em R$ das ASSUMO medido com cenários alternativos. Correções só de documentação: H07, H30 (substituída pela H40), H35, H36, STATUS, README. Nenhum cálculo alterado.
- **Verificado:** o script acusou as 7 mutações de uma cópia estragada (BOM, CRLF, vírgula, data, DV, confiança, rastro). Ele também quebrava com decimal malformado, o mesmo erro do validador na D26; corrigi antes de usar. Saída real: formato sem violação; ⚠️ `;` entre aspas em textos (inclusive `motivo` de `pendencias.csv`); 1 violação de coerência (linha `arredondamento` −0,03 da PEN-EXCESSO_REMESSA, que contradiz a Q-H "linha por linha, e depois soma": 709,43 × 709,46). "Rastro de 100%" segue desmarcado, com o que falta.
- **Para o Lucca:** metade do excesso por operação; `;` nos textos; regra PENDENTE `divergencias.data_referencia_vigencia` sem uso; levar a checagem de origem para o validador.
- **Commit:** `auditoria antes do Checkpoint 1: conformidade, formato e coerência`.

### 17/10 09:07–09:12 · Decisões da auditoria (D45)
- **Feito:** metade do excesso por operação (709,46; sem linha de arredondamento); escritor sem `;` em campo (`;` → `,`) e validador recusando `;` em qualquer CSV; `divergencias.data_referencia_vigencia` removida (coberta pela Q-B); validador conferindo a origem de toda linha do rastro contra as quatro fontes; teste de saldo negativo do Aurora (Q-M). AUDITORIA, CONFORMIDADE, STATUS, HIPOTESES (H34), regras (texto do excesso) atualizados.
- **Verificado:** testes novos primeiro (4 falharam; o do saldo negativo já passava e fica como proteção), depois a correção. `pytest`: 172 passed. CLI: exit 0, validador OK. `scripts/auditar_saida.py`: 0 violações, 0 avisos. Comissões, divergências, notas e lançamentos iguais; só a EXCESSO_REMESSA (+0,03) e textos mudaram. Reexecução: hashes iguais. "Rastro de 100%" marcado no STATUS.
- **Commit:** `decisões da auditoria: excesso por operação, sem ';' em campo, origem de todo o rastro`.

### 17/10 09:12–09:15 · CI no GitHub Actions (D46)
- **Feito:** `.github/workflows/ci.yml` (push; Ubuntu e Windows × Python 3.12 e 3.14; instala, testa, roda o fechamento sem chave com `TARVO_SEM_REDE=1`, `git diff --exit-code saida/`); selo e o que o CI garante no topo do README.
- **Verificado:** as 4 execuções do `34b84fd` ficaram verdes (Ubuntu e Windows, Python 3.12 e 3.14; de 27 s a 1 min), conferido pelo Lucca na aba Actions.
- **Commit:** `CI no GitHub Actions: Windows e Linux, 3.12 e 3.14, saída idêntica sem chave`.

### 17/10 09:15–09:23 · Dependências no pyproject (D47)
- **Feito:** `dependencies` no `pyproject.toml` (iguais ao `requirements.txt`, mantido); README e CI só com `pip install -e .`.
- **Verificado:** venv novo, só `pip install -e .`: dependências importam e `pytest` 172 passed.
- **Commit:** `dependências no pyproject: pip install -e . instala tudo`.

### 17/10 09:23–09:28 · Prova de outubro (parcial: parado antes de corrigir)
- **Feito:** varredura de datas fixas em `src/`; `tests/fixtures/gerar_outubro.py` (determinístico) gera `tests/fixtures/outubro/` (DADO SINTÉTICO DE TESTE: setembro deslocado um mês, ids com o mês renumerados, + EC novo, estorno da Bridge de venda de 05/09, TED de 300 mil em 01/10, PIX da EduAbroad); `tests/test_outubro.py` (8 testes, ponta a ponta). Nenhuma linha do código da solução mudou.
- **Verificado (item c, todos ✅):** exit 0 e validador OK; competência 10/2026 nas 21 notas; Casa com taxa contratada 0 nas 119 linhas; EC novo → PEN-EC_SEM_CADASTRO-EC1099000001 (71,87), sem quebrar; estorno TX89500001 da Bridge pela taxa antiga 2,59% (−37,86; pela nova seria −32,01), sem divergência; 7 lançamentos da EduAbroad por REGRA (alias), 0 linhas para a IA; TED de 300 mil por REGRA (`meridiano.mesma_titularidade`, 1.1.09.001). `pytest`: 180 passed.
- **Falhou (item a):** duas strings com mês fixo no código: `conferencias.py` ("cai no Meridiano em 01/10 [...] conferir no extrato de outubro", quem decide "analista (conferir em outubro)") e `divergencias.py` ("A nota de setembro sai pelo realizado"). Na saída de outubro, a pendência L92 diz "conferir em outubro". Parado para o Lucca decidir antes de corrigir; itens d e f não feitos. Em `regras.yaml`, `resgate_acima_do_aplicado: SALDO_APLICADO_ANTERIOR` é premissa de setembro (D36) que vale em todo mês.
- **Commit:** `fixture e teste de outubro (dado sintético), sem mudar o código da solução`.

### 17/10 09:28–09:38 · Prova de outubro concluída (D48–D50)
- **Feito:** textos com mês derivado da data (transferência em trânsito, excesso, resgate) e `formatos.nome_mes` (D48); resgate acima do aplicado condicional à linha de rendimento do mês, refinando a D36 (D49); flag `--pendencias-anteriores` com `pendencias_resolvidas.csv` (D50); testes: outubro sem "setembro" nas pendências, em trânsito cita "novembro", excesso cita "outubro", flag com e sem, resgate com e sem rendimento. README "Fechando outubro"; STATUS "roda em outubro" marcado; H38 atualizada.
- **Verificado:** setembro: só o texto da pendência L92 mudou ("cai no Meridiano no dia útil seguinte"); demais números e arquivos iguais. Outubro: exit 0, validador OK, `scripts/auditar_saida.py` 0 violações (setembro e outubro); com a flag, a L92 de setembro sai como "pendência de setembro resolvida" (MRD2026100001) e a TRANSFERENCIA_SEM_ORIGEM some (12 → 11 pendências). `pytest`: 186 passed.
- **Commit:** `outubro sem retrabalho: textos com mês derivado, resgate condicional e pendências anteriores`.

### 17/10 09:38–09:43 · Requisito de entrega da organização (D51)
- **Feito:** mensagem da organização (09:21) em `docs/FINANCEIRO_SLACK.md`; README com "Como a banca roda" no topo, seção "Chave de API" e extras listados; resumo do fechamento no fim da CLI (`formatos.fmt_brl`); teste do resumo.
- **Verificado:** nenhuma chave real no repositório (`git ls-files`: só `.env.example`, com a chave vazia; `git grep "sk-ant"`: nada). Os 6 arquivos com os nomes exatos do case; extras: `contestacao_ponte.csv`, `sugestoes_regra.csv` e, com a flag, `pendencias_resolvidas.csv`. CSVs de `saida/` iguais. `pytest`: 187 passed.
- **Commit:** `requisito de entrega: README (banca, chave de API, extras) e resumo do fechamento na tela`.

### 17/10 09:43–09:49 · Documentação para a banca
- **Feito:** `docs/CAUSA_RAIZ.md` (para o CFO: Casa, Rota, Bridge, Mundo Aberto, Atlas e a planilha, com as frases da Helena; por que o processo não pega; o que a solução muda; proposta de processo em 3 itens). `PROMPTS/MOMENTOS.md` reescrito com os 4 momentos mais fortes e os demais em resumo. README: tabela "Para a banca: onde ver cada critério". Cálculo e saída não mudaram.
- **Verificado:** todo número da causa raiz recalculado de `saida/` (Casa 116 · 15.397,42; Rota 79 · 1.546,28; Bridge 5 · 29,95; Mundo Aberto 23 · 1.418,85; metade 709,46; Atlas 7.876,05 e 57 transações; repasses L34 e L60) e os 9 `id_saida` citados existem; commits citados no MOMENTOS conferidos.
- **Commit:** `documentação para a banca: causa raiz, momentos e onde ver cada critério`.

### 17/10 09:49–10:47 · Resumo das hipóteses
- **Feito:** seção "Resumo" no topo do `HIPOTESES.md` (premissas por status, as 5 ASSUMO de maior impacto em R$ com o que muda se estiverem erradas, perguntas feitas × respostas de outros times aproveitadas); a H30 (substituída) foi para "Histórico (substituídas)" no fim, sem apagar nada.
- **Verificado:** 43 linhas H continuam no arquivo (26 CONFIRMADO, 15 ASSUMO, 1 SEI, 1 substituída); valores tirados de `docs/AUDITORIA.md` item 4. Cálculo e saída não mudaram.
- **Commit:** `HIPOTESES: resumo no topo e histórico das substituídas`.

### 17/10 10:47–11:53 · Correções da avaliação simulada (D52–D62)
- **Feito:** avaliação simulada da banca (sessão nova, sem contexto) em `docs/AVALIACAO_SIMULADA.md`; os scripts da verificação independente (outra sessão de IA) em `scripts/verificacao_independente/`. Onze correções, uma por commit, cada uma com teste: correção da D35, regra primeiro (D52); divergência de checkout como pendência por lojista (D53); confiança nunca vazia (D54); `ref_origem` das pendências só com ids (D55); bug da confiança com 3 casas no cache (D56); nota bloqueada em vez de valor parcial (D57); prefixo de uma palavra não casa (D58); feriados nacionais (D59); spread negativo pela Observação (D60); condições especiais em lista (D61); linha da Orbe fora da competência (D62).
- **Verificado:** setembro antes × depois: comissões (207.039,73 + 39.543,45), divergências (227 linhas), notas (21, 246.588,68), lançamentos (184, valores iguais) e contestação (28) **iguais**; mudou: lançamentos REGRA 177 → 184 (IA 5 → 0, HUMANO 2 → 0), pendências 11 → 14 (+3 DIVERGENCIA_CHECKOUT, 16.973,65), `ref_origem` das pendências, `sugestoes_regra.csv` 1 → 0 linhas, texto da fonte da taxa nas 116 divergências da Casa. `pytest`: 221 passed. `scripts/auditar_saida.py`: 0 violações. Os testes novos dos bugs (D56, D58) falhavam no código anterior.
- **Commits:** `c4d0944` · `8fdb36c` · `2239735` · `e62edb9` · `710b793` · `01e13ed` · `26807ec` · `3f042d8` · `3f26972` · `45f02f2` · `22c51ee` · documentação.

### 17/10 11:53–12:27 · Respostas de 17/10 de manhã (D63–D70)
- **Feito:** antes de implementar, quatro pontos voltaram ao Lucca por contradizer dados ou respostas: Bridge (Q-T 1: avisada dias depois de 15/09; nos dados, Orbe a 2,59% à vista até 18/09 e 2,19% desde 23/09, o que sustenta a leitura) → `condicao_nao_informada`; critério da Mundo Aberto → ASSUMO com aceite (a Helena delegou); alerta de antecipação → só lojista sem histórico (o critério do mês inteiro dava 5 alarmes falsos); Atlas em outubro → flag `--orbe-anterior` (setembro não tem modalidade nem data no pendencias/rastro). Depois, um commit por item: natureza das divergências (D63), critério da Mundo Aberto (D64), conta da L65 (D65), alerta de antecipação (D66), Atlas em outubro (D67), rascunhos de contestação (D68), premissas Q-P 2/Q-N 3/Q-N 4/Q-N 7/Q-Y/Q-S (D69), IA funcionando no outubro sintético com uma chamada real (D70). Q-N a Q-Y incorporadas em `docs/FINANCEIRO_SLACK.md` (35 trechos citados conferidos, iguais) e o arquivo de origem apagado; CAUSA_RAIZ com Q-T 1, Q-U e Q-W (citações conferidas contra o FINANCEIRO_SLACK); HIPOTESES (H51–H55, H15 e H39 CONFIRMADO, P18–P29, Resumo); STATUS.
- **Verificado:** setembro antes × depois: comissões, notas, lançamentos (valores e contas) e contestação iguais; divergências iguais nos números, com a coluna `natureza`; pendências 14 → 15 (+ alerta da Atlas, 124.235,32); `lancamentos_classificados.csv` ganha `motivo_conta`; `saida/rascunhos/` novo (4 rascunhos). Duas execuções seguidas: saída idêntica. `pytest`: 244 passed. `scripts/auditar_saida.py`: 0 violações. IA real: 1 chamada, 2.612 + 143 tokens, ~US$ 0,0003; sem rede, o cache dá a mesma saída byte a byte.
- **Commits:** `491824c` · `e099511` · `5633995` · `64ac5ce` · `49ab4b7` · `c9a7370` · `8c55d68` · `752ba4a` · `53b7a20` · documentação.

### 17/10 12:27–12:43 · Valor a devolver, provisão, pico da antecipação, devolver × recuperar (D71–D74)
- **Feito:** antes do item A, voltou ao Lucca: trocar o valor da divergência contrariava a Q-H c (CONFIRMADO); decidido separar (diferenca_brl pela Q-H c; `valor_a_devolver_brl` = cobrado pela Orbe − comissão contratada, D71). Provisão de folha e impostos do mês como pendência sem valor (D72, Q-R 3; não existia). Alerta de antecipação pela exposição máxima (D73). Toda divergência de checkout = devolver; Rota também recuperar da Orbe (D74), com o custo na CAUSA_RAIZ. `PROMPTS/03-claude-app-relatorio.md` commitado. O `.txt` da raiz é o export da sessão da avaliação simulada (11:34): não mexido.
- **Verificado:** Casa 15.396,77 em 116 linhas (as 118 do cálculo linha a linha menos o par TX88441917/TX88446763 que se anula), Rota 1.545,86, Bridge 29,94; devolver 16.972,57, recuperar 1.545,86, custo 15.426,71; pico da Atlas 124.235,32 em 15/09. `pytest`: 249 passed; auditoria 0 violações; duas execuções idênticas.
- **Commits:** `f12f909` · `369511a` · `4fb80bd` · `c039063` · `ebae2b0` · documentação.

### 17/10 12:43–13:07 · Documentação para a entrega e incidente com o export da avaliação
- **Incidente (~12:53):** ao mover o export da avaliação simulada (`2026-10-17-113437-….txt`, 587 linhas, fora do git) para `PROMPTS/04-avaliacao-simulada.txt`, o `sed` de troca do nome de usuário falhou (aspas no Git Bash) e o `rm` do original, encadeado com `;`, rodou mesmo assim: a cópia ficou vazia e o original foi apagado antes de ser conferido. Avisado na hora; a sessão original está em `.jsonl` (`~/.claude/projects/…/2b33409b-….jsonl`). O Lucca retomou a sessão e exportou de novo, mas a sessão retomada estava resumida e o export novo (`2026-10-17-125919-….txt`) tem 387 linhas e começa na resposta final: não passou na conferência (linhas ≠ 587), então não foi movido nem apagado. Regra daqui em diante: troca por script Python, conferir a cópia (tamanho, linhas, nada pessoal) e só apagar com `&&` em cada passo.
- **Feito:** README (problema em 2 frases, setembro em números, fato/resposta/premissa, limitações, com mais tempo; nenhum `[preencher]`); HIPOTESES com números conferidos contra a saída (H02, H03, H04, H08, H09, H11, H13, H19, H20, H44, H51) e escopo preenchido; `docs/CHECKPOINTS.md` (checkpoint 1 literal, 10:44, resposta do Manuel, o que virou cada premissa); DIARIO e DECISOES (D52–D74) com os horários do `git log`, que antes estavam estimados à mão e errados; MOMENTOS com o momento 5 (valor a devolver) e o incidente; STATUS e CAUSA_RAIZ com 16 pendências e devolver/recuperar/custo.
- **Verificado:** nenhum código nem saída mudou (`git diff --stat saida src` vazio); citações do CHECKPOINTS conferidas contra o FINANCEIRO_SLACK; contagens do Resumo do HIPOTESES = lista (28 CONFIRMADO, 25 ASSUMO, 1 SEI, 1 substituída).
- **Commits:** `715a5f9` · `f6da831` · `30e38dd` · `0a228a0` · documentação.

### 17/10 13:16–13:53 · Arquivo 06 e respostas Q-Z a Q-AH (D75–D84)
- **Feito:** PROMPTS/04 gerado do `.jsonl` completo da sessão da avaliação (conferido: 175 KB, 1.701 linhas, zero nome de usuário, e-mails ou chaves; só então o export parcial da raiz foi apagado). Respostas Q-Z a Q-AH lidas no Slack e copiadas literais no FINANCEIRO_SLACK. Um commit por item: 06 no fechamento (D75), Bridge como contrato (D76, corrige a D63), divergências transação por transação (D77), provisão fora do fechamento (D78), valor a devolver CONFIRMADO (D79), spread negativo com os dois valores (D80), alerta ASSUMO com aceite (D81), Atlas identificada e fora do arquivo (D82), regra do ajuste da Ponte registrada sem o abatimento (D83, passaria dos 20 min), aviso de layout no Aurora (D84). Docs: README, HIPOTESES (H15, H26, H41, H51, H53 atualizadas; H56–H57; P30–P38; Resumo), CAUSA_RAIZ, STATUS, CHECKPOINTS.
- **Verificado:** notas 243.284,29 (−3.304,39, igual à conta independente do Lucca); devolver 16.972,57, recuperar 1.575,80, custo 15.396,77; 210 linhas de divergência de checkout; 15 pendências; `pytest`: 259 passed; auditoria 0 violações; saída regenerada do zero e duas execuções idênticas. Os horários das D75–D84 tinham sido escritos estimados e foram corrigidos para os do `git log`.
- **Commits:** `324ced0` · `0a59b75` · `6c5bfb7` · `f4f56ce` · `af81e5c` · `116446a` · `b0d87a2` · `957246e` · `ab91056` · `7c74f23` · `12f5ba2` · `268b603` · documentação.

### 17/10 14:15–14:50 · Auditoria independente das regras e teste das regras (D85–D90)
- **Feito:** a auditoria independente das regras (fase 1 sem `regras.yaml` nem código; comparação depois) copiada sem edição para `docs/auditoria_regras/`, com README e citação no CHECKPOINTS (ponto 2 do Manuel). Das médias: Casa com tipo próprio (D85), rótulo do estorno de venda cobrada acima do contrato (D86), PIX de 18.240 como acompanhamento com a Q-N 5 (D87), rascunho da Orbe com a fórmula da Q-H c ao lado (D88), aviso quando o 06 falta (D89). Casos-ouro: 13 testes com os valores da Helena (`pytest -m caso_ouro`), 2 novos e 11 marcados. Teste das citações: 34 das 49 CONFIRMADO não tinham fala literal; todas ganharam a citação sem mudar status, IRRF/PIS/COFINS seguem CONFIRMADO porque o extrato diz "DEBITO DARF", e `aurora.orbe_recebivel` voltou a ASSUMO (D90, decisão Lucca). `docs/TESTE_DAS_REGRAS.md` com o limite: a fala existe ≠ a fala sustenta.
- **Verificado:** nenhum caso-ouro falhou; números iguais aos da D75–D84 (notas 243.284,29; devolver 16.972,57; recuperar 1.575,80; custo 15.396,77); só o status de 21 lançamentos mudou; `pytest`: 268 passed; auditoria 0 violações; duas rodadas idênticas. Horas das D85–D90 pela hora do commit (a D85 tinha sido escrita 14:08 e a D87 14:30; o commit é das 14:24 e 14:29).
- **Commits:** `f1aab3e` · `32eaeb8` · `b65544e` · `64af341` · `1f58407` · `5d5a61d` · `0be25e1` · `c276eed` · `77cfcc0` · documentação.

### 17/10 12:21–14:52 · Painel do fechamento (branch `relatorio`), na main às 14:55
- **Feito:** `saida/painel.html`, um arquivo único (HTML, CSS e JS inline) que abre com duplo clique. Telas: visão geral, decisões (devolver × recuperar, custo para a Tarvo), contratado × cobrado, remessa (Ponte) e rastro. Ele lê só a saída, o `regras.yaml`, o `HIPOTESES.md` e o sha256 do `data/`. Integrado ao `python -m tarvo` (gera depois do validador; com saída inválida, o painel antigo é apagado). Documentação em `docs/PAINEL.md`.
- **Verificado:** os mesmos bytes no Linux e no Windows (CI); `tests/test_painel.py`. Na main por `git merge --ff-only relatorio` (`067f017`), com a saída regenerada do zero: `git diff saida/` vazio e os quatro totais batendo; `pytest`: 291 passed; auditoria 0 violações; CI #15 verde.
- **Commits:** `0464b79` · `a66f4e5` · `bfd7029` · `7a544eb` · `067f017` (mais os merges da main na `relatorio`).

### 17/10 15:05–15:25 · Respostas Q-AI a Q-AM (D91–D96)
- **Feito:** as respostas da Helena (13:34 para o Lucca e para o David, 14:08 para a Turma do Barulho, 14:10 para os Desbravadores) e da Organização (14:11) copiadas literais no FINANCEIRO_SLACK. Implementado: mês do ajuste tardio, com a opção `--fechamento-anterior-aprovado` (D91); data-base da antecipação CONFIRMADO (D92); bandeira trocada sem pendência (D93); ajuste sem a original (D94); manifesto e log de execução (D95); regra aplicada por linha em `rastro_regras.csv` (D96). Casos-ouro novos: AN88445172 e TX88447011.
- **Verificado:** setembro com os mesmos números (só entram no git `manifesto.csv`, `rastro_regras.csv` e o painel com as contagens novas); `pytest`: 303 passed; auditoria 0 violações. A D94 testada no outubro sintético, a D91 numa cópia de setembro com um ajuste de agosto.
- **Commits:** `d07480c` · `f788bcf` · `81d9038` · `d5d8426` · `339bfff` · `6fb88f8` · `f791b60` · documentação.

### 17/10 15:49–16:25 · Auditoria final da banca (clone limpo, formato, rastro, recontagem, alarmes, docs)
- **Feito:** auditoria em 5 frentes paralelas (forks do Claude Code), sem mexer em cálculo, regras.yaml nem data/. Achados de texto corrigidos (README, STATUS, HIPOTESES, MOMENTOS, CAUSA_RAIZ, DECISOES, AUDITORIA); Theo e David só pelo primeiro nome; Checkpoint 2 (15:38) registrado; MOMENTOS com 4 momentos. Decisão do Lucca: o motivo das 118 linhas da Casa em `divergencias_taxa.csv` deixa de dizer "Orbe aplicou … contratada 0%" e passa a dizer isenção comercial da Tarvo (Q-AA 1, Q-AE 1).
- **Achado da IA que eu causei:** a troca do Theo no HIPOTESES deixou o `painel.html` com o hash antigo (o painel grava o sha256 do HIPOTESES e do regras.yaml) e o `test_painel` falhou; o painel foi gerado de novo (`80d2003`). Toda edição nesses dois arquivos pede o painel de novo.
- **Verificado:** clone limpo do GitHub com saída idêntica byte a byte; formato dos 6 arquivos e as refs contra data/ (`L<n>` = linha física, FITID); 492 `id_saida` com rastro que fecha; recontagem sem importar `src/` bate no centavo (comissão de checkout dos 21 lojistas 203.735,34, notas 243.284,29, devolver 16.972,57, recuperar 1.575,80, custo 15.396,77). Na troca do motivo, o diff da saída ficou só na coluna `motivo` (118 linhas `condicao_nao_informada`) e no hash do painel; `pytest`: 303 passed.
- **Commits:** `d25b79c` · `36c8031` · `3d02320` · `af3bbb7` · `2dfc636` · `46965e9` · `cea0cf6` · `3934a18` · `80d2003` · `41b27ea` · `6ee812c` · `1122b88` · `b5d2832` · `230ed04`.
