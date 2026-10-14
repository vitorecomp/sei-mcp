"""Tool registration package for SEI and SIP SOAP Web Services."""

from __future__ import annotations

from src.mcp_server import McpServer
from src.tools.documentos import register_documentos_tools
from src.tools.parametros import register_parametros_tools
from src.tools.processos import register_processos_tools


def register_all_sei_tools(server: McpServer) -> None:
    """Registers all SEI and SIP tools on the given MCP server instance."""
    register_processos_tools(server)
    register_documentos_tools(server)
    register_parametros_tools(server)


__all__ = [
    "register_all_sei_tools",
    "register_processos_tools",
    "register_documentos_tools",
    "register_parametros_tools",
]
