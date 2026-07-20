#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LIVE_CATALOG = DATA / "catalog-live.json"
FALLBACK_CATALOG = DATA / "catalog-fallback.json"
sys.path.insert(0, str(ROOT / "scripts"))


class AppHandler(SimpleHTTPRequestHandler):
    server_version = "UWDegreeMapper/1.0"

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        clean = parsed.path.lstrip("/") or "index.html"
        candidate = (ROOT / clean).resolve()
        if ROOT not in candidate.parents and candidate != ROOT:
            return str(ROOT / "index.html")
        return str(candidate)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/catalog":
            self._send_catalog()
            return
        if parsed.path == "/api/status":
            self._send_json({
                "liveCatalog": LIVE_CATALOG.exists(),
                "catalogFile": LIVE_CATALOG.name if LIVE_CATALOG.exists() else FALLBACK_CATALOG.name,
            })
            return
        super().do_GET()

    def _send_catalog(self) -> None:
        path = LIVE_CATALOG if LIVE_CATALOG.exists() else FALLBACK_CATALOG
        try:
            content = path.read_bytes()
        except OSError as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def run_sync(campus: str) -> bool:
    try:
        from scrape_uw_catalog import sync_catalog
        campuses = None if campus == "all" else [campus]
        sync_catalog(LIVE_CATALOG, campuses=campuses)
        return True
    except Exception as exc:
        print(f"Could not sync the official catalog: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the UW Degree Mapper website")
    parser.add_argument("--port", type=int, default=5173)
    parser.add_argument("--sync", action="store_true", help="Refresh all official UW course descriptions before serving")
    parser.add_argument("--campus", choices=["all", "Seattle", "Bothell", "Tacoma"], default="all")
    parser.add_argument("--sync-only", action="store_true")
    args = parser.parse_args()

    if args.sync or args.sync_only:
        ok = run_sync(args.campus)
        if args.sync_only:
            return 0 if ok else 1
        if not ok:
            print("Starting with the bundled offline catalog instead.")

    os.chdir(ROOT)
    mimetypes.add_type("application/javascript", ".js")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), AppHandler)
    print("\nUW Degree Mapper is running.")
    print(f"Open: http://localhost:{args.port}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
