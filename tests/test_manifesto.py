"""D95 (Q-AM, Organização 14:11): 'um registro de cada execução: quais arquivos entraram, quantas linhas de cada,
data e hora'. O manifesto em saida/ é determinístico; data e hora vão para o log em logs/, fora do git."""

import csv
import hashlib
import re
import shutil
from datetime import datetime, timedelta, timezone

from tarvo.__main__ import executar, main
from tarvo.saida.manifesto import registrar_execucao
from conftest import DADOS, RAIZ


def _ler(pasta):
    with open(pasta / "manifesto.csv", encoding="utf-8", newline="") as f:
        return {l["arquivo"]: l for l in csv.DictReader(f, delimiter=";")}


def test_manifesto_lista_cada_arquivo_com_linhas_e_sha256(tmp_path):
    executar(DADOS, tmp_path, RAIZ / "regras.yaml")
    m = _ler(tmp_path)
    assert {n: int(l["linhas_lidas"]) for n, l in m.items() if l["linhas_lidas"] and n != "regras.yaml"} == {
        "01_orbe_relatorio_comissoes_set2026.csv": 1943, "06_orbe_ajustes_tardios_set2026.csv": 14,
        "02_tabela_taxas_contratadas.xlsx": 25, "03_email_ponte_cambio_relatorio_set2026.eml": 233,
        "04_plano_de_contas_fenix_erp.csv": 52, "05a_extrato_banco_aurora_cc4471_set2026.csv": 84,
        "05b_extrato_banco_meridiano_cc90233_set2026.ofx": 100,
    }
    for arq in DADOS.iterdir():
        if arq.is_file():
            assert m[arq.name]["sha256"] == hashlib.sha256(arq.read_bytes()).hexdigest()
            assert int(m[arq.name]["bytes"]) == arq.stat().st_size
    assert m["00_LEIA-ME.md"]["papel"].startswith("não lido")
    assert m["regras.yaml"]["papel"].startswith("versão das regras: CONFIRMADO ")
    normalizado = (RAIZ / "regras.yaml").read_bytes().replace(b"\r\n", b"\n")
    assert m["regras.yaml"]["sha256"] == hashlib.sha256(normalizado).hexdigest()  # igual no Windows e no Linux


def test_manifesto_deterministico_e_sem_data_hora(tmp_path):
    executar(DADOS, tmp_path / "a", RAIZ / "regras.yaml")
    executar(DADOS, tmp_path / "b", RAIZ / "regras.yaml")
    a = (tmp_path / "a" / "manifesto.csv").read_bytes()
    assert a == (tmp_path / "b" / "manifesto.csv").read_bytes()
    assert not re.search(rb"\d{2}:\d{2}:\d{2}|20\d{2}-\d{2}-\d{2}T", a)


def test_dado_alterado_muda_o_sha256(tmp_path):
    dados = tmp_path / "d"
    shutil.copytree(DADOS, dados)
    (dados / "00_LEIA-ME.md").write_bytes((DADOS / "00_LEIA-ME.md").read_bytes() + b"\n")
    executar(dados, tmp_path / "s", RAIZ / "regras.yaml")
    executar(DADOS, tmp_path / "o", RAIZ / "regras.yaml")
    assert _ler(tmp_path / "s")["00_LEIA-ME.md"]["sha256"] != _ler(tmp_path / "o")["00_LEIA-ME.md"]["sha256"]


def test_log_da_execucao_tem_data_hora_e_fica_fora_da_saida(tmp_path):
    saida = tmp_path / "saida"
    assert main(["--dados", str(DADOS), "--saida", str(saida), "--sem-ia"]) == 0
    (log,) = (tmp_path / "logs").glob("execucao_*.log")
    texto = log.read_text(encoding="utf-8")
    assert re.search(r"^execução: 20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", texto)
    assert "01_orbe_relatorio_comissoes_set2026.csv; relatório da Orbe (checkout); linhas lidas 1943" in texto
    assert "notas a emitir: 243284.29 (21 notas)" in texto
    assert not list(saida.glob("*.log"))


def test_registrar_execucao_um_arquivo_por_execucao(tmp_path):
    fuso = timezone(timedelta(hours=-3))
    linhas = [{"arquivo": "x.csv", "papel": "teste", "linhas_lidas": 1, "bytes": 2, "sha256": "ab"}]
    a = registrar_execucao(tmp_path, linhas, ["python"], {}, agora=datetime(2026, 10, 17, 15, 0, 0, tzinfo=fuso))
    b = registrar_execucao(tmp_path, linhas, ["python"], {}, agora=datetime(2026, 10, 17, 15, 0, 1, tzinfo=fuso))
    assert (a.name, b.name) == ("execucao_20261017-150000.log", "execucao_20261017-150001.log")
    assert a.read_text(encoding="utf-8").startswith("execução: 2026-10-17T15:00:00-03:00")
