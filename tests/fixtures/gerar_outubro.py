"""Gera tests/fixtures/outubro/: DADO SINTÉTICO DE TESTE, a partir do data pack de setembro.

Só desloca as datas um mês para frente (set → out, ago → set, out → nov), mantendo o formato de
cada arquivo como chega (encoding, separador, fim de linha), e acrescenta quatro novidades:
  (i)   um EC novo, sem cadastro na planilha (2 vendas);
  (ii)  um estorno em outubro de uma venda de setembro da Bridge feita antes de 15/09 (TX88415459,
        05/09, crédito à vista, 2,59%): tem que usar a taxa antiga, pela data da venda original;
  (iii) no Meridiano, em 01/10, "TED RECEBIDA TARVO PAGAMENTOS LTDA - MESMA TITULARIDADE" de
        300.000,00 (a transferência que estava em trânsito no fim de setembro);
  (iv)  PIX recebidos "EDU ABROAD CONSULTORIA" no Meridiano (os 5 de setembro, deslocados): casam por
        regra pelo nome da Orbe ligado ao EC (D52);
  (v)   um PIX com nome NOVO: o primeiro aporte da Nórdica chega como "PIX RECEB NEI EDUCACAO
        INTERNACIONAL", que não está na planilha nem na Orbe; vai para a IA (mockada no teste);
  (vi)  a Atlas com contrato confirmado na planilha (vigência a partir de 10/09/2026, taxas SINTÉTICAS iguais
        às que a Orbe aplicava): com --orbe-anterior, as linhas de setembro dela entram na nota de outubro (Q-Q).
Os identificadores que carregam o mês são renumerados para não colidir com setembro (TX88… → TX89…,
TX87… → TX88…, AN88… → AN89…, PC-0926 → PC-1026, MRD202609 → MRD202610). Determinístico: o .xlsx e
o .eml saem com datas internas fixas.

Uso: python tests/fixtures/gerar_outubro.py [--origem data] [--destino tests/fixtures/outubro]
"""

from __future__ import annotations

import argparse
import calendar
import email
import io
import re
import zipfile
from datetime import date, datetime
from email import policy
from email.message import EmailMessage
from pathlib import Path

import openpyxl

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]

EC_NOVO = "1099000001"
NOME_EC_NOVO = "ESCOLA NOVA INTERCAMBIO"
ESTORNO_BRIDGE = ("TX89500001;08/10/2026;1075624862;ESCOLA BRIDGE IDIOMAS;ESTORNO;CREDITO A VISTA;1;HIPERCARD;"
                  "-1461,78;2,59;-37,86;-1423,92;TX88415459;05/09/2026")
VENDAS_EC_NOVO = [
    f"TX89500002;06/10/2026;{EC_NOVO};{NOME_EC_NOVO};VENDA;CREDITO A VISTA;1;VISA;2500,00;2,59;64,75;2435,25;;",
    f"TX89500003;20/10/2026;{EC_NOVO};{NOME_EC_NOVO};VENDA;PIX;1;;800,00;0,89;7,12;792,88;;",
]
FITID_TED_300K = "MRD2026100001"
NOME_NOVO_ANTES, NOME_NOVO = "PIX RECEB NORDICA EDUCACAO INTERNA", "PIX RECEB NEI EDUCACAO INTERNACIONAL"


def mais_um_mes(d: date) -> date:
    ano, mes = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return date(ano, mes, min(d.day, calendar.monthrange(ano, mes)[1]))


