"""Painel (`python -m tarvo.painel`): determinístico, números iguais aos CSVs, rastro inteiro, sem rede.

O painel é gerado numa cópia de `saida/` (o repositório não muda). Os totais são lidos dos
data-attributes e do JSON embutido e conferidos contra os CSVs, recalculados aqui.
"""

import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

import pytest

from tarvo.leitores.orbe import ler_orbe
from tarvo.painel import gerar_painel
from tarvo.painel.__main__ import main

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "saida"
DADOS = RAIZ / "data"
REGRAS = RAIZ / "regras.yaml"


def _ler(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _escrever(caminho: Path, linhas: list[dict], colunas: list[str]) -> None:
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)


def _copiar_saida(destino: Path, rascunhos: bool = True) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    for c in SAIDA.glob("*.csv"):
        shutil.copy(c, destino / c.name)
    if rascunhos and (SAIDA / "rascunhos").is_dir():
        shutil.copytree(SAIDA / "rascunhos", destino / "rascunhos")
    return destino


class _Elementos(HTMLParser):
    """Guarda (tag, atributos) de todo elemento e a pilha de `section` em que ele está."""

    def __init__(self):
        super().__init__()
        self.elementos: list[tuple[str, dict, tuple[str, ...]]] = []
        self.pilha: list[tuple[str, str]] = []
        self.dados_json = ""
        self._no_json = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        secoes = tuple(i for t, i in self.pilha if t == "section" and i)
        self.elementos.append((tag, a, secoes))
        self._no_json = tag == "script" and a.get("id") == "dados"
        if tag not in ("meta", "link", "input", "br", "img", "path", "rect", "circle"):
            self.pilha.append((tag, a.get("id", "")))

    def handle_endtag(self, tag):
        for i in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[i][0] == tag:
                del self.pilha[i:]
                break
        self._no_json = False

    def handle_data(self, data):
        if self._no_json:
            self.dados_json += data

    def com(self, atributo: str, secao: str | None = None):
        return [a for _, a, s in self.elementos if atributo in a and (secao is None or secao in s)]


def _abrir(caminho: Path) -> _Elementos:
    p = _Elementos()
    p.feed(caminho.read_text(encoding="utf-8"))
    return p


@pytest.fixture(scope="module")
def painel(tmp_path_factory):
    pasta = _copiar_saida(tmp_path_factory.mktemp("saida"))
    caminho, tamanho_json = gerar_painel(pasta, DADOS, REGRAS)
    return pasta, caminho, tamanho_json, _abrir(caminho)


def test_gerar_duas_vezes_da_os_mesmos_bytes(painel, tmp_path):
    pasta, caminho, _, _ = painel
    outra = _copiar_saida(tmp_path / "outra")
    caminho2, _ = gerar_painel(outra, DADOS, REGRAS)
    assert caminho.read_bytes() == caminho2.read_bytes()


def test_cli_gera_painel_html(tmp_path, capsys):
    pasta = _copiar_saida(tmp_path / "saida")
    assert main(["--saida", str(pasta), "--dados", str(DADOS), "--regras", str(REGRAS)]) == 0
    assert (pasta / "painel.html").exists()
    assert "painel.html gerado" in capsys.readouterr().out


def test_json_do_rastro_tem_todas_as_linhas(painel):
    pasta, _, tamanho_json, p = painel
    dados = json.loads(p.dados_json.replace("<\\/", "</"))
    rastro = _ler(pasta / "rastro.csv")
    cols = dados["rastro"]["cols"]
    assert len(dados["rastro"]["rows"]) == len(rastro)
    assert [dict(zip(cols, r)) for r in dados["rastro"]["rows"]] == [{c: (l[c] or "") for c in cols} for l in rastro]
    assert tamanho_json < 3 * 1024 * 1024


