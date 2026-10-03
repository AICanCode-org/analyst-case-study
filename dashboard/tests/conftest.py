import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GOLDEN = REPO / "contract" / "golden" / "answers-2026-06.json"


@pytest.fixture
def answers():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture
def fake_llm():
    """A local OpenAI-compatible /chat/completions that answers with `server.reply` (no network, no key)."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            server.requests.append(
                {"body": json.loads(self.rfile.read(length)), "auth": self.headers.get("Authorization")}
            )
            if server.status != 200:
                self.send_response(server.status)
                self.end_headers()
                return
            payload = (
                server.raw
                if server.raw is not None
                else json.dumps({"choices": [{"message": {"role": "assistant", "content": server.reply}}]})
            )
            data = payload.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.reply, server.raw, server.status, server.requests = "", None, 200, []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server.url = f"http://127.0.0.1:{server.server_address[1]}/v1"
    yield server
    server.shutdown()
    server.server_close()
