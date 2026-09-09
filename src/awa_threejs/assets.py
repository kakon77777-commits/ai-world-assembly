from __future__ import annotations
import hashlib, json
from pathlib import Path

class PresentationAssetError(ValueError): pass

def sha256_file(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""): digest.update(chunk)
    return digest.hexdigest()

def verify_presentation_assets(dist_dir: str|Path) -> dict:
    root=Path(dist_dir)
    try: manifest=json.loads((root/"presentation-assets.json").read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise PresentationAssetError("presentation-assets.json is missing or invalid") from exc
    if manifest.get("target")!="threejs" or manifest.get("three_version")!="0.180.0": raise PresentationAssetError("unexpected Three.js target/version")
    artifacts=manifest.get("artifacts")
    if not isinstance(artifacts,list) or not artifacts: raise PresentationAssetError("presentation artifact closure is empty")
    seen=set()
    for item in artifacts:
        if not isinstance(item,dict) or set(item)!={"path","sha256"}: raise PresentationAssetError("presentation artifact record is invalid")
        path=item["path"]
        if path in seen: raise PresentationAssetError("duplicate presentation artifact path")
        seen.add(path); target=(root/path).resolve()
        try: target.relative_to(root.resolve())
        except ValueError as exc: raise PresentationAssetError("presentation artifact path escapes dist root") from exc
        if not target.is_file() or sha256_file(target)!=item["sha256"]: raise PresentationAssetError(f"presentation artifact hash mismatch: {path}")
    return manifest
