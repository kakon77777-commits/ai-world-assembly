from __future__ import annotations
import json,mimetypes
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from .bridge import PresentationBridge,PresentationBridgeError,StalePresentationBinding

class PresentationHTTPServer(ThreadingHTTPServer):
    def __init__(self,address,bridge:PresentationBridge,static_dir:str|Path): super().__init__(address,PresentationRequestHandler); self.bridge=bridge; self.static_dir=Path(static_dir).resolve()
class PresentationRequestHandler(BaseHTTPRequestHandler):
    server:PresentationHTTPServer
    def log_message(self,format,*args): return
    def _json(self,status,payload):
        body=json.dumps(payload,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode(); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(body)
    def _read(self):
        try: size=int(self.headers.get("Content-Length","0"))
        except ValueError as exc: raise PresentationBridgeError("invalid Content-Length") from exc
        if size<1 or size>65536: raise PresentationBridgeError("JSON request body size is invalid")
        try: return json.loads(self.rfile.read(size).decode())
        except (UnicodeDecodeError,json.JSONDecodeError) as exc: raise PresentationBridgeError("request body is not valid UTF-8 JSON") from exc
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/projection": return self._json(200,self.server.bridge.projection())
        if path=="/health": return self._json(200,{"ok":True,"generation":self.server.bridge.generation})
        self._static(path)
    def do_POST(self):
        path=urlparse(self.path).path
        try:
            if path=="/api/reload": return self._json(200,self.server.bridge.reload())
            if path=="/api/action": return self._json(200,self.server.bridge.submit_intent(self._read()))
            return self._json(404,{"error":"not_found"})
        except StalePresentationBinding as exc: self._json(409,{"error":"stale_binding","message":str(exc),"projection":self.server.bridge.projection()})
        except PresentationBridgeError as exc: self._json(400,{"error":"invalid_request","message":str(exc)})
    def _static(self,path):
        rel="index.html" if path in {"","/"} else path.lstrip("/"); candidate=(self.server.static_dir/rel).resolve()
        try: candidate.relative_to(self.server.static_dir)
        except ValueError: return self.send_error(403)
        if not candidate.is_file(): candidate=self.server.static_dir/"index.html"
        if not candidate.is_file(): return self.send_error(404)
        body=candidate.read_bytes(); self.send_response(200); self.send_header("Content-Type",mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)

def build_bridge(package_path,binding_path,actor_id=None):
    from compilableworld.entity_transaction import EntityTransactionRuntime
    from awa_alien_lineage.runtime import install_alien_lineage_runtime
    package=json.loads(Path(package_path).read_text(encoding="utf-8")); binding=json.loads(Path(binding_path).read_text(encoding="utf-8")); runtime=EntityTransactionRuntime(package); install_alien_lineage_runtime(runtime); actor=actor_id or package.get("world",{}).get("default_player_entity")
    if not isinstance(actor,str) or not actor: raise PresentationBridgeError("presentation actor is required")
    return PresentationBridge(runtime,actor,binding)
def serve(package_path,binding_path,static_dir,*,actor_id=None,host="127.0.0.1",port=8767):
    server=PresentationHTTPServer((host,port),build_bridge(package_path,binding_path,actor_id),static_dir)
    try: server.serve_forever()
    finally: server.server_close()
