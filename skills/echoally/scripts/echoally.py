"""One-shot client for EchoAlly's stateless, JSON-response MCP endpoint."""

import argparse
import json
import os
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener


DEFAULT_ENDPOINT = "https://dev.ichunzhen.cn/mcp"
PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26")
MAX_RESPONSE = 8 * 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ClientError(Exception):
    pass


class Client:
    def __init__(self, endpoint, key):
        url = urlsplit(endpoint)
        if url.scheme != "https" or not url.hostname or url.username is not None or url.query or url.fragment:
            raise ClientError("Set ECHOALLY_MCP_URL to the HTTPS endpoint displayed in the App.")
        if not key or not key.isascii() or not key.isprintable() or any(char.isspace() for char in key):
            raise ClientError("Set ECHOALLY_API_KEY in the host's private environment.")
        self.endpoint = endpoint
        self.headers = {
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        tls = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None)
        self.opener = build_opener(NoRedirect(), HTTPSHandler(context=tls))

    def post(self, rpc_method, params=None, request_id=None):
        message = {"jsonrpc": "2.0", "method": rpc_method}
        if request_id is not None:
            message["id"] = request_id
        if params is not None:
            message["params"] = params
        request = Request(self.endpoint, data=json.dumps(message).encode(), headers=self.headers)
        with self.opener.open(request, timeout=30) as response:
            if request_id is None:
                return
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ClientError("Result exceeds the size limit. Narrow the request.")
            reply = json.loads(raw)
        if not isinstance(reply, dict) or reply.get("jsonrpc") != "2.0" or reply.get("id") != request_id:
            raise ClientError("Unexpected MCP response.")
        if "error" in reply:
            error = reply["error"]
            raise ClientError("MCP error {}: {}".format(error.get("code"), error.get("message")))
        if not isinstance(reply.get("result"), dict):
            raise ClientError("Missing MCP result.")
        return reply["result"]

    def connect(self):
        server = self.post("initialize", {
            "protocolVersion": PROTOCOL_VERSIONS[0],
            "capabilities": {},
            "clientInfo": {"name": "echoally-skill", "version": "0.1.0"},
        }, 1)
        version = server.get("protocolVersion")
        if version not in PROTOCOL_VERSIONS:
            raise ClientError("Server negotiated an unsupported MCP version.")
        self.headers["MCP-Protocol-Version"] = version
        self.post("notifications/initialized")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="action", required=True)
    commands.add_parser("list", help="Discover tools for this key.")
    call = commands.add_parser("call", help="Read tool arguments as one JSON object on stdin.")
    call.add_argument("tool")
    args = cli.parse_args()
    try:
        client = Client(os.environ.get("ECHOALLY_MCP_URL", DEFAULT_ENDPOINT),
                        os.environ.get("ECHOALLY_API_KEY", ""))
        params = None
        if args.action == "call":
            arguments = json.load(sys.stdin)
            if not isinstance(arguments, dict):
                raise ClientError("Tool arguments must be a JSON object.")
            params = {"name": args.tool, "arguments": arguments}
        client.connect()
        result = client.post("tools/call" if params else "tools/list", params, 2)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get("isError") else 0
    except HTTPError as exc:
        print("EchoAlly returned HTTP {}.".format(exc.code), file=sys.stderr)
    except (ValueError, URLError, OSError, ClientError) as exc:
        print(str(exc), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
