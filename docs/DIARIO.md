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

### ~21h40 · Decisões do mínimo e momentos de IA
- **Feito:** Lucca manteve Casa −5,50 e aprovou `COM-<cnpj>-CHECKOUT` e as colunas extras. Saída em ordem determinística (comissão decrescente, depois CNPJ; rastro por `id_saida` e linha). Registrada a conferência independente do Lucca (outra sessão, sem ver o código: 21 lojistas no centavo, 207.031,31, 57 pendentes, 1.943 linhas). `PROMPTS/MOMENTOS.md` com 3 entradas. A separação fatos/contas das obrigações de 08/2026 já estava feita (commit `56da90a`).
- **Verificado:** `pytest`: 51 passed (novo teste de ordem); duas execuções seguidas geram `rastro.csv` com o mesmo hash.
- **Commit:** `decisões do mínimo e momentos de IA`.

### ~21h45–21h55 · E5a: divergências de checkout
- **Feito:** `calculos/divergencias.py`: diferença = `valor_taxa` Orbe − comissão contratada (a mesma da E2, com a mesma taxa e fonte). Venda líquida com os estornos dela (D10) e reversão líquida com a antecipação (D17, a confirmar); só lista se ≠ 0 (tolerância 0, D09). Casa entra, Atlas fica fora. `divergencias_taxa.csv` com as colunas do case e extras (lojista, data, valor_bruto, comissao_contratada, valor_taxa_orbe, direcao, liquida_com, motivo com a fonte da taxa, decisao=Helena). Validador: conservação (Σ `valor_taxa` = Σ comissão + Σ divergências), divergência só aponta linha que está numa comissão, e cobertura contando só COM-/PEN-.
- **Verificado:** 200 divergências, R$ 16.973,00; conservação 224.004,31 = 207.031,31 + 16.973,00, igual à previsão independente. Rota 1.546,28 e Bridge 29,95 iguais à exploração. Hand-check: TX88423647 (66,28), TX88428053 (4,49), AN88445802 (1.206,58). `pytest`: 65 passed.
- **Bugs achados e corrigidos (teste antes da correção):** (1) zero negativo (`-0.00`) no rastro da Casa (−1.021,01 × 0): o formatador agora escreve `0.00`; (2) a CLI caía com código 1 num console cp1252 por causa do "Σ" (só tinha passado porque eu forcei UTF-8 no terminal): D18.
- **Commit:** `E5a: divergências de checkout com conservação validada`.

### ~22h00–22h15 · E4: comissão e divergências de REMESSA
- **Feito:** leitor do .eml (stdlib `email`) e do anexo (aba pelo cabeçalho "Nº Operação", colunas pelo nome, competência lida do relatório, totais declarados conferidos). `calculos/remessa.py`: destino de cada linha (competência pela contratação → duplicata → spread negativo → cadastro → elegível) e comissão 50% × Spread R$ com ROUND_HALF_EVEN por operação (D19). Divergência de remessa no valor cheio, com o aplicado recalculado de TC e PTAX (D22), padrão 1,5% e tolerância 0,005 p.p. Exclusões anotadas no rastro como EXC- (D23). Validador com cobertura por (ref, linha) e conservação da remessa. Correção de bug latente: condição especial da Casa não vale para o spread de remessa (D24).
- **Verificado:** 233 linhas = 228 elegíveis + 1 duplicata + 4 negativos; Σ Spread 78.073,59 = declarado. Comissão 39.542,89. Hand-check PC-0926-0011: (4,0920 − 4,0315) × 2.438,46 − 1,2% × 4,0315 × 2.438,46 = 147,5268 − 117,9666 = 29,56. PC-0926-0002: 50% × 262,01 = 131,005 → 131,00 (meio → par). `pytest`: 83 passed.
- **A confirmar com o Lucca:** D21 (divergência do spread negativo pela fórmula: −3.565,99; pelo spread: −1.834,05), D20 (arredondamento da divergência).
- **Commit:** `E4: comissão e divergências de remessa`.

