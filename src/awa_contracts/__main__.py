from __future__ import annotations

import argparse
import sys

from .validator import ContractValidationError, validate_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="awa-contracts")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate one JSON document against one contract schema")
    validate.add_argument("schema")
    validate.add_argument("document")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        try:
            validate_files(args.schema, args.document)
        except ContractValidationError as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            return 1
        print("VALID")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
