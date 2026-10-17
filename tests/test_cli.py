"""Teste de fumaça da CLI."""

import subprocess
import sys
from pathlib import Path

from tarvo.__main__ import main

RAIZ = Path(__file__).resolve().parents[1]


def test_help_roda_como_modulo():
    r = subprocess.run([sys.executable, "-m", "tarvo", "--help"], cwd=RAIZ, capture_output=True, text=True)
    assert r.returncode == 0
    assert "--dados" in r.stdout and "--saida" in r.stdout


def test_roda_o_minimo_e_valida(tmp_path, capsys):
    codigo = main(["--dados", str(RAIZ / "data"), "--saida", str(tmp_path / "saida"), "--regras", str(RAIZ / "regras.yaml")])
    out = capsys.readouterr().out
    assert codigo == 0
    assert "01_orbe_relatorio_comissoes_set2026.csv" in out
    assert "VALIDADOR: OK" in out
    assert "conservação do checkout e da remessa fecha" in out
    assert {p.name for p in (tmp_path / "saida").iterdir()} == {
        "comissoes_por_lojista.csv", "divergencias_taxa.csv", "lancamentos_classificados.csv", "notas_a_emitir.csv",
        "pendencias.csv", "rastro.csv", "contestacao_ponte.csv", "sugestoes_regra.csv",  # extras
    }


def test_console_cp1252_nao_derruba_a_cli(tmp_path):
    # console do Windows com saída redirecionada usa cp1252, que não tem "Σ"
    env = {**__import__("os").environ, "PYTHONIOENCODING": "cp1252"}
    r = subprocess.run(
        [sys.executable, "-m", "tarvo", "--dados", "data", "--saida", str(tmp_path), "--regras", "regras.yaml"],
        cwd=RAIZ, capture_output=True, env=env,
    )
    assert r.returncode == 0, r.stderr.decode("cp1252", errors="replace")[-500:]


def test_pasta_de_dados_inexistente(tmp_path):
    assert main(["--dados", str(tmp_path / "nao_existe"), "--saida", str(tmp_path)]) == 2


def test_regras_padrao_e_do_repositorio_nao_da_pasta_atual(tmp_path):
    """Rodar de fora do repo sem --regras usa o regras.yaml da raiz do repositório (D41)."""
    r = subprocess.run(
        [sys.executable, "-m", "tarvo", "--dados", str(RAIZ / "data"), "--saida", str(tmp_path / "saída com espaço")],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, r.stderr
    assert "VALIDADOR: OK" in r.stdout


def test_regras_explicito_tem_prioridade(tmp_path):
    codigo = main(["--dados", str(RAIZ / "data"), "--saida", str(tmp_path / "saida"), "--regras", str(tmp_path / "nao_existe.yaml")])
    assert codigo == 2
