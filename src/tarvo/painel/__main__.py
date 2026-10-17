"""CLI do painel: `python -m tarvo.painel --saida saida` gera `saida/painel.html` a partir da saída já gerada."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tarvo.painel import gerar_painel

REGRAS_PADRAO = Path(__file__).resolve().parents[3] / "regras.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tarvo.painel",
        description="Gera saida/painel.html (arquivo único, sem servidor) a partir de saida/*.csv, regras.yaml e data/.",
    )
    parser.add_argument("--saida", type=Path, default=Path("saida"), help="pasta dos CSVs gerados (padrão: saida)")
    parser.add_argument("--dados", type=Path, default=Path("data"), help="pasta do data pack (padrão: data)")
    parser.add_argument("--regras", type=Path, default=REGRAS_PADRAO, help="regras.yaml (padrão: o da raiz)")
    parser.add_argument("--hipoteses", type=Path, default=None, help="HIPOTESES.md (padrão: ao lado do regras.yaml)")
    args = parser.parse_args(argv)
    caminho, tamanho_json = gerar_painel(args.saida, args.dados, args.regras, args.hipoteses)
    print(f"{caminho} gerado ({caminho.stat().st_size:,} bytes; JSON do rastro {tamanho_json:,} bytes)".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