def _dmy(m: re.Match) -> str:
    d = mais_um_mes(date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _my(m: re.Match) -> str:
    mes, ano = int(m.group(1)), int(m.group(2))
    ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    return f"{mes:02d}/{ano}"


RE_DMY = re.compile(r"\b(\d{2})/(\d{2})/(20\d{2})\b")
RE_MY = re.compile(r"(?<![\d/])(\d{2})/(20\d{2})\b")  # "FOLHA 08/2026", "Competência: 09/2026"


def deslocar_texto(t: str) -> str:
    return RE_MY.sub(_my, RE_DMY.sub(_dmy, t))


def renumerar(t: str) -> str:
    t = re.sub(r"\b(TX|AN)8([78])(\d{6})\b", lambda m: f"{m.group(1)}8{int(m.group(2)) + 1}{m.group(3)}", t)
    return t.replace("PC-0926-", "PC-1026-").replace("MRD202609", "MRD202610")


def orbe(origem: Path, destino: Path) -> None:
    src = next(origem.glob("01_orbe_*.csv"))
    texto = src.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in texto else "\n"
    linhas = texto.split(nl)
    cab, corpo = linhas[0], [l for l in linhas[1:] if l]
    # o estorno (ii) referencia uma venda real de setembro: renumerar antes, acrescentar depois
    novas = [renumerar(deslocar_texto(l)) for l in corpo] + VENDAS_EC_NOVO + [ESTORNO_BRIDGE]
    (destino / src.name.replace("set2026", "out2026")).write_bytes((nl.join([cab] + novas) + nl).encode("utf-8"))


def aurora(origem: Path, destino: Path) -> None:
    src = next(origem.glob("05a_*.csv"))
    texto = src.read_bytes().decode("utf-8")
    # "Período: 01/09/2026 a 30/09/2026" → até o último dia de outubro; saldos e linhas físicas iguais
    texto = deslocar_texto(texto).replace("01/10/2026 a 30/10/2026", "01/10/2026 a 31/10/2026")
    (destino / src.name.replace("set2026", "out2026")).write_bytes(texto.encode("utf-8"))


def meridiano(origem: Path, destino: Path) -> None:
    src = next(origem.glob("05b_*.ofx"))
    texto = src.read_bytes().decode("cp1252")

    def data_ofx(m: re.Match) -> str:
        d = mais_um_mes(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        return f"{d.year}{d.month:02d}{d.day:02d}{m.group(4)}"

    texto = re.sub(r"(20\d{2})(\d{2})(\d{2})(\d{6}\[)", data_ofx, texto)
    texto = texto.replace("<DTEND>20261030235959", "<DTEND>20261031235959")
    texto = texto.replace("<DTASOF>20261030235959", "<DTASOF>20261031235959")
    texto = renumerar(RE_MY.sub(_my, texto))
    texto = texto.replace(NOME_NOVO_ANTES, NOME_NOVO, 1)  # (v) só o primeiro aporte da Nórdica
    nl ="\r\n" if "\r\n" in texto else "\n"
    assert FITID_TED_300K not in texto
    ted = nl.join(["<STMTTRN>", "<TRNTYPE>CREDIT", "<DTPOSTED>20261001100000[-3:BRT]", "<TRNAMT>300000.00",
                   f"<FITID>{FITID_TED_300K}", "<CHECKNUM>300000", "<MEMO>TED RECEBIDA TARVO PAGAMENTOS LTDA - MESMA TITULARIDADE",
                   "</STMTTRN>"])
    i = texto.index("<STMTTRN>")
    texto = texto[:i] + ted + nl + texto[i:]
    m = re.search(r"<BALAMT>(-?\d+\.\d{2})", texto)
    novo = f"{float(m.group(1)) + 300000:.2f}"  # saldo final do OFX inclui a TED de 300 mil
    texto = texto[:m.start(1)] + novo + texto[m.end(1):]
    (destino / src.name.replace("set2026", "out2026")).write_bytes(texto.encode("cp1252"))


def _zip_deterministico(conteudo: bytes, quando: tuple) -> bytes:
    entrada, saida = zipfile.ZipFile(io.BytesIO(conteudo)), io.BytesIO()
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        for info in entrada.infolist():
            novo = zipfile.ZipInfo(info.filename, date_time=quando)
            novo.compress_type = zipfile.ZIP_DEFLATED
            dados = entrada.read(info.filename)
            if info.filename == "docProps/core.xml":  # o openpyxl grava a hora do save: fixa
                carimbo = "%04d-%02d-%02dT%02d:%02d:%02dZ" % quando
                dados = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*", lambda m: m.group(1) + carimbo.encode(), dados)
            z.writestr(novo, dados)
    return saida.getvalue()


def ponte(origem: Path, destino: Path) -> None:
    src = next(origem.glob("03_email_*.eml"))
    msg = email.message_from_bytes(src.read_bytes(), policy=policy.default)
    corpo = msg.get_body(preferencelist=("plain",)).get_content()
    anexo = next(p for p in msg.iter_attachments() if (p.get_filename() or "").endswith(".xlsx"))
    wb = openpyxl.load_workbook(io.BytesIO(anexo.get_content()))
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, datetime):
                    c.value = datetime.combine(mais_um_mes(c.value.date()), c.value.time())
                elif isinstance(c.value, str):
                    c.value = renumerar(deslocar_texto(c.value))
    wb.properties.created = wb.properties.modified = datetime(2026, 11, 2, 7, 12)
    buf = io.BytesIO()
    wb.save(buf)
    xlsx = _zip_deterministico(buf.getvalue(), (2026, 11, 2, 7, 12, 0))

    novo = EmailMessage(policy=policy.default)
    for h in ("From", "To", "Cc"):
        novo[h] = msg[h]
    novo["Date"] = "Mon, 02 Nov 2026 07:15:03 -0300"
    novo["Subject"] = deslocar_texto(str(msg["Subject"]))
    novo["Message-ID"] = "<relatorio-102026@pontecambio.com.br>"
    novo.set_content(deslocar_texto(corpo))
    nome = deslocar_texto(anexo.get_filename()).replace("092026", "102026")
    novo.add_attachment(xlsx, maintype="application", subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        filename=nome)
    novo.set_boundary("===============1026000000000000000==")
    (destino / src.name.replace("set2026", "out2026")).write_bytes(novo.as_bytes())


def copiar_sem_mes(origem: Path, destino: Path) -> None:
    src = next(origem.glob("04_plano_de_contas*.csv"))
    (destino / src.name).write_bytes(src.read_bytes())


# (vi) o comercial confirmou a Atlas: linha nova na aba vigente, valendo desde 10/09 (Q-Q). Taxas SINTÉTICAS,
# iguais às que a Orbe já aplicava à Atlas em setembro (para o teste não misturar divergência com faturamento)
LINHA_ATLAS = ("Atlas Idiomas Ltda", "39566044000119", "1076801732", 0.0199, 0.0349, 0.0399, 0.0449, 0.0099, 0.021, None,
               "a partir de 10/09/2026", "DADO SINTÉTICO: contrato confirmado pelo comercial em outubro")


def taxas(origem: Path, destino: Path) -> None:
    src = next(origem.glob("02_tabela_taxas_contratadas*.xlsx"))
    wb = openpyxl.load_workbook(src)
    ws = wb["Taxas vigentes"]
    cab = next(r[0].row for r in ws.iter_rows() if r[0].value == "Lojista")
    vazia = next(r for r in range(cab + 1, ws.max_row + 2) if all(c.value is None for c in ws[r]))
    ws.insert_rows(vazia)
    for col, valor in enumerate(LINHA_ATLAS, start=1):
        ws.cell(vazia, col).value = valor
    wb.properties.created = wb.properties.modified = datetime(2026, 11, 2, 7, 12)
    buf = io.BytesIO()
    wb.save(buf)
    (destino / src.name).write_bytes(_zip_deterministico(buf.getvalue(), (2026, 11, 2, 7, 12, 0)))


LEIA_ME = """# DADO SINTÉTICO DE TESTE: não é dado real da Tarvo

Gerado por `tests/fixtures/gerar_outubro.py` a partir do data pack de setembro (`data/`), só para provar
que o fechamento roda em outubro sem mudar código (`tests/test_outubro.py`). As datas foram deslocadas
um mês (set → out), os identificadores com o mês foram renumerados, e há seis novidades:

1. um EC novo (1099000001, "ESCOLA NOVA INTERCAMBIO"), sem cadastro na planilha;
2. um estorno em 08/10 da venda TX88415459 da Bridge, de 05/09 (antes da taxa nova de 15/09);
3. no Meridiano, em 01/10, a TED de 300.000,00 de mesma titularidade (a transferência que estava em trânsito);
4. PIX recebidos "EDU ABROAD CONSULTORIA" (casam pelo nome da Orbe ligado ao EC);
5. um aporte da Nórdica com nome novo ("PIX RECEB NEI EDUCACAO INTERNACIONAL"), que vai para a IA;
6. a Atlas com contrato na planilha (linha nova, vigência a partir de 10/09/2026, taxas sintéticas).

Os valores e o plano de contas são os de setembro; a planilha de taxas é a de setembro mais a linha da Atlas. Não use estes números para nada além de teste.
"""


def gerar(origem: Path, destino: Path) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    for p in destino.iterdir():
        if p.is_file():
            p.unlink()
    orbe(origem, destino)
    aurora(origem, destino)
    meridiano(origem, destino)
    ponte(origem, destino)
    copiar_sem_mes(origem, destino)
    taxas(origem, destino)
    (destino / "README.md").write_bytes(LEIA_ME.encode("utf-8"))
    return destino


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--origem", type=Path, default=RAIZ / "data")
    ap.add_argument("--destino", type=Path, default=AQUI / "outubro")
    a = ap.parse_args()
    print(gerar(a.origem, a.destino))
