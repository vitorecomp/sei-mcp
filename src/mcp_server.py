"""Model Context Protocol (MCP) Server Engine for SEI Web Services."""

from __future__ import annotations

import inspect
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from src.config import get_sei_config

logger = logging.getLogger(__name__)

SERVER_START_TIME = time.monotonic()


@dataclass
class McpToolDefinition:
    """Represents a registered MCP tool."""

    name: str
    title: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Any]


class McpServer:
    """JSON-RPC 2.0 Model Context Protocol Server implementation."""

    def __init__(self, name: str = "SEI MCP Server", version: str = "1.0.0") -> None:
        self.name = name
        self.version = version
        self._tools: Dict[str, McpToolDefinition] = {}

    def register_tool(
        self,
        name: str,
        title: str,
        description: str,
        input_schema: Optional[Dict[str, Any]],
        handler: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """Registers a tool on the MCP server."""
        schema = input_schema or {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        if "type" not in schema:
            schema = {
                "type": "object",
                "properties": schema,
            }
        self._tools[name] = McpToolDefinition(
            name=name,
            title=title,
            description=description,
            input_schema=schema,
            handler=handler,
        )

    @property
    def tools(self) -> List[McpToolDefinition]:
        """Returns all registered tools in registration order."""
        return list(self._tools.values())

    def handle_jsonrpc(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processes a single JSON-RPC 2.0 request or notification."""
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request: Expected JSON-RPC 2.0"},
                "id": payload.get("id") if isinstance(payload, dict) else None,
            }

        method = payload.get("method")
        req_id = payload.get("id")
        params = payload.get("params") or {}

        # Notifications do not have an "id" field and do not return a response payload
        if req_id is None and isinstance(method, str) and method.startswith("notifications/"):
            return None

        if method == "initialize":
            requested_version = (
                params.get("protocolVersion") if isinstance(params, dict) else None
            ) or "2024-11-05"
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": requested_version,
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version,
                    },
                },
            }

        if method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            }

        if method == "tools/list":
            tools_list = [
                {
                    "name": t.name,
                    "title": t.title,
                    "description": t.description,
                    "inputSchema": t.input_schema,
                }
                for t in self._tools.values()
            ]
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": tools_list},
            }

        if method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"resources": []},
            }

        if method == "prompts/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"prompts": []},
            }

        if method == "tools/call":
            if not isinstance(params, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params for tools/call"},
                }
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            if not tool_name or tool_name not in self._tools:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: '{tool_name}'",
                    },
                }

            tool_def = self._tools[tool_name]
            try:
                res = tool_def.handler(arguments)
                if inspect.isawaitable(res):
                    import asyncio

                    res = asyncio.run(res)

                # If handler already returned an MCP content dict
                if isinstance(res, dict) and "content" in res and isinstance(res["content"], list):
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": res,
                    }

                text_out = (
                    res
                    if isinstance(res, str)
                    else json.dumps(res, indent=2, ensure_ascii=False)
                )
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": text_out,
                            }
                        ],
                    },
                }
            except Exception as exc:
                logger.error("Error executing tool '%s': %s", tool_name, exc)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "error": True,
                                        "tool": tool_name,
                                        "message": str(exc),
                                    },
                                    indent=2,
                                    ensure_ascii=False,
                                ),
                            }
                        ],
                        "isError": True,
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: '{method}'",
            },
        }


def create_mcp_server() -> McpServer:
    """Factory function to instantiate and register all SEI & SIP tools on the MCP Server."""
    from src.tools import register_all_sei_tools

    server = McpServer(name="SEI MCP Server", version="1.0.0")

    def _get_system_info(_args: Dict[str, Any]) -> Dict[str, Any]:
        cfg = get_sei_config()
        return {
            "status": "healthy",
            "uptimeSeconds": int(time.monotonic() - SERVER_START_TIME),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pythonVersion": sys.version.split()[0],
            "environment": cfg.environment,
            "service": "sei-mcp-server",
            "protocol": "SOAP 1.1 RPC/Encoded (SEI Web Services v3.1+)",
            "seiWsUrl": cfg.sei_ws_url,
            "sipWsUrl": cfg.sip_ws_url,
            "registeredToolsCount": len(server.tools),
            "capabilities": [
                "sei-processos (gestão completa de processos via SOAP SeiWS)",
                "sei-documentos (inclusão, consulta, arquivos, publicações e e-mail)",
                "sei-parametros (blocos, unidades, usuários, contatos, séries, hipóteses, catálogos)",
                "sip-servicos (consulta e replicação de permissões e usuários no SIP)",
            ],
        }

    server.register_tool(
        name="get_system_info",
        title="Get System Info",
        description=(
            "Retrieves server health status, Python runtime version, system uptime, "
            "registered tools count, and SEI SOAP Web Services configuration."
        ),
        input_schema={
            "type": "object",
            "properties": {},
        },
        handler=_get_system_info,
    )

    register_all_sei_tools(server)
    return server