### ~22h20–22h35 · Decisões D17/D20/D21/D22 e E6a: notas a emitir
- **Feito:** D22: divergência de remessa = Spread R$ − contratado × PTAX × ME (mesma base da comissão). D21: `impacto_repasse_tarvo` = 50% × Spread R$ nos negativos, motivo novo. D17 e D20 confirmadas (D17 virou a regra `divergencias.reversao_liquida_com_antecipacao`, lida pelo código). `calculos/notas.py`: 1 nota por lojista com comissão CHECKOUT > 0, 1 nota REMESSA para a Ponte; discriminação em `notas.discriminacao` com a competência dos dados; nota negativa → pendência NF_NEGATIVA; pendência CONFERENCIA_REPASSE calculada (participação × total declarado × nota, decomposta pelas exclusões; data do TED lida do e-mail). Validador: notas = comissões e nenhuma nota ≤ 0; pendências derivadas fora da cobertura.
- **Verificado:** Mundo Aberto 1.418,88; negativos −3.565,98 (Canguru −1.001,29); impacto −917,03; 21 notas (207.036,81 + 39.542,89); conferência 39.036,80 × 39.542,89 = 506,09 = 917,03 − 410,94, todos iguais aos números previstos pelo Lucca. `pytest`: 91 passed.
- **Bugs achados e corrigidos:** (1) o validador dava exceção (InvalidOperation) com vírgula decimal em vez de reportar erro: D26; (2) uma substituição em lote quebrou duas f-strings da CLI (`
` virou quebra de linha real); a CLI não rodava e foi corrigida antes do commit.
- **Commit:** `D21/D22 e E6a: notas a emitir com conferência do repasse`.

### ~22h40–22h55 · Respostas Q-H/Q-I/Q-J: arredondamento comum
- **Feito:** Q-H, Q-I e Q-J em `docs/FINANCEIRO_SLACK.md` (literal). `regras.yaml`: arredondamento comum (ROUND_HALF_UP) por linha CONFIRMADO para a comissão de checkout, as divergências e os 50% da remessa, **corrigindo o ASSUMO de truncar (D09)** e o HALF_EVEN (D19/D20) → D27; tolerância 0 do checkout removida, divergência de checkout = round(bruto × (aplicada − contratada)) só onde as taxas diferem; divergência de remessa volta à coluna "Spread %" (D28); Q-I CONFIRMADO (obrigações de agosto e despesas diretas); Q-J pendência EXCESSO_REMESSA (D30). Arredondamento num só lugar (`formatos.modo_arredondamento`, lido do `regras.yaml`). Validador: divergência recalculada da fonte, resíduo de truncamento por linha (D29). Conferência do repasse com o terceiro componente (arredondamento).
- **Verificado:** todos os números bateram no centavo com a previsão independente do Lucca antes do commit: checkout 207.039,73 (Bridge 11.916,02; Casa −5,50); divergências checkout 200 · 16.973,65 (Casa 15.397,42; Rota 1.546,28; Bridge 29,95); resíduo −9,07; remessa 39.543,45; Mundo Aberto 1.418,85; negativos −3.565,98; notas CHECKOUT 20 · 207.045,23; nota REMESSA 39.543,45; conferência 506,65 = 917,03 − 410,94 + 0,56. `pytest`: 94 passed.
- **Ponto levado ao Lucca:** o pedido dizia "|resíduo por linha| < 0,01"; truncar × arredondar dá exatamente 0,01 em 969 linhas, então o critério implementado é ≤ 0,01 (D29). Um teste novo errou o exemplo (escolhi uma linha da Casa, que tem taxa 0) e foi corrigido para a L6 TX88410316.
- **Commit:** `Q-H/Q-I/Q-J: arredondamento comum, resíduo de truncamento e excesso da remessa`.

### ~23h00–23h15 · E6b parte 1: extratos classificados só por regra
- **Feito:** leitores do Aurora (UTF-8 com fallback Latin-1, linhas de dado pelo conteúdo, saldos e saldo corrido), do Meridiano (OFX pelo CHARSET do cabeçalho, FITID e linha física) e do plano de contas (lançáveis = ANALITICA + ACEITA_LANCTO=S). `classificacao_extratos` no `regras.yaml`: 26 regras por padrão de descrição, com sinal, sem número de linha (D32); as regras antigas por linha saíram. Lojista no extrato por prefixo exato (D31). Conferências: transferências entre contas, aportes × Ponte, aplicação × resgate em FIFO. Validador: cada lançamento uma vez, Σ Aurora = final − inicial, contas lançáveis, HUMANO sem conta.
- **Verificado:** 184 lançamentos (84 + 100), 174 por regra, 10 HUMANO; Σ Aurora −2.532.423,41 = saldo final − saldo anterior; 3 transferências casadas no mesmo dia e L92 sem par; Ponte Aérea 18.240,00 sem operação; resgate de 09/09 com excesso de 392,00. `pytest`: 143 passed (cada regra com um caso de setembro).
- **Alarme falso evitado:** a 1ª execução acusou divergência de aportes de −394.222,69 da EduAbroad, mas os aportes dela só não tinham sido identificados (nome do banco "EDU ABROAD"); somados à mão, batem com as operações. Lojista sem aporte identificado, havendo PIX RECEB sem regra, agora fica "não conferido" (D33).
- **Commit:** `E6b parte 1: extratos classificados por regra, com conferências`.