def test_saidas_do_json_fecham_com_o_rastro(painel):
    pasta, _, _, p = painel
    dados = json.loads(p.dados_json.replace("<\\/", "</"))
    soma: dict[str, Decimal] = defaultdict(Decimal)
    for l in _ler(pasta / "rastro.csv"):
        soma[l["id_saida"]] += Decimal(l["valor"])
    for ident, s in dados["saidas"].items():
        assert Decimal(s["soma"]) == soma[ident], ident
        if s["confere"] is not None:
            assert s["confere"] is True, ident  # a saída já validada: toda soma confere


def test_titulo_bate_com_notas_a_emitir(painel):
    pasta, _, _, p = painel
    notas = _ler(pasta / "notas_a_emitir.csv")
    (h1,) = p.com("data-total-notas")
    assert Decimal(h1["data-total-notas"]) == sum(Decimal(n["valor_brl"]) for n in notas)
    assert int(h1["data-qtd-notas"]) == len(notas)
    linhas_nota = {a["data-nota"]: Decimal(a["data-valor"]) for a in p.com("data-nota")}
    assert linhas_nota == {n["id_saida"]: Decimal(n["valor_brl"]) for n in notas}


def test_cada_pendencia_aparece_uma_vez_no_kanban(painel):
    pasta, _, _, p = painel
    pend = _ler(pasta / "pendencias.csv")
    cartoes = p.com("data-pendencia", secao="decisoes")
    contagem = Counter(a["data-pendencia"] for a in cartoes)
    assert set(contagem) == {l["id_saida"] for l in pend}
    assert set(contagem.values()) == {1}
    valor = {l["id_saida"]: l["valor_brl"] for l in pend}
    for a in cartoes:
        assert (Decimal(a["data-valor"]) if a["data-valor"] else None) == (Decimal(valor[a["data-pendencia"]]) if valor[a["data-pendencia"]] else None)


def test_totais_das_colunas_e_grupos_batem_com_pendencias(painel):
    pasta, _, _, p = painel
    pend = {l["id_saida"]: l for l in _ler(pasta / "pendencias.csv")}
    cartoes = p.com("data-pendencia", secao="decisoes")
    # em jogo = Σ |valor_brl| das pendências que somam (data-soma=1), recalculado do CSV
    em_jogo = sum(abs(Decimal(pend[a["data-pendencia"]]["valor_brl"])) for a in cartoes
                  if a["data-soma"] == "1" and pend[a["data-pendencia"]]["valor_brl"])
    (total,) = p.com("data-total-decisao")
    assert Decimal(total["data-total-decisao"]) == em_jogo
    colunas = [a for a in p.com("data-coluna") if a["data-coluna"] != "regra"]
    assert sum(Decimal(a["data-total"]) for a in colunas) == em_jogo
    assert sum(int(a["data-qtd"]) for a in colunas) == len(pend)
    grupos = p.com("data-grupo")
    assert sum(Decimal(a["data-total"]) for a in grupos) == em_jogo
    nao_somam = {a["data-pendencia"] for a in cartoes if a["data-soma"] == "0"}
    tipos_fora = {pend[i]["tipo"] for i in nao_somam}
    assert {"TRANSFERENCIA_EM_TRANSITO", "APORTE_SEM_OPERACAO"} & {l["tipo"] for l in pend.values()} <= tipos_fora


