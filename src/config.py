"""Configuration management for the SEI MCP Server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WSDL_PATH = str(PROJECT_ROOT / "sei-documentation" / "sei.wsdl")


@dataclass(frozen=True)
class SeiConfig:
    """Typed configuration for SEI SOAP Web Services and MCP HTTP/SSE Server."""

    # SEI & SIP SOAP Web Service Endpoints (SEI-WebServices-v3.1.pdf)
    sei_ws_url: str
    sei_wsdl_path: str
    sip_ws_url: str
    rh_ws_url: str

    # SEI System Authentication (Administração > Sistemas > Serviços)
    sigla_sistema: str
    identificacao_servico: str
    id_unidade: str

    # SOAP Transport Settings
    soap_encoding: str
    verify_ssl: bool | str
    timeout: int

    # MCP Server & Gemini Enterprise OAuth Settings
    port: int
    host: str
    environment: str
    oauth_enabled: bool
    oauth_client_id: Optional[str]
    oauth_protected_resource: str
    oauth_authorization_server: str


def _parse_verify_ssl(raw: str) -> bool | str:
    val = raw.strip()
    if val.lower() in ("true", "1", "yes", ""):
        return True
    if val.lower() in ("false", "0", "no"):
        return False
    return val


def get_sei_config() -> SeiConfig:
    """Loads SEI and MCP server configuration from environment variables."""
    env = (
        os.getenv("ENV")
        or os.getenv("PYTHON_ENV")
        or os.getenv("NODE_ENV")
        or "production"
    ).strip()
    is_dev = env.lower() in ("dev", "development", "local", "test")

    raw_oauth = os.getenv("OAUTH_ENABLED", "").strip().lower()
    if raw_oauth == "true":
        oauth_enabled = True
    elif raw_oauth == "false":
        oauth_enabled = False
    else:
        oauth_enabled = not is_dev

    oauth_client_id = (
        os.getenv("OAUTH_CLIENT_ID") or os.getenv("GOOGLE_OAUTH_AUDIENCE") or ""
    ).strip() or None

    return SeiConfig(
        sei_ws_url=os.getenv(
            "SEI_WS_URL",
            "https://sei.orgao.gov.br/sei/controlador_ws.php?servico=sei",
        ).strip(),
        sei_wsdl_path=os.getenv("SEI_WSDL_PATH", DEFAULT_WSDL_PATH).strip(),
        sip_ws_url=os.getenv(
            "SIP_WS_URL",
            "https://sei.orgao.gov.br/sip/controlador_ws.php?servico=wsdl",
        ).strip(),
        rh_ws_url=os.getenv("RH_WS_URL", "").strip(),
        sigla_sistema=os.getenv("SEI_SIGLA_SISTEMA", "").strip(),
        identificacao_servico=os.getenv("SEI_IDENTIFICACAO_SERVICO", "").strip(),
        id_unidade=os.getenv("SEI_ID_UNIDADE", "").strip(),
        soap_encoding=os.getenv("SEI_SOAP_ENCODING", "UTF-8").strip() or "UTF-8",
        verify_ssl=_parse_verify_ssl(os.getenv("SEI_VERIFY_SSL", "true")),
        timeout=int(os.getenv("SEI_TIMEOUT", "60")),
        port=int(os.getenv("PORT", "3000")),
        host=os.getenv("HOST", "0.0.0.0").strip(),
        environment=env,
        oauth_enabled=oauth_enabled,
        oauth_client_id=oauth_client_id,
        oauth_protected_resource=os.getenv(
            "OAUTH_PROTECTED_RESOURCE", "https://mcp-demo-sei.aidemo.space"
        ).strip(),
        oauth_authorization_server=os.getenv(
            "OAUTH_AUTHORIZATION_SERVER", "https://accounts.google.com"
        ).strip(),
    )
