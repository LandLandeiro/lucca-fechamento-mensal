"""Conversões de formato exatas, usadas pelos leitores e pelo cadastro.

Responsabilidade: transformar texto/células das fontes em `Decimal`, `date` e CNPJ de 14
dígitos sem perder informação e sem adivinhar. Quando o valor não está num formato
conhecido, a função levanta `FormatoInvalido` (o chamador transforma em aviso/pendência).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

CENTAVO = Decimal("0.01")

_RE_DECIMAL_BR_SEM_MILHAR = re.compile(r"^-?\d+(,\d+)?$")
_RE_DECIMAL_BR_COM_MILHAR = re.compile(r"^-?\d{1,3}(\.\d{3})*(,\d+)?$")
_RE_DATA_BR = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_RE_PCT_TEXTO = re.compile(r"^(\d+(?:,\d+)?)\s*%$")
_RE_CNPJ_TEXTO = re.compile(r"^[\d./\-\s]+$")


class FormatoInvalido(ValueError):
    """Valor fora do formato esperado para a coluna."""


def decimal_br(texto: str, milhar: bool = False) -> Decimal:
    """'5773,57' → Decimal('5773.57'). Com `milhar=True` aceita '1.019.882,54'."""
    s = (texto or "").strip()
    padrao = _RE_DECIMAL_BR_COM_MILHAR if milhar else _RE_DECIMAL_BR_SEM_MILHAR
    if not padrao.match(s):
        raise FormatoInvalido(f"número fora do formato pt-BR: {texto!r}")
    return Decimal(s.replace(".", "").replace(",", ".") if milhar else s.replace(",", "."))


def data_br(texto: str) -> date:
    """'22/08/2026' → date(2026, 8, 22)."""
    m = _RE_DATA_BR.match((texto or "").strip())
    if not m:
        raise FormatoInvalido(f"data fora do formato DD/MM/AAAA: {texto!r}")
    dia, mes, ano = (int(g) for g in m.groups())
    try:
        return date(ano, mes, dia)
    except ValueError as e:
        raise FormatoInvalido(f"data inexistente: {texto!r}") from e


def decimal_de_celula(valor: object) -> Decimal:
    """Número de célula (int/float) → Decimal pela representação curta do float."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise FormatoInvalido(f"célula não numérica: {valor!r}")
    return Decimal(repr(valor)) if isinstance(valor, float) else Decimal(valor)


def taxa_de_celula(valor: object, casas: int) -> Decimal | str | None:
    """Taxa da planilha como fração exata.

    - vazio → None
    - número (0.0269 ou 0.007900000000000001) → Decimal quantizado em `casas` casas;
      erro se a quantização mudar o valor além de ruído de float (< 1e-12)
    - texto "2,69%" → Decimal('0.0269')
    - outro texto (ex.: "padrão") → devolvido como str, sem interpretar
    """
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    quantum = Decimal(1).scaleb(-casas)
    if isinstance(valor, str):
        m = _RE_PCT_TEXTO.match(valor.strip())
        if not m:
            return valor.strip()
        d = Decimal(m.group(1).replace(",", ".")) / 100
    else:
        d = decimal_de_celula(valor)
    q = d.quantize(quantum)
    if abs(q - d) > Decimal("1e-12"):
        raise FormatoInvalido(f"taxa com mais de {casas} casas: {valor!r}")
    return q


def normalizar_cnpj(valor: object) -> str | None:
    """CNPJ com 14 dígitos, ou None se o formato não permitir.

    - texto com ou sem máscara ('22.224.579/0001-09', '78576234000179'): só dígitos, exige 14
    - número (célula numérica perde o zero à esquerda: 3229837000103) → completa com zeros
    """
    if valor is None:
        return None
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        if isinstance(valor, float) and not valor.is_integer():
            return None
        s = str(int(valor))
        return s.zfill(14) if len(s) <= 14 else None
    s = str(valor).strip()
    if not s or not _RE_CNPJ_TEXTO.match(s):
        return None
    digitos = re.sub(r"\D", "", s)
    return digitos if len(digitos) == 14 else None


def cnpj_valido(cnpj: str) -> bool:
    """Confere os dois dígitos verificadores."""
    if not cnpj or len(cnpj) != 14 or not cnpj.isdigit() or len(set(cnpj)) == 1:
        return False

    def dv(base: str, pesos: list[int]) -> int:
        r = sum(int(d) * p for d, p in zip(base, pesos)) % 11
        return 0 if r < 2 else 11 - r

    d1 = dv(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = dv(cnpj[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return cnpj[12:] == f"{d1}{d2}"


def texto_de_celula(valor: object) -> str | None:
    """Célula → texto limpo (datas viram DD/MM/AAAA, números inteiros sem '.0')."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    s = str(valor).strip()
    return s or None


def fmt_dinheiro(valor: Decimal) -> str:
    """Decimal → '374.08' (ponto decimal, 2 casas). Exige valor já em centavos."""
    if valor != valor.quantize(CENTAVO):
        raise ValueError(f"valor com fração de centavo na saída: {valor}")
    return f"{valor.quantize(CENTAVO):.2f}"


def fmt_pct(fracao: Decimal) -> str:
    """Fração 0.0359 → '3.59' (percentual, sem zeros à direita)."""
    pct = (fracao * 100).normalize()
    return format(pct, "f")


def decimal_seguro(texto: str) -> Decimal:
    """Decimal de texto já em formato com ponto (usado pelo validador)."""
    try:
        return Decimal(texto)
    except InvalidOperation as e:
        raise FormatoInvalido(f"número inválido: {texto!r}") from e
