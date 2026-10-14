"""Dual-Transport (StreamableHTTP & SSE + Stdio) HTTP Server for SEI MCP Server."""

from __future__ import annotations

import argparse
import json
import logging
import queue
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from src.auth import check_mcp_oauth
from src.config import SeiConfig, get_sei_config
from src.mcp_server import McpServer, create_mcp_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sei-mcp-server")


class SseSessionRegistry:
    """Thread-safe registry of active Server-Sent Events (SSE) sessions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: Dict[str, "queue.Queue[Optional[str]]"] = {}

    def create_session(self) -> Tuple[str, "queue.Queue[Optional[str]]"]:
        session_id = str(uuid.uuid4())
        q: "queue.Queue[Optional[str]]" = queue.Queue()
        with self._lock:
            self._sessions[session_id] = q
        return session_id, q

    def get_session(self, session_id: str) -> Optional["queue.Queue[Optional[str]]"]:
        with self._lock:
            return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        with self._lock:
            q = self._sessions.pop(session_id, None)
        if q is not None:
            q.put(None)


sse_registry = SseSessionRegistry()


def build_health_payload(config: SeiConfig) -> Dict[str, Any]:
    """Builds the JSON payload for GET /health."""
    return {
        "status": "healthy",
        "service": "sei-mcp-server",
        "protocol": "Model Context Protocol",
        "transports": ["StreamableHTTP (/mcp)", "SSE (/sse)"],
        "environment": config.environment,
    }


def build_oauth_protected_resource_payload(config: SeiConfig) -> Dict[str, Any]:
    """Builds the JSON payload for GET /.well-known/oauth-protected-resource."""
    return {
        "resource": config.oauth_protected_resource,
        "authorization_servers": [config.oauth_authorization_server],
        "scopes_supported": ["openid", "email", "profile"],
        "bearer_methods_supported": ["header"],
    }


def build_oauth_authorization_server_payload() -> Dict[str, Any]:
    """Builds the JSON payload for GET /.well-known/oauth-authorization-server."""
    return {
        "issuer": "https://accounts.google.com",
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "scopes_supported": ["openid", "email", "profile"],
        "response_types_supported": ["code"],
    }


class SeiMcpHttpRequestHandler(BaseHTTPRequestHandler):
    """HTTP/1.1 Request Handler supporting StreamableHTTP (/mcp), SSE (/sse + /messages), and OAuth."""

    protocol_version = "HTTP/1.1"
    mcp_server: McpServer = create_mcp_server()

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, Accept, Mcp-Session-Id",
        )

    def _send_json(self, status_code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def _drain_body(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length > 0:
            self.rfile.read(content_length)

    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return None
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode("utf-8"))

    def _headers_dict(self) -> Dict[str, str]:
        return {k: v for k, v in self.headers.items()}

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        cfg = get_sei_config()

        if path == "/health":
            self._send_json(200, build_health_payload(cfg))
            return

        if path == "/.well-known/oauth-protected-resource":
            self._send_json(200, build_oauth_protected_resource_payload(cfg))
            return

        if path == "/.well-known/oauth-authorization-server":
            self._send_json(200, build_oauth_authorization_server_payload())
            return

        if path == "/mcp":
            self._send_json(
                405,
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Method not allowed. Use POST for StreamableHTTP MCP requests.",
                    },
                    "id": None,
                },
            )
            return

        if path == "/sse":
            self._handle_sse_stream()
            return

        self._send_json(404, {"error": f"Not Found: {path}"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        cfg = get_sei_config()

        if path == "/mcp":
            self._handle_streamable_http(cfg)
            return

        if path == "/messages":
            self._handle_sse_post_message(parsed.query, cfg)
            return

        self._drain_body()
        self._send_json(404, {"error": f"Not Found: {path}"})

    def _handle_streamable_http(self, cfg: SeiConfig) -> None:
        # Validate Accept header per MCP StreamableHTTP specification
        accept_header = (self.headers.get("Accept") or "").lower()
        if "text/event-stream" not in accept_header:
            self._drain_body()
            self._send_json(
                406,
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": (
                            "Not Acceptable: Client must accept both "
                            "application/json and text/event-stream."
                        ),
                    },
                    "id": None,
                },
            )
            return

        try:
            body = self._read_json_body()
        except Exception as exc:
            self._send_json(
                400,
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {exc}"},
                    "id": None,
                },
            )
            return

        auth_check = check_mcp_oauth(self._headers_dict(), body, cfg)
        if not auth_check.allowed:
            self._send_json(auth_check.status_code, auth_check.error_payload)
            return

        response_payload = self.mcp_server.handle_jsonrpc(body or {})
        if response_payload is None:
            # JSON-RPC Notification (e.g. notifications/initialized)
            self.send_response(202)
            self._send_cors_headers()
            self.send_header("Content-Length", "0")
            self.end_headers()
            self.wfile.flush()
            return

        self._send_json(200, response_payload)

    def _handle_sse_stream(self) -> None:
        session_id, q = sse_registry.create_session()
        logger.info("Opened SSE session: %s", session_id)

        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            endpoint_event = f"event: endpoint\ndata: /messages?sessionId={session_id}\n\n"
            self.wfile.write(endpoint_event.encode("utf-8"))
            self.wfile.flush()

            while True:
                try:
                    msg = q.get(timeout=15.0)
                    if msg is None:
                        break
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # Send SSE comment keepalive to detect broken connections
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            sse_registry.remove_session(session_id)
            logger.info("Closed SSE session: %s", session_id)

    def _handle_sse_post_message(self, query_string: str, cfg: SeiConfig) -> None:
        qs = parse_qs(query_string)
        session_ids = qs.get("sessionId")
        if not session_ids or not session_ids[0].strip():
            self._drain_body()
            self._send_json(
                400,
                {"error": "Bad Request: Missing 'sessionId' query parameter"},
            )
            return

        session_id = session_ids[0].strip()
        q = sse_registry.get_session(session_id)
        if q is None:
            self._drain_body()
            self._send_json(
                404,
                {"error": f"Session not found or expired: {session_id}"},
            )
            return

        try:
            body = self._read_json_body()
        except Exception as exc:
            self._send_json(
                400,
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {exc}"},
                    "id": None,
                },
            )
            return

        auth_check = check_mcp_oauth(self._headers_dict(), body, cfg)
        if not auth_check.allowed:
            self._send_json(auth_check.status_code, auth_check.error_payload)
            return

        response_payload = self.mcp_server.handle_jsonrpc(body or {})
        if response_payload is not None:
            event_data = f"event: message\ndata: {json.dumps(response_payload, ensure_ascii=False)}\n\n"
            q.put(event_data)

        self._send_json(202, {"status": "Accepted"})


def run_stdio_server() -> None:
    """Runs the MCP server over standard input/output (stdio transport)."""
    mcp_server = create_mcp_server()
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            payload = json.loads(line_str)
            resp = mcp_server.handle_jsonrpc(payload)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            err_resp = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
                "id": None,
            }
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def run_http_server(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Starts the multi-threaded HTTP/SSE MCP server."""
    cfg = get_sei_config()
    bind_host = host or cfg.host
    bind_port = port or cfg.port

    SeiMcpHttpRequestHandler.mcp_server = create_mcp_server()
    httpd = ThreadingHTTPServer((bind_host, bind_port), SeiMcpHttpRequestHandler)
    httpd.daemon_threads = True

    print("\n==================================================")
    print(f"🚀 SEI MCP Server (Python) running on port {bind_port}")
    print(f"🌐 StreamableHTTP Endpoint: http://{bind_host}:{bind_port}/mcp")
    print(f"📡 SSE Endpoint: http://{bind_host}:{bind_port}/sse")
    print(f"🏥 Health Check: http://{bind_host}:{bind_port}/health")
    print(f"🔧 Registered SEI/SIP Tools: {len(SeiMcpHttpRequestHandler.mcp_server.tools)}")
    print("==================================================\n", flush=True)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down SEI MCP Server...")
        httpd.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="SEI MCP Server for Gemini Enterprise")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run MCP server over stdio transport instead of HTTP/SSE",
    )
    parser.add_argument("--host", type=str, default=None, help="HTTP bind host")
    parser.add_argument("--port", type=int, default=None, help="HTTP bind port")
    args = parser.parse_args()

    if args.stdio:
        run_stdio_server()
    else:
        run_http_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
