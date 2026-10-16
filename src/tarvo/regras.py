"""Carrega e valida `regras.yaml`.

Responsabilidade: regra de negócio é dado, não código. Este módulo só lê o YAML,
confere que cada regra tem `valor`, `status` (SEI | ASSUMO | CONFIRMADO | PENDENTE),
`fonte` e `pergunta_ref`, e expõe os valores. Regra PENDENTE (sem valor) bloqueia o
cálculo que depende dela (vira pendência), em vez de o código inventar um padrão.
"""

from __future__ import annotations

from pathlib import Path

import yaml

STATUS_VALIDOS = ("SEI", "ASSUMO", "CONFIRMADO", "PENDENTE")
CAMPOS = ("valor", "status", "fonte", "pergunta_ref")


class RegraInvalida(ValueError):
    """`regras.yaml` com estrutura inválida."""


class RegraPendente(LookupError):
    """Pediu o valor de uma regra que ainda não foi decidida."""


def _iterar_regras(arvore: dict, prefixo: str = ""):
    """Percorre o YAML devolvendo (chave pontuada, regra); regra = dict que tem `status`."""
    for nome, no in arvore.items():
        chave = f"{prefixo}{nome}"
        if isinstance(no, dict) and "status" in no:
            yield chave, no
        elif isinstance(no, dict):
            yield from _iterar_regras(no, chave + ".")
        else:
            raise RegraInvalida(f"{chave}: esperado um grupo ou uma regra, veio {type(no).__name__}")


def validar_regras(arvore: dict) -> dict[str, dict]:
    """Valida a estrutura e devolve as regras indexadas pela chave pontuada (ex.: 'orbe.arredondamento_valor_taxa')."""
    regras: dict[str, dict] = {}
    erros: list[str] = []
    for chave, regra in _iterar_regras(arvore):
        faltando = [c for c in CAMPOS if c not in regra]
        if faltando:
            erros.append(f"{chave}: faltam campos {faltando}")
            continue
        status = regra["status"]
        if status not in STATUS_VALIDOS:
            erros.append(f"{chave}: status {status!r} fora de {STATUS_VALIDOS}")
        elif status == "PENDENTE" and regra["valor"] is not None:
            erros.append(f"{chave}: PENDENTE não pode ter valor")
        elif status != "PENDENTE" and regra["valor"] is None:
            erros.append(f"{chave}: {status} sem valor (use PENDENTE)")
        elif status != "PENDENTE" and not regra["fonte"]:
            erros.append(f"{chave}: {status} sem fonte")
        regras[chave] = regra
    if erros:
        raise RegraInvalida("regras.yaml inválido:\n  " + "\n  ".join(erros))
    return regras


def carregar_regras(caminho: Path) -> dict[str, dict]:
    """Lê o YAML e valida a estrutura."""
    with open(caminho, encoding="utf-8") as f:
        arvore = yaml.safe_load(f) or {}
    return validar_regras(arvore)


def valor_da_regra(regras: dict[str, dict], chave: str):
    """Valor de uma regra; erro explícito se a regra não existir ou estiver PENDENTE."""
    if chave not in regras:
        raise KeyError(f"regra inexistente: {chave}")
    regra = regras[chave]
    if regra["status"] == "PENDENTE":
        raise RegraPendente(f"regra {chave} está PENDENTE (pergunta {regra['pergunta_ref']})")
    return regra["valor"]