def test_contratado_bate_com_comissoes_divergencias_e_orbe(painel):
    pasta, _, _, p = painel
    linhas = {a["data-id"]: a for a in p.com("data-situacao") if "data-id" in a}
    coms = [c for c in _ler(pasta / "comissoes_por_lojista.csv") if c["linha_negocio"] == "CHECKOUT"]
    divs = [d for d in _ler(pasta / "divergencias_taxa.csv") if d["linha_negocio"] == "CHECKOUT"]
    div_cnpj = defaultdict(Decimal)
    for d in divs:
        div_cnpj[d["cnpj"]] += Decimal(d["diferenca_brl"])
    for c in coms:
        a = linhas[c["id_saida"]]
        assert Decimal(a["data-planilha"]) == Decimal(c["comissao_brl"])
        assert Decimal(a["data-divergencia"]) == div_cnpj[c["cnpj"]]
        assert a["data-situacao"] == ("com_diferenca" if div_cnpj[c["cnpj"]] else "confere")
    sem_contrato = [l for l in _ler(pasta / "pendencias.csv") if l["tipo"] == "SEM_CONTRATO_VIGENTE"]
    assert {l["id_saida"] for l in sem_contrato} == {i for i, a in linhas.items() if a["data-situacao"] == "sem_contrato"}
    # resíduo de truncamento = Σ valor_taxa da Orbe (linhas das comissões) − Σ comissão − Σ divergência
    rastro = _ler(pasta / "rastro.csv")
    refs = [(r["arquivo_origem"], r["ref_origem"]) for r in rastro if r["id_saida"].startswith("COM-") and r["id_saida"].endswith("-CHECKOUT")]
    arquivos = {r["arquivo_origem"] for r in rastro if r["id_saida"].startswith("COM-") and r["id_saida"].endswith("-CHECKOUT")}
    vt = {(a, t.ref_origem): t.valor_taxa for a in arquivos for t in ler_orbe(DADOS / a).transacoes}
    residuo = sum(vt[r] for r in refs) - sum(Decimal(c["comissao_brl"]) for c in coms) - sum(div_cnpj.values())
    (nota,) = p.com("data-residuo")
    assert Decimal(nota["data-residuo"]) == residuo
    for a in linhas.values():  # a linha "pela taxa aplicada" é Σ valor_taxa da Orbe
        if a["data-situacao"] != "sem_contrato":
            ids = [(r["arquivo_origem"], r["ref_origem"]) for r in rastro if r["id_saida"] == a["data-id"]]
            assert Decimal(a["data-aplicada"]) == sum(vt[i] for i in ids)


def test_aba_remessa_bate_com_comissoes_e_divergencias(painel):
    pasta, _, _, p = painel
    linhas = {a["data-remessa"]: a for a in p.com("data-remessa")}
    coms = [c for c in _ler(pasta / "comissoes_por_lojista.csv") if c["linha_negocio"] == "REMESSA"]
    assert set(linhas) == {c["id_saida"] for c in coms}
    div_cnpj, negativo, ate_contrato = defaultdict(Decimal), defaultdict(Decimal), defaultdict(Decimal)
    for d in _ler(pasta / "divergencias_taxa.csv"):
        if d["linha_negocio"] == "REMESSA":
            if Decimal(d["spread_brl"]) < 0:  # spread negativo: outra natureza (Q-O), não é "com diferença"
                negativo[d["cnpj"]] += Decimal(d["spread_brl"])
                ate_contrato[d["cnpj"]] += Decimal(d["diferenca_brl"])
            else:
                div_cnpj[d["cnpj"]] += Decimal(d["diferenca_brl"])
    for c in coms:
        a = linhas[c["id_saida"]]
        assert Decimal(a["data-comissao"]) == Decimal(c["comissao_brl"])
        assert Decimal(a["data-divergencia"]) == div_cnpj[c["cnpj"]]
        esperado = "com_diferenca" if div_cnpj[c["cnpj"]] else ("spread_negativo" if negativo[c["cnpj"]] else "confere")
        assert a["data-situacao"] == esperado
        assert Decimal(a["data-negativo"]) == negativo[c["cnpj"]]
        assert Decimal(a["data-negativo-contrato"]) == ate_contrato[c["cnpj"]]
    # os dois valores do spread negativo (Q-AA 3): a pendência leva a diferença até o contrato
    pend = [l for l in _ler(pasta / "pendencias.csv") if l["id_saida"].endswith("SPREAD_NEGATIVO")]
    if pend:
        assert Decimal(pend[0]["valor_brl"]) == sum(ate_contrato.values())


