"""Serve only frozen demo files on loopback, with byte ranges for video seeking."""
from __future__ import annotations

import argparse
import functools
import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, allowed: frozenset[str], **kwargs):
        self.demo_root = Path(directory).resolve()
        self.allowed = allowed
        self.remaining = None
        super().__init__(*args, directory=directory, **kwargs)

    def send_head(self):
        self.remaining = None
        target = Path(self.translate_path(self.path))
        if target.is_dir():
            target = target / "index.html"
        target = target.resolve()
        if (not target.is_relative_to(self.demo_root) or not target.is_file()
                or target.relative_to(self.demo_root).as_posix() not in self.allowed):
            self.send_error(HTTPStatus.NOT_FOUND)
            return None
        size = target.stat().st_size
        header = self.headers.get("Range")
        start, end = 0, size - 1
        if header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", header)
            valid = match is not None and bool(match[1] or match[2]) and size > 0
            if valid:
                if match[1]:
                    start = int(match[1])
                    end = min(int(match[2]), size - 1) if match[2] else size - 1
                else:
                    suffix = int(match[2])
                    valid = suffix > 0
                    start = max(0, size - suffix)
                valid = valid and 0 <= start <= end < size
            if not valid:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
        stream = target.open("rb")
        stream.seek(start)
        self.remaining = max(0, end - start + 1)
        self.send_response(HTTPStatus.PARTIAL_CONTENT if header else HTTPStatus.OK)
        self.send_header("Content-Type", self.guess_type(str(target)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(self.remaining))
        if header:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        return stream

    def copyfile(self, source, outputfile):
        remaining = self.remaining
        while remaining:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="在本機預覽固定示範，支援影片時間軸跳轉")
    parser.add_argument("--port", type=int, default=3023)
    parser.add_argument("--directory", type=Path,
                        default=Path(__file__).resolve().parents[1] / "examples/azhong-mmeng-1202")
    args = parser.parse_args()
    directory = args.directory.resolve(strict=True)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    allowed = frozenset(["manifest.json"] + [entry["path"] for entry in manifest["files"]])
    handler = functools.partial(DemoHandler, directory=str(directory), allowed=allowed)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
