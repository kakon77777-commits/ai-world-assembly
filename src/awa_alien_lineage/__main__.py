from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build import AlienLineageBuildError, emit_runtime_authoring, emit_spawn_runtime_authoring


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="awa-alien-lineage", description="Build and verify the bounded Alien Lineage Runtime slice")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--semantic-snapshot", required=True)
    build.add_argument("--composition-receipt", required=True)
    build.add_argument("--asset-graph-snapshot", required=True)
    build.add_argument("--plan", required=True)
    build.add_argument("--slice", required=True)
    build.add_argument("--out", required=True)
    build.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    spawn_build = sub.add_parser("spawn-build")
    spawn_build.add_argument("--semantic-snapshot", required=True)
    spawn_build.add_argument("--composition-receipt", required=True)
    spawn_build.add_argument("--asset-graph-snapshot", required=True)
    spawn_build.add_argument("--plan", required=True)
    spawn_build.add_argument("--slice", required=True)
    spawn_build.add_argument("--spawn-profile", required=True)
    spawn_build.add_argument("--out", required=True)
    spawn_build.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    scenario = sub.add_parser("scenario-run")
    scenario.add_argument("package")
    scenario.add_argument("scenario_id")
    scenario.add_argument("--actor", default=None)
    scenario.add_argument("--assertions", default=None, help="Optional AWA domain-state assertion sidecar")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            receipt_path = emit_runtime_authoring(
                args.semantic_snapshot,
                args.composition_receipt,
                args.asset_graph_snapshot,
                args.plan,
                args.slice,
                args.out,
                root=args.root,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            print(json.dumps({"receipt": str(receipt_path), "authoring_sha256": receipt["authoring_sha256"], "runtime_module": receipt["runtime_module"]}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "spawn-build":
            receipt_path = emit_spawn_runtime_authoring(
                args.semantic_snapshot, args.composition_receipt, args.asset_graph_snapshot,
                args.plan, args.slice, args.spawn_profile, args.out, root=args.root,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            print(json.dumps({"receipt": str(receipt_path), "authoring_sha256": receipt["authoring_sha256"], "runtime_modules": receipt["runtime_modules"], "compatibility_commit": receipt["compatibility_commit"]}, ensure_ascii=False, indent=2))
            return 0
        from .scenario import run_alien_lineage_scenario
        package = json.loads(Path(args.package).read_text(encoding="utf-8"))
        assertions = None
        if args.assertions:
            assertions = json.loads(Path(args.assertions).read_text(encoding="utf-8"))
        report = run_alien_lineage_scenario(package, args.scenario_id, actor_id=args.actor, domain_assertions=assertions)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 1
    except (AlienLineageBuildError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
