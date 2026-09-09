from __future__ import annotations

import argparse
import json
from pathlib import Path

from .intake import CompilableWorldIntakeError, emit_authoring


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="awa-cw-intake", description="Emit deterministic CompilableWorld Authoring Layer inputs")
    sub = parser.add_subparsers(dest="command", required=True)
    emit = sub.add_parser("emit")
    emit.add_argument("--semantic-snapshot", required=True)
    emit.add_argument("--composition-receipt", required=True)
    emit.add_argument("--asset-graph-snapshot", required=True)
    emit.add_argument("--plan", required=True)
    emit.add_argument("--out", required=True)
    emit.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt_path = emit_authoring(
            args.semantic_snapshot,
            args.composition_receipt,
            args.asset_graph_snapshot,
            args.plan,
            args.out,
            root=args.root,
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        print(json.dumps({"receipt": str(receipt_path), "world_id": receipt["world_id"], "authoring_sha256": receipt["authoring_sha256"]}, ensure_ascii=False, indent=2))
        return 0
    except (CompilableWorldIntakeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
