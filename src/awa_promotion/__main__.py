from __future__ import annotations

import argparse
from pathlib import Path

from awa_contracts.validator import load_json
from .promotion import PromotionEvaluator


def main() -> None:
    parser = argparse.ArgumentParser(prog="awa-promotion")
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--conflict-set", required=True)
    evaluate.add_argument("--policy", required=True)
    evaluate.add_argument("--out", required=True)
    authorize = sub.add_parser("authorize")
    authorize.add_argument("--readiness", required=True)
    authorize.add_argument("--grant", required=True)
    authorize.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path.cwd()
    evaluator = PromotionEvaluator(root=root)
    if args.command == "evaluate":
        evaluator.evaluate(conflict_set=load_json(Path(args.conflict_set)), policy=load_json(Path(args.policy)), out=args.out)
    else:
        evaluator.authorize(readiness=load_json(Path(args.readiness)), grant=load_json(Path(args.grant)), out=args.out)


if __name__ == "__main__":
    main()