def test_quebra_de_linha_do_checkout_nao_muda_os_bytes(tmp_path, monkeypatch):
    """autocrlf no Windows: CSS/JS com CRLF geram o mesmo painel que com LF (o CI roda no Ubuntu)."""
    import tarvo.painel as modulo

    ativos = tmp_path / "ativos"
    ativos.mkdir()
    for nome in ("estilo.css", "app.js"):
        texto = (modulo.AQUI / nome).read_text(encoding="utf-8").replace("\r\n", "\n")
        (ativos / nome).write_bytes(texto.replace("\n", "\r\n").encode("utf-8"))
    lf = _copiar_saida(tmp_path / "lf")
    crlf = _copiar_saida(tmp_path / "crlf")
    a, _ = gerar_painel(lf, DADOS, REGRAS)
    monkeypatch.setattr(modulo, "AQUI", ativos)
    b, _ = gerar_painel(crlf, DADOS, REGRAS)
    assert a.read_bytes() == b.read_bytes()


def test_premissas_assumo_e_contagem_por_status(painel):
    _, _, _, p = painel
    from tarvo.regras import carregar_regras

    regras = carregar_regras(REGRAS)
    contagem = Counter(r["status"] for r in regras.values() if not r.get("substituida"))
    for a in p.com("data-status"):
        assert int(a["data-qtd"]) == contagem.get(a["data-status"], 0)


def test_nenhuma_url_externa_alem_do_google_fonts(painel):
    _, caminho, _, _ = painel
    texto = caminho.read_text(encoding="utf-8")
    urls = set(re.findall(r"(?:https?:)?//[A-Za-z0-9.-]+\.[a-z]{2,}", texto))
    assert urls <= {"https://fonts.googleapis.com", "https://fonts.gstatic.com"}, urls
    assert not re.search(r"\b(?:src|href)\s*=\s*[\"']?(?:https?:)?//(?!fonts\.g)", texto)


def test_sem_data_de_geracao_e_com_sha256_dos_insumos(painel):
    _, caminho, _, _ = painel
    texto = caminho.read_text(encoding="utf-8")
    import hashlib

    for c in sorted(DADOS.iterdir()):
        if c.is_file():
            assert hashlib.sha256(c.read_bytes()).hexdigest()[:12] in texto, c.name
    assert not re.search(r"20\d\d-\d\d-\d\dT\d\d:\d\d", texto)


def test_campos_opcionais_aparecem_quando_existem(tmp_path):
    """natureza, ALERTA_* e rascunhos/ ainda não existem nesta saída: quando vierem, a seção aparece."""
    pasta = _copiar_saida(tmp_path / "saida")
    divs = _ler(pasta / "divergencias_taxa.csv")
    pend = _ler(pasta / "pendencias.csv")
    casa = next(p for p in pend if p["tipo"] == "DIVERGENCIA_CHECKOUT" and "Ninguém avisou" in p["motivo"])
    refs_casa = set(casa["ref_origem"].split("|"))
    for d in divs:
        d["natureza"] = "condicao_nao_informada" if d["ref_origem"] in refs_casa else (
            "contrato_orbe" if d["linha_negocio"] == "CHECKOUT" else "spread_acima_contrato")
    _escrever(pasta / "divergencias_taxa.csv", divs, list(divs[0].keys()))
    alerta = {"id_saida": "PEN-ALERTA_ANTECIPACAO-X", "tipo": "ALERTA_ANTECIPACAO", "ref_origem": "AN1",
              "valor_brl": "100.00", "motivo": "antecipação acima do vendido", "quem_decide": "Helena + comercial"}
    _escrever(pasta / "pendencias.csv", pend + [alerta], list(pend[0].keys()))
    (pasta / "rascunhos").mkdir(exist_ok=True)
    (pasta / "rascunhos" / "contestacao_orbe.md").write_text("rascunho", encoding="utf-8")

    caminho, _ = gerar_painel(pasta, DADOS, REGRAS)
    p = _abrir(caminho)
    grupos = {a["data-grupo"]: a for a in p.com("data-grupo")}
    assert "recuperar_orbe" in grupos and "devolver_lojista" in grupos
    devolver = Decimal(grupos["devolver_lojista"]["data-total"])
    assert devolver >= abs(Decimal(casa["valor_brl"]))
    texto = caminho.read_text(encoding="utf-8")
    assert 'class="alertas"' in texto and "antecipação acima do vendido" in texto
    assert 'href="rascunhos/contestacao_orbe.md"' in texto
    cartao = next(a for a in p.com("data-pendencia") if a["data-pendencia"] == "PEN-ALERTA_ANTECIPACAO-X")
    assert cartao["data-soma"] == "0"


