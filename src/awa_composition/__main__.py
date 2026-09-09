from __future__ import annotations

import argparse
import json
from pathlib import Path

from .resolver import (
    CompositionError,
    load_capability_registry,
    load_module_registry,
    load_world_profile,
    resolve_composition,
)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic CSC-OCM world profile resolver")
    parser.add_argument("profile", type=Path)
    parser.add_argument("--modules", type=Path, required=True, help="directory of module-manifest.v0.1 JSON files")
    parser.add_argument("--capabilities", type=Path, required=True, help="directory of capability-contract.v0.1 JSON files")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(arv)
    try:
        root = _root()
        profile = load_world_profile(args.profile, root=root)
        modules = load_module_registry(args.modules, root=root)
        capabilities = load_capability_registry(args.capabilities, root=root)
        receipt = resolve_composition(profile, modules, capabilities, root=root)
    except CompositionError as exc:
        parser.error(str(exc))
    encoded = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