### ~23h30–23h40 · Decisões da E6b parte 1
- **Feito:** H36: EduAbroad sem alias; plano da parte 2 registrado (D37). H37: regra RENDIMENTO APLIC → 3.2.01. H38: resgate de 392,00 acima do aplicado fica em 1.1.02.001, sem pendência (saldo aplicado anterior a 01/09, D36). Atlas: lojistas do extrato = planilha vigente ∪ nomes da Orbe dos ECs sem vínculo (D35); L34 e L60 → 2.1.01.001 por regra; pendência de faturamento mantida.
- **Verificado:** 7 linhas sem regra (só EduAbroad), como esperado. `pytest`: 148 passed. Validador OK.
- **Diferenças levadas ao Lucca:** (1) a união com **todos** os nomes da Orbe resolveria também a EduAbroad ("EDU ABROAD CONSULTORIA" é o nome da Orbe do EC dela), contra a D37 e o esperado; restringi aos ECs sem vínculo. (2) Pendências: **15**, não 16 (eram 19; saíram 3 SEM_REGRA — L34, L60, MRD2026090680 — e a do resgate).
- **Commit:** `decisões da E6b parte 1: rendimento, resgate, Atlas e plano da EduAbroad`.

### 17/10 ~00h15–00h30 · Respostas Q-K, Q-L, Q-M
- **Feito:** Q-K, Q-L e Q-M no FINANCEIRO_SLACK, no HIPOTESES (P15–P17, H40–H42, H26, "Fica de fora") e no `regras.yaml`. Q-K: CONFERENCIA_REPASSE reescrita sem prever desconto (valor = faturado, rastro = linhas da nota REMESSA); coluna `participacao_tarvo_no_spread` (D38). Q-L: módulo `calculos/contestacao.py`, 3 pendências CONTESTACAO_PONTE e extra `saida/contestacao_ponte.csv` (D39); validador confere Σ por pendência. Q-M: `orbe_recebivel` CONFIRMADO; saldo negativo e conciliação por parcela fora.
- **Verificado:** Mundo Aberto 23 ops = 1.418,85 (mesmo número da divergência); negativos 4 ops = −1.834,05 (Σ Spread R$; −3.565,98 contra o contrato); duplicata R77 = 821,88; a R76 continua em COM- e a R77 em EXC- (conta uma vez). Pendências 15 → 18. `pytest`: 151 passed (testes novos: TED sem desconto, coluna renomeada, contestação por motivo, validador recusa contestação que não fecha). Validador OK.
- **Commit:** `Q-K/Q-L/Q-M: conferência do TED sem desconto, contestação com a Ponte e créditos da Orbe`.

### 17/10 ~00h35–00h45 · Teste de reprodutibilidade
- **Feito:** clone em `%TEMP%\tarvo-repro`, seguindo o README como avaliador num Windows sem Python no PATH. Achados: (1) a seção "Como rodar do zero" do README estava vazia (`[preencher]`); (2) `python` do PATH = atalho da Store (código 9009); (3) sem `pip install -e .` → "No module named tarvo"; (4) fora da raiz sem `--regras` → código 2 (`regras.yaml` relativo à pasta atual); (5) `Activate.ps1` costuma estar bloqueado num Windows limpo; (6) o README não dizia se roda sem chave (roda: a IA ainda não está ligada). README corrigido com pré-requisito, passos, comando único, saída esperada e esses avisos (D40). Código não mudou.
- **Verificado:** duas execuções no clone + `saida/` commitada no clone + `saida/` do projeto: SHA-256 idêntico nos 7 CSVs. Com `--dados "%TEMP%\teste ação\dados"` e `--saida "%TEMP%\teste ação\saída com espaço"` rodando de fora do repo (com `--regras`): código 0, validador OK, 7 CSVs idênticos. Segundo clone seguindo o README novo ao pé da letra: código 0, `pytest` 151 passed, `git status` sem mudança em `saida/`.
- **Commit:** `teste de reprodutibilidade`.

