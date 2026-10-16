"""CLI: `python -m tarvo --dados data --saida saida`.

E0: só valida as pastas e lista os arquivos encontrados. O fechamento em si entra
nas próximas etapas (docs/PLANO.md, seção 9).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tarvo",
        description=(
            "Fechamento mensal da Tarvo: lê o data pack como chega e gera os CSVs de saída."
        ),
    )
    parser.add_argument("--dados", type=Path, default=Path("data"), help="pasta do data pack (padrão: data)")
    parser.add_argument("--saida", type=Path, default=Path("saida"), help="pasta dos CSVs gerados (padrão: saida)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = criar_parser().parse_args(argv)

    if not args.dados.is_dir():
        print(f"erro: pasta de dados não encontrada: {args.dados}", file=sys.stderr)
        return 2
    if args.saida.exists() and not args.saida.is_dir():
        print(f"erro: --saida não é uma pasta: {args.saida}", file=sys.stderr)
        return 2
    args.saida.mkdir(parents=True, exist_ok=True)

    arquivos = sorted(p for p in args.dados.iterdir() if p.is_file())
    print(f"dados: {args.dados} ({len(arquivos)} arquivos)")
    for p in arquivos:
        print(f"  {p.name}  ({p.stat().st_size} bytes)")
    print(f"saida: {args.saida}")
    print("E0: estrutura pronta; cálculos ainda não implementados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
