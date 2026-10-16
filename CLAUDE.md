# Tarvo · fechamento de setembro/2026 (Desafio Barte AI)

Leia `docs/case.md` (instruções oficiais), `HIPOTESES.md`, `docs/PLANO.md` e `docs/EXPLORACAO.md` (formato real de cada arquivo, armadilhas, mapa, ambiguidades) antes de qualquer tarefa. O data pack está em `data/` e **não pode ser alterado nem limpo à mão**: a solução lê os arquivos como chegam.

## Regras deste projeto

1. **Regra de negócio não se inventa.** Se a regra não está nos dados nem em `HIPOTESES.md` como CONFIRMADO ou ASSUMO, pare e me diga — eu decido se pergunto ao financeiro ou assumo e registro.
2. **Todo número de saída tem rastro** até as linhas de origem (`rastro.csv`); a soma das linhas por `id_saida` tem que bater com o número reportado. Total que não fecha = número inventado.
3. **Dinheiro em Decimal, quantizado em centavos na saída; nunca float.** Percentuais sem arredondar no meio do caminho.
4. **Alarme falso conta contra.** Na dúvida, não afirme: vira linha em `pendencias.csv` com motivo e quem decide.
5. **IA só onde há ambiguidade real** (ex.: classificar lançamento sem regra clara), sempre com `metodo` e `confianca`. Regra determinística primeiro.
6. Formato de saída é fixo (ver `docs/case.md`): CSV com `;`, ponto decimal, datas AAAA-MM-DD, CNPJ só números (14 dígitos).
7. A solução tem que rodar de novo em outubro com arquivos novos no mesmo formato: nada de valor fixo de setembro no código.

## Como trabalhar comigo (Lucca)

- Antes de construir, diga o plano em poucas linhas. Explique decisões técnicas em 2–3 linhas para eu defender.
- Quando eu pedir análise, não escreva código de solução.
- Commits pequenos, em português. Nunca peça nem escreva a chave da API: ela está só no `.env.local`.

## Estrutura

```
data/                 data pack original (somente leitura)
docs/                 case.md, PLANO.md, EXPLORACAO.md, STATUS.md, DIARIO.md, DECISOES.md
regras.yaml           regras de negócio como dado: valor, status (SEI|ASSUMO|CONFIRMADO|PENDENTE), fonte, pergunta_ref
src/tarvo/
  __main__.py         CLI
  modelo.py           dataclasses (Decimal, ref_origem em todo registro)
  leitores/           um por arquivo; armadilhas de leitura na docstring
  cadastro.py         CNPJ 14 dígitos, EC→CNPJ por chave, taxas com vigência
  regras.py           carrega/valida regras.yaml
  calculos/           comissoes, divergencias, notas (determinístico)
  classificacao/      por_regra → por_ia (sobras) → HUMANO
  pendencias.py       o que exige uma pessoa
  saida/              escritor (formato fixo) e validador (rastro fecha)
tests/                pytest
saida/                CSVs gerados
```

Perguntas ao financeiro: canal `#duvidas-hackathon-ai` (registro em `HIPOTESES.md`). Regra PENDENTE (`valor: null`) em `regras.yaml` **não** se resolve no código: o cálculo dependente vira pendência e eu sou avisado.

## Comandos (PowerShell, na raiz)

```powershell
.\.venv\Scripts\Activate.ps1                    # ativar o ambiente
python -m tarvo --dados data --saida saida      # rodar o fechamento
python -m tarvo --help
pytest                                          # testes
```

Sem ativar: `.\.venv\Scripts\python.exe -m tarvo ...` e `.\.venv\Scripts\python.exe -m pytest`.
Recriar o ambiente: `& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv` → `pip install -r requirements.txt` → `pip install -e .` (o `python` do PATH é o atalho da Microsoft Store e não serve).

## PROTOCOLO de fim de etapa

Ao terminar cada etapa (E1, E2…), nesta ordem:

1. **Testes:** `pytest` passando (todo bug corrigido ganha um teste antes da correção).
2. **`docs/STATUS.md`:** checklist, contagem de regras por status, números atuais, próximo passo.
3. **`docs/DIARIO.md`:** hora, etapa, o que foi feito, como foi verificado, commit.
4. **`docs/DECISOES.md`:** só se houve decisão técnica (alternativa + motivo).
5. **Commit** pequeno, em português, com o nome da etapa.
