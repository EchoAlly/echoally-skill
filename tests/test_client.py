"""Exercise the installed skill runner over a private HTTPS loopback endpoint."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/echoally/scripts/echoally.py"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        rpc = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.messages.append((rpc, dict(self.headers)))
        if self.path == "/redirect":
            self.send_response(307)
            self.send_header("Location", self.server.endpoint)
            self.end_headers()
            return
        if rpc["method"] == "notifications/initialized":
            self.send_response(202)
            self.end_headers()
            return
        answers = {
            "initialize": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}},
            "tools/list": {"tools": [{"name": "list_records"}]},
            "tools/call": {"content": [{"type": "text", "text": "Saved"}]},
        }
        result = answers[rpc["method"]]
        if rpc["method"] == "tools/call" and rpc["params"]["name"] == "unknown":
            result = {"isError": True, "content": [{"type": "text", "text": "Unknown tool"}]}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"jsonrpc": "2.0", "id": rpc["id"], "result": result}).encode())


class ClientIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        root = Path(cls.temp.name)
        cls.ca = root / "cert.pem"
        key = root / "key.pem"
        conf = root / "openssl.cnf"
        conf.write_text("[req]\ndistinguished_name=dn\nprompt=no\nx509_extensions=v3\n"
                        "[dn]\nCN=localhost\n[v3]\nsubjectAltName=IP:127.0.0.1\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,digitalSignature\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid:always\n")
        subprocess.run(["openssl", "req", "-config", str(conf), "-x509", "-nodes",
                        "-newkey", "rsa:2048", "-days", "1", "-keyout", str(key), "-out", str(cls.ca)],
                       check=True, capture_output=True)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cls.ca, key)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
        server.endpoint = "https://127.0.0.1:{}/mcp".format(server.server_port)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        cls.server = server
        cls.addClassCleanup(server.server_close)
        cls.addClassCleanup(server.shutdown)

    def setUp(self):
        self.server.messages = []

    def invoke(self, *args, stdin="", key="dummy-key", endpoint=None):
        env = dict(os.environ, SSL_CERT_FILE=str(self.ca), ECHOALLY_API_KEY=key,
                   ECHOALLY_MCP_URL=endpoint or self.server.endpoint, NO_PROXY="127.0.0.1",
                   no_proxy="127.0.0.1")
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, env=env,
                              capture_output=True, text=True, timeout=5)

    def test_handshake_and_discovery(self):
        run = self.invoke("list")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["tools"][0]["name"], "list_records")
        messages = self.server.messages
        self.assertEqual([rpc["method"] for rpc, _ in messages],
                         ["initialize", "notifications/initialized", "tools/list"])
        for _, headers in messages:
            self.assertEqual(headers["Authorization"], "Bearer dummy-key")
        self.assertEqual(messages[-1][1]["Mcp-Protocol-Version"], "2025-06-18")
        self.assertNotIn("dummy-key", run.stdout + run.stderr)

    def test_create_passes_idempotency_key_and_literal_text(self):
        args = {"title": "摘要", "content_md": "first\nsecond $PATH",
                "client_request_id": "0095bde2-956c-43d8-bdd8-31c5555a06ad"}
        run = self.invoke("call", "save_memo", stdin=json.dumps(args))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.server.messages[-1][0]["params"], {"name": "save_memo", "arguments": args})

    def test_not_success_on_tool_error(self):
        run = self.invoke("call", "unknown", stdin="{}")
        self.assertNotEqual(run.returncode, 0)
        self.assertTrue(json.loads(run.stdout)["isError"])

    def test_refuses_redirect_with_key(self):
        run = self.invoke("list", endpoint=self.server.endpoint.replace("/mcp", "/redirect"))
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(len(self.server.messages), 1)
        self.assertNotIn("dummy-key", run.stderr)

    def test_refuses_http_missing_key_and_invalid_arguments_before_connecting(self):
        for run in (
            self.invoke("list", endpoint=self.server.endpoint.replace("https:", "http:")),
            self.invoke("list", key=""),
            self.invoke("call", "create_todo", stdin="[]"),
        ):
            self.assertNotEqual(run.returncode, 0)
        self.assertEqual(self.server.messages, [])


if __name__ == "__main__":
    unittest.main()
