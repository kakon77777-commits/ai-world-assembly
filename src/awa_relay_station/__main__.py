from __future__ import annotations
import argparse,json
from pathlib import Path
from .build import emit_runtime_authoring
from .scenario import run_relay_station_scenario


def main() -> None:
    p=argparse.ArgumentParser(prog="awa-relay-station"); sub=p.add_subparsers(dest="cmd",required=True)
    b=sub.add_parser("build");
    for name in ["semantic-snapshot","composition-receipt","asset-graph-snapshot","intake-plan","runtime-slice"]: b.add_argument(f"--{name}",required=True)
    b.add_argument("--out",required=True); b.add_argument("--root",default=str(Path(__file__).resolve().parents[2]))
    r=sub.add_parser("scenario-run"); r.add_argument("package"); r.add_argument("scenario_id"); r.add_argument("--assertions");
    args=p.parse_args()
    if args.cmd=="build":
        path=emit_runtime_authoring(args.semantic_snapshot,args.composition_receipt,args.asset_graph_snapshot,args.intake_plan,args.runtime_slice,args.out,root=args.root); print(path)
    else:
        package=json.loads(Path(args.package).read_text()); assertions=json.loads(Path(args.assertions).read_text()) if args.assertions else None; result=run_relay_station_scenario(package,args.scenario_id,domain_assertions=assertions); print(json.dumps(result,ensure_ascii=False,indent=2)); raise SystemExit(0 if result["passed"] else 1)

if __name__=="__main__": main()
