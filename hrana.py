"""Turso / libSQL için Hrana-over-HTTP istemcisi (yalnızca standart kütüphane + urllib3).

sqlite3 bağlantısının kullandığımız kısmını taklit eder: execute / executescript / close, satırlara ad ya da
sırayla erişim, lastrowid / rowcount. Vercel gibi dosya sistemi kalıcı olmayan ortamlarda veritabanı uzaktadır.

Her bağımsız komut tek bir HTTP isteğidir (akış açılır, çalışır, kapanır). BEGIN ile başlayan işlemlerde akış
COMMIT / ROLLBACK'e kadar açık tutulur (baton). Uzak bağlantı yeni akışta PRAGMA foreign_keys değerini
aynı istekte yeniden kurar.
"""
import base64
import json
import os
import sqlite3
import threading

import urllib3

_POOL = None
_POOL_LOCK = threading.Lock()


def _pool():
    global _POOL
    if _POOL is None:
        with _POOL_LOCK:
            if _POOL is None:
                _POOL = urllib3.PoolManager(
                    maxsize=8,
                    timeout=urllib3.Timeout(connect=6.0, read=30.0),
                    retries=urllib3.Retry(total=2, connect=2, read=0, status=0, backoff_factor=0.15, raise_on_status=False),
                )
    return _POOL


class HranaError(sqlite3.OperationalError):
    """Uzak veritabanı hatası (sqlite3.OperationalError alt sınıfı: mevcut except blokları çalışır)."""


class HranaIntegrityError(sqlite3.IntegrityError):
    """UNIQUE / FOREIGN KEY / NOT NULL / CHECK ihlali (sqlite3.IntegrityError alt sınıfı)."""


def _err(info):
    msg = (info or {}).get("message", "veritabanı hatası")
    code = (info or {}).get("code", "") or ""
    if code.startswith("SQLITE_CONSTRAINT") or "constraint failed" in msg.lower():
        return HranaIntegrityError(msg)
    return HranaError(msg)


class Row:
    """sqlite3.Row benzeri: row["ad"], row[0], row.keys(), dict(row), iter, len."""
    __slots__ = ("_v", "_k", "_i")

    def __init__(self, keys, values, index):
        self._k = keys
        self._v = values
        self._i = index

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._v[key]
        try:
            return self._v[self._i[key]]
        except KeyError:
            try:
                return self._v[self._i[str(key).lower()]]
            except KeyError:
                raise IndexError("No item with that key") from None

    def keys(self):
        return list(self._k)

    def __iter__(self):
        return iter(self._v)

    def __len__(self):
        return len(self._v)

    def __eq__(self, other):
        return isinstance(other, Row) and self._v == other._v and self._k == other._k

    def __hash__(self):
        return hash(tuple(self._v))

    def __repr__(self):
        return "<Row %r>" % (dict(zip(self._k, self._v)),)


def _enc(v):
    if v is None:
        return {"type": "null"}
    if isinstance(v, bool):
        return {"type": "integer", "value": str(int(v))}
    if isinstance(v, int):
        if not -(2 ** 63) <= v < 2 ** 63:
            raise OverflowError("Python int too large to convert to SQLite INTEGER")     # sqlite3 ile aynı davranış
        return {"type": "integer", "value": str(v)}
    if isinstance(v, float):
        return {"type": "float", "value": v}
    if isinstance(v, (bytes, bytearray, memoryview)):
        return {"type": "blob", "base64": base64.b64encode(bytes(v)).decode("ascii")}
    return {"type": "text", "value": str(v)}


def _dec(cell):
    t = cell.get("type")
    if t == "null":
        return None
    if t == "integer":
        return int(cell["value"])
    if t == "float":
        return float(cell["value"])
    if t == "blob":
        b = cell.get("base64", "")
        return base64.b64decode(b + "=" * (-len(b) % 4))
    return cell.get("value", "")


class Cursor:
    def __init__(self, cols=(), rows=(), rowcount=-1, lastrowid=None):
        self.description = tuple((c, None, None, None, None, None, None) for c in cols)
        self._rows = list(rows)
        self._pos = 0
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def fetchone(self):
        if self._pos >= len(self._rows):
            return None
        r = self._rows[self._pos]
        self._pos += 1
        return r

    def fetchall(self):
        out = self._rows[self._pos:]
        self._pos = len(self._rows)
        return out

    def __iter__(self):
        while True:
            r = self.fetchone()
            if r is None:
                return
            yield r

    def close(self):
        pass