def test_sem_campos_opcionais_as_secoes_somem(tmp_path):
    """Saída sem natureza, sem valor_a_devolver_brl, sem ALERTA_* e sem rascunhos/: gera, e as seções somem."""
    pasta = _copiar_saida(tmp_path / "saida", rascunhos=False)
    divs = _ler(pasta / "divergencias_taxa.csv")
    colunas = [c for c in divs[0] if c not in ("natureza", "valor_a_devolver_brl")]
    _escrever(pasta / "divergencias_taxa.csv", [{c: d[c] for c in colunas} for d in divs], colunas)
    pend = [l for l in _ler(pasta / "pendencias.csv") if not l["tipo"].upper().startswith("ALERTA")]
    _escrever(pasta / "pendencias.csv", pend, list(pend[0].keys()))
    caminho, _ = gerar_painel(pasta, DADOS, REGRAS)
    texto = caminho.read_text(encoding="utf-8")
    p = _abrir(caminho)
    assert 'class="alertas"' not in texto
    assert "rascunhos/" not in texto
    grupos = {a["data-grupo"]: a for a in p.com("data-grupo")}
    assert "recuperar_orbe" not in grupos  # sem natureza, nada se afirma sobre a Orbe
    divergencias = [l for l in pend if l["tipo"] == "DIVERGENCIA_CHECKOUT"]
    assert Decimal(grupos["devolver_lojista"]["data-total"]) == sum(abs(Decimal(l["valor_brl"])) for l in divergencias)


def test_custo_para_a_tarvo_e_devolver_menos_recuperar(painel):
    """Toda divergência de checkout volta ao lojista (Q-A, Q-U 4), pelo valor a devolver; recuperar = parte contrato_orbe."""
    pasta, _, _, p = painel
    divs = [d for d in _ler(pasta / "divergencias_taxa.csv") if d["linha_negocio"] == "CHECKOUT"]
    devolver = sum(Decimal(d["valor_a_devolver_brl"]) for d in divs)
    recuperar = sum(Decimal(d["valor_a_devolver_brl"]) for d in divs if d["natureza"] == "contrato_orbe")
    (custo,) = p.com("data-custo")
    assert Decimal(custo["data-devolver"]) == devolver
    assert Decimal(custo["data-recuperar"]) == recuperar
    assert Decimal(custo["data-custo"]) == devolver - recuperar
    grupos = {a["data-grupo"]: a for a in p.com("data-grupo")}
    assert Decimal(grupos["devolver_lojista"]["data-total"]) == devolver
    assert Decimal(grupos["recuperar_orbe"]["data-total"]) == 0  # não soma: é o mesmo valor que volta ao lojista
    assert Decimal(grupos["recuperar_orbe"]["data-a-parte"]) == recuperar
    # as pendências de divergência carregam o mesmo valor a devolver (o kanban usa valor_brl)
    pend = [l for l in _ler(pasta / "pendencias.csv") if l["tipo"] == "DIVERGENCIA_CHECKOUT"]
    assert sum(Decimal(l["valor_brl"]) for l in pend) == devolver
    itens = [a for a in p.com("data-item", secao="visao")]
    assert {a["data-item"] for a in itens} >= {l["id_saida"] for l in pend}


