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
        "pendencias.csv", "rastro.csv", "contestacao_ponte.csv", "sugestoes_regra.csv", "rascunhos",  # extras
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


def test_resumo_para_o_financeiro(tmp_path, capsys):
    assert main(["--dados", str(RAIZ / "data"), "--saida", str(tmp_path / "saida")]) == 0
    out = capsys.readouterr().out
    resumo = out[out.index("RESUMO DO FECHAMENTO"):]
    for trecho in ("RESUMO DO FECHAMENTO - setembro de 2026", "R$ 207.039,73", "R$ 39.543,45", "R$ 246.588,68  (21 notas)",
                   "checkout, devolver aos lojistas:          R$ 16.972,57  (200 transações)",
                   "recuperar da Orbe (contrato):            R$ 1.545,86",
                   "custo para a Tarvo (Orbe não avisada):    R$ 15.426,71", "por regra 184, por IA conferida 0, por decisão de uma pessoa 0",
                   "Pendências: 16", "os 6 do fechamento: comissoes_por_lojista.csv"):
        assert trecho in resumo, trecho
    assert "−" not in resumo  # console cp1252 do Windows não tem o sinal de menos tipográfico