### 17/10 ~00h50–00h55 · regras.yaml padrão relativo ao repositório
- **Feito:** padrão de `--regras` resolvido a partir do pacote (raiz do repo), não da pasta atual; `--regras` explícito continua com prioridade (D41). Aviso de "rodar na raiz" removido do README.
- **Verificado:** teste novo primeiro (falhou: código 2), depois a correção: rodar de fora do repo sem `--regras`, com `--saida` com espaço e acento, dá código 0 e validador OK; `--regras` explícito inexistente dá código 2 (prioridade). `pytest`: 153 passed.
- **Commit:** `regras.yaml padrão relativo ao repositório`.

### 17/10 ~08h00–08h40 · E6b parte 2: IA nas sobras
- **Feito:** conferi o SDK instalado (`anthropic` 1.15.0, pydantic 2.14.1) e a forma documentada de saída estruturada (`messages.parse(output_format=<BaseModel>)` → `.parsed_output`; junta `output_config` com o formato). `classificacao/por_ia.py`: prompt versionado (`src/tarvo/prompts/classificar_lancamento.md`, D43), chave do `.env.local` (nunca impressa), cache `cache_ia/`, verificação (a)–(d), aplicação nas linhas e pendências, aportes aceitos na conferência, `sugestoes_regra.csv`; `--sem-ia`; regras `classificacao.modelo_ia` e `classificacao.verificacao_ia` (D42).
- **Testes sem rede (`tests/test_ia.py`):** cliente mockado (i) válido → IA + cache + reexecução sem chamadas; (ii) conta inexistente → HUMANO (a); (iii) confiança 0,5 → HUMANO (d); (iv) aportes atribuídos à Mundo Aberto → Σ não bate → HUMANO (c); conta de aporte sem lojista → HUMANO (b); sem chave e sem cache → HUMANO + aviso; `--sem-ia` → exit 0; chave lida do arquivo e nunca impressa. `conftest` liga `TARVO_SEM_REDE`.
- **Execução real (uma vez):** 7 chamadas, 18.118 + 2.379 tokens, ~US$ 0,003. 5 aportes EduAbroad aceitos (Σ 394.222,69 = Ponte); L28 e L69 recusados: a IA não ligou "EDU ABROAD CONSULTORIA LTD" à EduAbroad (confiança 0,5 e 0,4). Não mexi no prompt para forçar outra resposta.
- **Verificado:** segunda execução 0 chamadas (cache), SHA-256 dos 8 CSVs iguais; a chave não aparece em `cache_ia/` nem em `saida/`; validador OK (agora também exige confiança em linha IA); pendências 18 → 13; `pytest`: 161 passed.
- **Commit:** `E6b parte 2: IA nas sobras, verificada pelo código, com cache`.

### 17/10 ~08h40–08h50 · Decisões da E6b parte 2
- **Feito:** L28 e L69 por decisão humana do Lucca (`decisoes_humanas` no `regras.yaml`, uma por linha, aplicadas só à linha exata e antes da IA): 2.1.01.001 EduAbroad, metodo HUMANO, confiança vazia; pendências IA_REPROVADA saíram. SUG-001 aprovada: `classificacao_extratos.aliases_lojista` "EDU ABROAD CONSULTORIA" → 16181276000153, Aurora e Meridiano, vigência 2026-10-01; `sugestoes_regra.csv` marca APROVADA. Validador: HUMANO com conta só com decisão explícita; HUMANO sem confiança (D44).
- **Verificado:** alias casa por REGRA com data de outubro (Aurora e Meridiano) e não casa em setembro; decisão com valor diferente não se aplica (vira aviso); validador recusa HUMANO com conta sem decisão. Setembro: 5 IA + 2 decisão humana; pendências 13 → 11; IA com 5 sobras, 0 chamadas. Reexecução: SHA-256 dos 8 CSVs iguais. `pytest`: 168 passed.
- **Commit:** `decisões da E6b parte 2: L28/L69 por decisão humana e alias da EduAbroad para outubro`.
