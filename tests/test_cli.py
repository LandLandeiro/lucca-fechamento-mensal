"""Teste de fumaça da CLI (E0)."""

import subprocess
import sys
from pathlib import Path

from tarvo.__main__ import main

RAIZ = Path(__file__).resolve().parents[1]


def test_help_roda_como_modulo():
    r = subprocess.run(
        [sys.executable, "-m", "tarvo", "--help"], cwd=RAIZ, capture_output=True, text=True
    )
    assert r.returncode == 0
    assert "--dados" in r.stdout and "--saida" in r.stdout


def test_lista_arquivos_do_data_pack(tmp_path, capsys):
    assert main(["--dados", str(RAIZ / "data"), "--saida", str(tmp_path / "saida")]) == 0
    out = capsys.readouterr().out
    assert "01_orbe_relatorio_comissoes_set2026.csv" in out
    assert (tmp_path / "saida").is_dir()


def test_pasta_de_dados_inexistente(tmp_path):
    assert main(["--dados", str(tmp_path / "nao_existe"), "--saida", str(tmp_path)]) == 2
