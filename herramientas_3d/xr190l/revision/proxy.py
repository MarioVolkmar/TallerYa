# Proxy local a localhost:8001 sin CSP + POST /__guardar/<nombre> que guarda un dataURL en caps/
import base64, os, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "caps")
SALTAR = {"content-security-policy", "content-length", "transfer-encoding", "connection", "content-encoding"}
class H(BaseHTTPRequestHandler):
    def _fwd(self, metodo, cuerpo=None):
        req = urllib.request.Request("http://localhost:8001" + self.path, data=cuerpo, method=metodo)
        for k, v in self.headers.items():
            if k.lower() not in ("host", "accept-encoding", "content-length", "connection"): req.add_header(k, v)
        req.add_header("Host", "localhost:8001")
        try: r = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e: r = e
        data = r.read()
        if "rayos=1" in self.path: data = data.replace(b'data-modo="moto"', b'data-modo="rayos"')
        self.send_response(r.status if hasattr(r, "status") else r.code)
        for k, v in r.headers.items():
            if k.lower() not in SALTAR: self.send_header(k, v.replace("localhost:8001", "localhost:8765"))
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path.startswith("/__js/"):
            data = open(os.path.join(os.path.dirname(D), os.path.basename(self.path.split("?")[0])), "rb").read()
            self.send_response(200); self.send_header("Content-Type", "application/javascript"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        self._fwd("GET")
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); cuerpo = self.rfile.read(n)
        if self.path.startswith("/__guardar/"):
            s = cuerpo.decode(); s = s.split(",", 1)[1] if "," in s else s
            open(os.path.join(D, os.path.basename(self.path)), "wb").write(base64.b64decode(s))
            self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok"); return
        self._fwd("POST", cuerpo)
    def log_message(self, *a): pass
ThreadingHTTPServer(("127.0.0.1", 8767), H).serve_forever()
