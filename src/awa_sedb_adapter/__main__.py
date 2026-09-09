from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .projection import export_entity, export_namespace
from .source import ReadOnlySedbSource


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only SEDB → AWA projection adapter")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="verify the required SEDB read schema")
    check.add_argument("database")

    entity = sub.add_parser("entity", help="export one semantic-game-entity.v0.1 projection")
    entity.add_argument("database")
    entity.add_argument("entity_id")
    entity.add_argument("--namespace", default="global")
    entity.add_argument("-o", "--output")

    namespace = sub.add_parser("namespace", help="export a deterministic namespace snapshot")
    namespace.add_argument("database")
    namespace.add_argument("namespace")
    namespace.add_argument("-o", "--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = ReadOnlySedbSource(args.database)
    if args.command == "check":
        with source.snapshot():
            pass
        print("SEDB read schema: compatible")
        return 0
    if args.command == "entity":
        _write(
            export_entity(source, args.entity_id, namespace=args.namespace),
            args.output,
        )
        return 0
    _write(export_namespace(source, args.namespace), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
