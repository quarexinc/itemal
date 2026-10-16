"""Yerel test için Turso/libSQL taklidi: Hrana-over-HTTP (/v2/pipeline) konuşur, arkada SQLite dosyası kullanır.

  python tools/fake_turso.py --db /tmp/t.db --port 8765 [--token gizli]

Uygulamayı Vercel'e göndermeden önce uzak-veritabanı yolunu denemek içindir:
  TURSO_DATABASE_URL=http://127.0.0.1:8765  TURSO_AUTH_TOKEN=gizli  python app.py
"""
import argparse
import base64
import json
import secrets
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STREAMS = {}
LOCK = threading.Lock()
STATS = {"pipelines": 0, "statements": 0}


def enc(v):
    if v is None:
        return {"type": "null"}
    if isinstance(v, int):
        return {"type": "integer", "value": str(v)}
    if isinstance(v, float):
        return {"type": "float", "value": v}
    if isinstance(v, (bytes, bytearray)):
        return {"type": "blob", "base64": base64.b64encode(bytes(v)).decode()}
    return {"type": "text", "value": v}


def dec(a):
    t = a["type"]
    if t == "null":
        return None
    if t == "integer":
        return int(a["value"])
    if t == "float":
        return float(a["value"])
    if t == "blob":
        return base64.b64decode(a["base64"] + "=" * (-len(a["base64"]) % 4))
    return a["value"]


def make_handler(db_path, token):
    def new_conn():
        c = sqlite3.connect(db_path, isolation_level=None, timeout=15, check_same_thread=False)
        c.execute("PRAGMA journal_mode = WAL")
        return c

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/stats":
                return self._send(200, STATS)
            self._send(404, {"error": "yok"})

        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(n)
            if token and self.headers.get("Authorization") != "Bearer " + token:
                return self._send(401, {"error": "Unauthorized"})
            if self.path != "/v2/pipeline":
                return self._send(404, {"error": "yok"})
            req = json.loads(raw)
            baton = req.get("baton")
            if baton:
                with LOCK:
                    conn = STREAMS.get(baton)
                if conn is None:
                    return self._send(400, {"error": "stream expired"})
            else:
                conn = new_conn()
            results, closed = [], False
            STATS["pipelines"] += 1
            for r in req["requests"]:
                t = r["type"]
                if t == "close":
                    closed = True
                    results.append({"type": "ok", "response": {"type": "close"}})
                elif t in ("execute", "sequence"):
                    try:
                        if t == "sequence":
                            conn.executescript(r["sql"])
                            results.append({"type": "ok", "response": {"type": "sequence"}})
                            continue
                        st = r["stmt"]
                        STATS["statements"] += 1
                        if st.get("named_args"):
                            params = {a["name"].lstrip(":@$"): dec(a["value"]) for a in st["named_args"]}
                        else:
                            params = [dec(a) for a in st.get("args", [])]
                        cur = conn.execute(st["sql"], params)
                        cols = [{"name": d[0], "decltype": None} for d in (cur.description or [])]
                        rows = [[enc(v) for v in row] for row in cur.fetchall()] if st.get("want_rows", True) else []
                        results.append({"type": "ok", "response": {"type": "execute", "result": {
                            "cols": cols, "rows": rows, "affected_row_count": max(cur.rowcount, 0),
                            "last_insert_rowid": str(cur.lastrowid) if cur.lastrowid else None}}})
                    except sqlite3.IntegrityError as e:
                        results.append({"type": "error", "error": {"message": str(e), "code": "SQLITE_CONSTRAINT"}})
                    except sqlite3.Error as e:
                        results.append({"type": "error", "error": {"message": str(e), "code": "SQLITE_ERROR"}})
                else:
                    results.append({"type": "error", "error": {"message": "desteklenmiyor: " + t}})
            if closed:
                try:
                    conn.close()
                finally:
                    with LOCK:
                        STREAMS.pop(baton, None)
                out_baton = None
            else:
                out_baton = baton or secrets.token_hex(16)
                with LOCK:
                    STREAMS[out_baton] = conn
            self._send(200, {"baton": out_baton, "base_url": None, "results": results})

    return H


def serve(db, port, token=""):
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(db, token))
    srv.daemon_threads = True
    return srv


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default="")
    a = ap.parse_args()
    print(f"fake turso: http://127.0.0.1:{a.port}  db={a.db}", flush=True)
    serve(a.db, a.port, a.token).serve_forever()
