"""Toda regra CONFIRMADO no regras.yaml tem uma citação que aparece literalmente em docs/FINANCEIRO_SLACK.md.

Citação = trecho entre aspas em `fonte` ou `aceite`, com 12 caracteres ou mais. Reticências ("..." ou "…") separam
trechos, e cada trecho tem que estar na fala. Comparação sem diferença de espaços, asteriscos (negrito do Slack) e
estilo de aspas/apóstrofo. Uma regra pode ter outras citações (do e-mail da Ponte, dos dados); basta uma do canal.
"""
import re
from pathlib import Path

from tarvo.regras import carregar_regras
from conftest import RAIZ

MINIMO = 12


def _norm(texto: str) -> str:
    texto = texto.replace("\n> ", "\n")  # a fala quebrada em linhas de citação do markdown
    texto = texto.replace("*", "").replace("’", "'").replace("“", '"').replace("”", '"')
    return " ".join(texto.split())


def _citacoes(regra: dict) -> list[str]:
    textos = " ".join(str(regra.get(c) or "") for c in ("fonte", "aceite"))
    return [c for c in re.findall(r"'([^']+)'|\"([^\"]+)\"", textos) for c in c if len(c.strip()) >= MINIMO]


def _literal(citacao: str, slack: str) -> bool:
    trechos = [t.strip(" .,;:") for t in re.split(r"\.\.\.|…", citacao)]
    trechos = [t for t in trechos if len(t) >= MINIMO]
    return bool(trechos) and all(_norm(t) in slack for t in trechos)


def sem_citacao_literal() -> list[tuple[str, str]]:
    slack = _norm((RAIZ / "docs" / "FINANCEIRO_SLACK.md").read_text(encoding="utf-8"))
    falhas = []
    for chave, regra in carregar_regras(RAIZ / "regras.yaml").items():
        if regra["status"] != "CONFIRMADO":
            continue
        cits = _citacoes(regra)
        if not cits:
            falhas.append((chave, "sem citação entre aspas"))
        elif not any(_literal(c, slack) for c in cits):
            falhas.append((chave, "citação não literal: " + cits[0][:80]))
    return falhas


def test_toda_regra_confirmada_tem_citacao_literal_do_canal():
    falhas = sem_citacao_literal()
    assert falhas == [], "\n".join(f"{k}: {m}" for k, m in falhas)


def test_citacao_inventada_ou_editada_nao_passa():
    slack = _norm((RAIZ / "docs" / "FINANCEIRO_SLACK.md").read_text(encoding="utf-8"))
    assert _literal("A gente não trunca. (a) Arredondamento comum para o centavo", slack)
    assert not _literal("A gente não trunca. Arredondamento comum para o centavo", slack)  # sem o "(a)": editada
    assert not _literal("A Orbe pode cobrar acima do contrato", slack)  # inventada