def test_premissas_do_hipoteses_com_a_contagem_do_resumo(painel):
    _, _, _, p = painel
    from tarvo.painel import ler_hipoteses

    hip = ler_hipoteses(RAIZ / "HIPOTESES.md")
    tabela = Counter(l["status"] for l in hip["linhas"])
    assert tabela == Counter({k: v for k, v in hip["contagem_resumo"].items() if v})  # o Resumo bate com a tabela
    assert hip["substituidas"] == hip["substituidas_resumo"]
    assert len(hip["linhas"]) + hip["substituidas"] == hip["total_resumo"]
    for a in p.com("data-hip-status"):
        assert int(a["data-qtd"]) == tabela.get(a["data-hip-status"], 0)
    listadas = {a["data-hipotese"] for a in p.com("data-hipotese")}
    assert listadas == {l["id"] for l in hip["linhas"] if l["status"] == "ASSUMO"}


def test_fechadas_por_regra_agrupadas(painel):
    pasta, _, _, p = painel
    cartoes = p.com("data-fechada", secao="decisoes")
    lancs = [l for l in _ler(pasta / "lancamentos_classificados.csv") if l["metodo"] in ("REGRA", "IA")]
    assert sum(int(a["data-qtd"]) for a in cartoes if a["data-fechada"] == "classificacao") == len(lancs)
    rastro = _ler(pasta / "rastro.csv")
    exc = Counter(r["id_saida"] for r in rastro if r["id_saida"].startswith("EXC-"))
    assert sorted(int(a["data-qtd"]) for a in cartoes if a["data-fechada"] == "exclusao") == sorted(exc.values())
    (coluna,) = [a for a in p.com("data-coluna") if a["data-coluna"] == "regra"]
    assert int(coluna["data-qtd"]) == len(cartoes)


def test_atlas_rotulo_de_referencia(painel):
    _, caminho, _, _ = painel
    texto = caminho.read_text(encoding="utf-8")
    assert texto.count("taxa cobrada pela Orbe (referência); comissão a definir pelo comercial") >= 3  # visão, kanban, tabela


def test_nenhum_caminho_local_no_html(painel):
    _, caminho, _, _ = painel
    texto = caminho.read_text(encoding="utf-8")
    assert not re.search(r"[A-Za-z]:[\\/]+Users", texto)


def test_python_m_tarvo_gera_o_painel_e_a_saida_continua_deterministica(tmp_path):
    """`python -m tarvo` gera saida/painel.html no fim; duas execuções dão os mesmos bytes, iguais aos da saída entregue."""
    from tarvo.__main__ import main as main_tarvo

    pastas = [tmp_path / "a", tmp_path / "outra pasta"]
    for pasta in pastas:
        assert main_tarvo(["--dados", str(DADOS), "--saida", str(pasta)]) == 0
    a, b = pastas
    arquivos = sorted(c.relative_to(a).as_posix() for c in a.rglob("*") if c.is_file())
    assert "painel.html" in arquivos
    assert arquivos == sorted(c.relative_to(b).as_posix() for c in b.rglob("*") if c.is_file())
    for nome in arquivos:
        assert (a / nome).read_bytes() == (b / nome).read_bytes(), nome
    # o CI (git diff --exit-code saida/) cobre também o painel: o versionado é o que a execução gera
    assert (a / "painel.html").read_bytes() == (SAIDA / "painel.html").read_bytes()


def test_fim_de_linha_do_regras_e_do_hipoteses_nao_muda_o_painel(painel, tmp_path):
    """autocrlf no Windows converte regras.yaml e HIPOTESES.md para CRLF no checkout: o hash dos insumos ignora isso."""
    pasta, caminho, _, _ = painel
    gerados = []
    for fim in ("\n", "\r\n"):
        raiz = tmp_path / ("crlf" if fim == "\r\n" else "lf")
        raiz.mkdir()
        for nome in ("regras.yaml", "HIPOTESES.md"):
            texto = (RAIZ / nome).read_text(encoding="utf-8")
            (raiz / nome).write_bytes(texto.replace("\r\n", "\n").replace("\n", fim).encode("utf-8"))
        saida = _copiar_saida(raiz / "saida")
        destino, _ = gerar_painel(saida, DADOS, raiz / "regras.yaml")
        gerados.append(destino.read_bytes())
    assert gerados[0] == gerados[1]
    assert gerados[0] == caminho.read_bytes()
