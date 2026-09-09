from __future__ import annotations

import argparse
import json
from pathlib import Path

from awa_contracts.validator import load_json

from .loop import BoundedAssembler
from .provider import reference_producer_for


def main() -> None:
    parser = argparse.ArgumentParser(prog="awa-assembler")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one bounded candidate generation/repair loop")
    run.add_argument("--task", required=True)
    run.add_argument("--project-state", default="PROJECT_STATE.json")
    run.add_argument("--semantic-snapshot", required=True)
    run.add_argument("--composition-receipt", required=True)
    run.add_argument("--presentation-binding", required=True)
    run.add_argument("--capability-contract", required=True)
    run.add_argument("--nodes", required=True)
    run.add_argument("--edges", required=True)
    run.add_argument("--artifacts", required=True)
    run.add_argument("--validations", required=True)
    run.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    task = load_json(args.task)
    assembler = BoundedAssembler(root=root, producer=reference_producer_for(task))
    receipt = assembler.run(
        task=task,
        project_state=args.project_state,
        semantic_snapshot=args.semantic_snapshot,
        composition_receipt=args.composition_receipt,
        presentation_binding=args.presentation_binding,
        capability_contract=args.capability_contract,
        nodes=args.nodes,
        edges=args.edges,
        artifacts=args.artifacts,
        validations=args.validations,
        out=args.out,
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
