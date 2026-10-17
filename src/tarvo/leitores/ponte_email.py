"""Leitor do e-mail da Ponte Câmbio (`03_email_ponte_cambio_*.eml`) e do anexo .xlsx.

Armadilhas de leitura encontradas na exploração:
- MIME multipart; assunto em encoded-word UTF-8; corpo text/plain em quoted-printable.
- O corpo traz informação de negócio (participação de 50% do spread realizado, data de
  crédito, NF de intermediação, status "APROVADO C/ RESSALVA", prazo de contestação,
  CNPJ da Ponte). O leitor devolve o texto; a interpretação fica em `regras.yaml`.
- Anexo .xlsx em base64: usar o pacote `email` em vez de fatiar linhas (a última linha
  do base64 é curta e some num filtro por tamanho).
- Aba "Operações": título em R1–R3 (parceiro, CNPJ, competência), cabeçalho em R5,
  dados até a primeira linha vazia; depois vêm linhas de total
  ("Total de operações:", "Spread total R$:") que NÃO são dados.
- Aba "Resumo": totais por moeda (só para conferência).
- Datas como serial do Excel; CNPJ com e sem máscara; nome cortado em 20 caracteres.
- Floats binários (72214.46000000001): converter via repr → Decimal e quantizar.
- `Nº Operação` pode repetir (PC-0926-0162 aparece 2×, a 2ª com obs "reprocessada").
  O leitor preserva as duas linhas; a duplicidade é tratada depois.
- `ref_origem` = `Nº Operação` (a linha da planilha também é guardada).

A aba é achada pelo cabeçalho ("Nº Operação"), as colunas pelo nome. Valor fora do
formato vira linha inválida com o motivo, nunca é corrigido.
"""

from __future__ import annotations

import email
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from email import policy
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

from tarvo.formatos import FormatoInvalido, decimal_de_celula, texto_de_celula
from tarvo.leitores.orbe import ErroLeitura, LinhaInvalida
from tarvo.modelo import Aviso, OperacaoPonte

CABECALHO_CHAVE = "Nº Operação"
# coluna → (campo, casas decimais | "data" | "texto")
COLUNAS = {
    "Nº Operação": ("ref_origem", "texto"),
    "Data Contratação": ("data_contratacao", "data"),
    "Data Liquidação": ("data_liquidacao", "data"),
    "CNPJ Cliente": ("cnpj_cliente_bruto", "texto"),
    "Cliente": ("cliente", "texto"),
    "Moeda": ("moeda", "texto"),
    "Valor ME": ("valor_me", 2),
    "Taxa Cliente": ("taxa_cliente", 4),
    "PTAX Ref.": ("ptax_ref", 4),
    "Valor R$": ("valor_brl", 2),
    "Spread R$": ("spread_brl", 2),
    "Spread %": ("spread_pct", 6),
    "Spread Estimado R$ (D-1)": ("spread_estimado_brl", 2),
    "IOF R$": ("iof_brl", 2),
    "Status Compliance": ("status_compliance", "texto"),
    "Observação": ("observacao", "texto"),
}
_RE_COMPETENCIA = re.compile(r"Compet[êe]ncia:\s*(\d{2})/(\d{4})")


@dataclass(frozen=True)
class EmailPonte:
    remetente: str
    data_envio: str
    assunto: str
    corpo: str
    nome_anexo: str
    anexo_xlsx: bytes


@dataclass
class LeituraPonte:
    arquivo: str  # nome do .eml (é o arquivo do data pack)
    nome_anexo: str
    competencia: tuple[int, int] | None = None  # (ano, mês)
    operacoes: list[OperacaoPonte] = field(default_factory=list)
    linhas_invalidas: list[LinhaInvalida] = field(default_factory=list)
    avisos: list[Aviso] = field(default_factory=list)
    totais_declarados: dict[str, Decimal] = field(default_factory=dict)  # rótulo → valor
    total_linhas_dados: int = 0


def ler_email(caminho: Path) -> EmailPonte:
    """Decodifica o .eml: cabeçalhos, corpo em texto e bytes do anexo .xlsx."""
    msg = email.message_from_bytes(caminho.read_bytes(), policy=policy.default)
    corpo_parte = msg.get_body(preferencelist=("plain",))
    corpo = corpo_parte.get_content() if corpo_parte is not None else ""
    anexos = [p for p in msg.iter_attachments() if (p.get_filename() or "").lower().endswith(".xlsx")]
    if len(anexos) != 1:
        raise ErroLeitura(f"{caminho.name}: esperado 1 anexo .xlsx, achei {len(anexos)}")
    anexo = anexos[0]
    return EmailPonte(
        remetente=str(msg.get("From", "")),
        data_envio=str(msg.get("Date", "")),
        assunto=str(msg.get("Subject", "")),
        corpo=corpo,
        nome_anexo=anexo.get_filename(),
        anexo_xlsx=anexo.get_payload(decode=True),
    )


