from __future__ import annotations
import argparse,json
from .assets import PresentationAssetError,verify_presentation_assets
from .bridge import PresentationBridgeError
from .server import serve

def parser():
    root=argparse.ArgumentParser(prog="awa-threejs"); sub=root.add_subparsers(dest="command",required=True); s=sub.add_parser("serve"); s.add_argument("package"); s.add_argument("--binding",required=True); s.add_argument("--static-dir",required=True); s.add_argument("--actor"); s.add_argument("--host",default="127.0.0.1"); s.add_argument("--port",type=int,default=8767); v=sub.add_parser("verify-assets"); v.add_argument("dist_dir"); return root

def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.command=="serve": serve(args.package,args.binding,args.static_dir,actor_id=args.actor,host=args.host,port=args.port); return 0
        print(json.dumps(verify_presentation_assets(args.dist_dir),ensure_ascii=False,indent=2)); return 0
    except (PresentationBridgeError,PresentationAssetError,OSError,ValueError) as exc: print(f"ERROR: {exc}"); return 1
if __name__=="__main__": raise SystemExit(main())
