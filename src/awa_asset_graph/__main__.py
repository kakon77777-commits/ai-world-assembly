from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .graph import AssetGraph, AssetGraphError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze an AWA Dynamic Asset Graph")
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--edges", required=True)
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--validations", required=True)
    parser.add_argument("--root-dir", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="validate graph registries and structural contracts")
    check.set_defaults(command="check")

    snapshot = sub.add_parser("snapshot", help="emit deterministic required closure snapshot")
    snapshot.add_argument("roots", nargs="+")
    snapshot.add_argument("-o", "--output")
    snapshot.add_argument("--tasks-output")
    return parser


def _write_or_print(payload: object, output: str | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output:
        Path(output).write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        graph = AssetGraph.from_directories(
            nodes=args.nodes,
            edges=args.edges,
            artifacts=args.artifacts,
            validations=args.validations,
            root=args.root_dir,
        )
        if args.command == "check":
            print("OK")
            return 0
        analysis = graph.analyze(args.roots)
        _write_or_print(analysis.snapshot, args.output)
        if args.tasks_output:
            _write_or_print(analysis.generation_tasks, args.tasks_output)
        return 0
    except AssetGraphError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
