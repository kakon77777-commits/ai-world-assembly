from __future__ import annotations

import argparse
import json
from pathlib import Path

from awa_contracts.validator import load_json

from .orchestrator import MultiWorldOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(prog="awa-orchestrate")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one reviewed multi-world orchestration plan")
    run.add_argument("--plan", required=True)
    run.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    receipt = MultiWorldOrchestrator(root=root).run(plan=load_json(args.plan), out=args.out)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