def ler_operacoes(anexo_xlsx: bytes, arquivo: str, nome_anexo: str, rotulos_total: list[str]) -> LeituraPonte:
    """Lê a aba de operações do anexo. `rotulos_total` vem de `ponte.linhas_que_nao_sao_dados`."""
    wb = load_workbook(io.BytesIO(anexo_xlsx), data_only=True)
    res = LeituraPonte(arquivo=arquivo, nome_anexo=nome_anexo)
    achado = _achar_aba(wb)
    if achado is None:
        raise ErroLeitura(f"{arquivo}/{nome_anexo}: nenhuma aba com o cabeçalho {CABECALHO_CHAVE!r}")
    ws, linha_cab, cols = achado
    faltando = [c for c in COLUNAS if c not in cols]
    if faltando:
        raise ErroLeitura(f"{arquivo}/{nome_anexo}: colunas não encontradas no cabeçalho R{linha_cab}: {faltando}")

    for r in range(1, linha_cab):
        texto = " ".join(t for i in range(1, ws.max_column + 1) if (t := texto_de_celula(ws.cell(r, i).value)))
        if m := _RE_COMPETENCIA.search(texto):
            res.competencia = (int(m.group(2)), int(m.group(1)))
    if res.competencia is None:
        res.avisos.append(Aviso(arquivo, "-", "competência não encontrada no cabeçalho do relatório"))

    fim_do_bloco = False
    for r in range(linha_cab + 1, ws.max_row + 1):
        brutos = {c: ws.cell(r, i).value for c, i in cols.items()}
        vazia = all(texto_de_celula(ws.cell(r, i).value) is None for i in range(1, ws.max_column + 1))
        if vazia:
            fim_do_bloco = True
            continue
        primeira = texto_de_celula(ws.cell(r, 1).value) or ""
        if primeira in rotulos_total:
            valor = ws.cell(r, 2).value
            try:
                res.totais_declarados[primeira] = decimal_de_celula(valor)
            except FormatoInvalido:
                res.avisos.append(Aviso(arquivo, f"R{r}", f"total declarado ilegível: {primeira} {valor!r}"))
            continue
        if fim_do_bloco:
            res.avisos.append(Aviso(arquivo, f"R{r}", f"linha depois do bloco de dados, ignorada: {primeira!r}"))
            continue
        res.total_linhas_dados += 1
        ref = texto_de_celula(brutos["Nº Operação"]) or f"R{r}"
        try:
            campos = {campo: _converter(brutos[col], tipo) for col, (campo, tipo) in COLUNAS.items()}
        except FormatoInvalido as e:
            res.linhas_invalidas.append(LinhaInvalida(r, ref, str(e), repr(brutos)))
            continue
        if not campos["ref_origem"] or not campos["cnpj_cliente_bruto"]:
            res.linhas_invalidas.append(LinhaInvalida(r, ref, "Nº Operação ou CNPJ vazio", repr(brutos)))
            continue
        op = OperacaoPonte(linha_planilha=r, arquivo_origem=arquivo, **campos)
        if abs(op.valor_me * op.taxa_cliente - op.valor_brl) > Decimal("0.01"):
            res.avisos.append(Aviso(arquivo, f"R{r}", f"{op.ref_origem}: Valor R$ ≠ Valor ME × Taxa Cliente"))
        if abs(op.valor_me * (op.taxa_cliente - op.ptax_ref) - op.spread_brl) > Decimal("0.01"):
            res.avisos.append(Aviso(arquivo, f"R{r}", f"{op.ref_origem}: Spread R$ ≠ Valor ME × (Taxa Cliente − PTAX)"))
        res.operacoes.append(op)
    return res


def _achar_aba(wb):
    for ws in wb.worksheets:
        for r in range(1, min(ws.max_row, 30) + 1):
            textos = {texto_de_celula(ws.cell(r, i).value): i for i in range(1, ws.max_column + 1)}
            if CABECALHO_CHAVE in textos:
                return ws, r, {t: i for t, i in textos.items() if t}
    return None


def _converter(valor, tipo):
    if tipo == "texto":
        return texto_de_celula(valor)
    if tipo == "data":
        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            return from_excel(valor).date()  # serial do Excel
        raise FormatoInvalido(f"data ilegível: {valor!r}")
    d = decimal_de_celula(valor)
    q = d.quantize(Decimal(1).scaleb(-tipo))
    if abs(q - d) > Decimal("1e-9"):
        raise FormatoInvalido(f"número com mais de {tipo} casas: {valor!r}")
    return q


def ler_totais_declarados(anexo_xlsx: bytes) -> dict:
    """Lê a aba "Resumo" (totais por moeda), para conferência."""
    raise NotImplementedError