class Connection:
    """Tek bir istek/iş parçacığı için bağlantı (Flask g.db ile aynı ömürde)."""

    def __init__(self, url, token):
        url = url.strip()
        if url.startswith("libsql://"):
            url = "https://" + url[len("libsql://"):]
        elif url.startswith("wss://"):
            url = "https://" + url[len("wss://"):]
        elif url.startswith("ws://"):
            url = "http://" + url[len("ws://"):]
        self.base = url.rstrip("/")
        self.token = token or ""
        self.baton = None
        self.stream_base = None
        self.in_tx = False
        self.fk = True
        self.total_requests = 0

    # ------------------------------------------------------------------ taşıma
    def _post(self, requests, retry_ok):
        body = json.dumps({"baton": self.baton, "requests": requests}, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        base = self.stream_base or self.base
        attempts = 2 if retry_ok else 1
        last = None
        for _ in range(attempts):
            try:
                resp = _pool().request("POST", base + "/v2/pipeline", body=body, headers=headers)
            except urllib3.exceptions.HTTPError as err:
                last = err
                continue
            self.total_requests += 1
            if resp.status == 401 or resp.status == 403:
                raise HranaError("Turso kimlik doğrulaması başarısız (TURSO_AUTH_TOKEN'ı kontrol et).")
            if resp.status >= 400:
                text = resp.data[:300].decode("utf-8", "replace")
                try:
                    text = json.loads(text).get("error", text)
                except Exception:
                    pass
                self.baton = None
                self.stream_base = None
                self.in_tx = False
                raise HranaError(f"Turso isteği reddedildi ({resp.status}): {text}")
            return json.loads(resp.data.decode("utf-8"))
        self.baton = None
        self.stream_base = None
        self.in_tx = False
        raise HranaError(f"Turso'ya ulaşılamadı: {last}")

    def _pipeline(self, requests, retry_ok=False):
        data = self._post(requests, retry_ok)
        self.baton = data.get("baton")
        if data.get("base_url"):
            self.stream_base = data["base_url"].rstrip("/")
        if not self.baton:
            self.stream_base = None
        return data.get("results", [])

    @staticmethod
    def _stmt(sql, args):
        if isinstance(args, dict):                      # :ad / @ad / $ad biçimli adlı parametreler
            named = [{"name": str(k).lstrip(":@$"), "value": _enc(v)} for k, v in args.items()]
            return {"type": "execute", "stmt": {"sql": sql, "named_args": named, "want_rows": True}}
        return {"type": "execute", "stmt": {"sql": sql, "args": [_enc(a) for a in args], "want_rows": True}}

    def _pragma_fk(self):
        return {"type": "execute", "stmt": {"sql": "PRAGMA foreign_keys = %s" % ("ON" if self.fk else "OFF"), "want_rows": False}}

    # ------------------------------------------------------------------ genel arayüz
    def execute(self, sql, args=()):
        head = sql.lstrip()[:16].upper()
        if head.startswith("PRAGMA FOREIGN_KEYS"):          # akışlar arası kalıcı olmadığı için bağlantıda tutulur
            if "=" in sql:
                self.fk = sql.split("=", 1)[1].strip().rstrip(";").upper() in ("ON", "1", "TRUE", "YES")
            return Cursor()
        if not isinstance(args, dict):
            args = tuple(args)
        reqs = []
        new_stream = self.baton is None
        if new_stream:
            reqs.append(self._pragma_fk())
        reqs.append(self._stmt(sql, args))
        starts_tx = head.startswith("BEGIN")
        ends_tx = head.startswith("COMMIT") or head.startswith("END") or head.startswith("ROLLBACK")
        keep_open = starts_tx or (self.in_tx and not ends_tx)
        if not keep_open:
            reqs.append({"type": "close"})
        retry_ok = (not self.in_tx) and head.startswith(("SELECT", "WITH", "PRAGMA"))
        results = self._pipeline(reqs, retry_ok)
        if starts_tx:
            self.in_tx = True
        elif ends_tx:
            self.in_tx = False
        off = 1 if new_stream else 0
        if len(results) <= off:
            raise HranaError("Turso'dan beklenmeyen yanıt.")
        res = results[off]
        if res.get("type") == "error":
            if not keep_open:
                self.baton = None
            raise _err(res.get("error"))
        out = res["response"]["result"]
        cols = [c.get("name") or "" for c in out.get("cols", [])]
        index = {}
        for n, c in enumerate(cols):
            index.setdefault(c, n)
            index.setdefault(c.lower(), n)
        rows = [Row(cols, [_dec(c) for c in raw], index) for raw in out.get("rows", [])]
        lid = out.get("last_insert_rowid")
        return Cursor(cols, rows, out.get("affected_row_count", -1), int(lid) if lid not in (None, "") else None)

    def executescript(self, script):
        reqs = []
        new_stream = self.baton is None
        if new_stream:
            reqs.append(self._pragma_fk())
        reqs.append({"type": "sequence", "sql": script})
        if not self.in_tx:
            reqs.append({"type": "close"})
        results = self._pipeline(reqs)
        off = 1 if new_stream else 0
        res = results[off] if len(results) > off else {"type": "error", "error": {"message": "yanıt yok"}}
        if res.get("type") == "error":
            if not self.in_tx:
                self.baton = None
            raise _err(res.get("error"))
        return Cursor()

    def commit(self):
        pass

    def rollback(self):
        if self.in_tx:
            self.execute("ROLLBACK")

    def close(self):
        if self.baton:
            try:
                self._pipeline([{"type": "close"}])
            except Exception:
                pass
        self.baton = None
        self.stream_base = None
        self.in_tx = False


def configured():
    return os.getenv("TURSO_DATABASE_URL", "").strip()


def connect():
    return Connection(os.environ["TURSO_DATABASE_URL"], os.getenv("TURSO_AUTH_TOKEN", ""))
