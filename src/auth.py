"""Google OAuth 2.0 Authentication Gate for Gemini Enterprise MCP Requests."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from src.config import SeiConfig, get_sei_config

logger = logging.getLogger(__name__)

TOOLS_CALL_METHOD = "tools/call"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


@dataclass
class AuthCheckResult:
    """Result of evaluating the OAuth 2.0 gate on an incoming MCP request."""

    allowed: bool
    status_code: int = 200
    error_payload: Optional[Dict[str, Any]] = None
    user_info: Optional[Dict[str, Any]] = None


def verify_google_access_token(token: str, timeout: int = 10) -> Dict[str, Any]:
    """Verifies a Google OAuth 2.0 Bearer access token via Google's tokeninfo endpoint."""
    response = requests.get(
        GOOGLE_TOKENINFO_URL,
        params={"access_token": token},
        timeout=timeout,
    )
    if response.status_code != 200:
        try:
            err_data = response.json()
            err_desc = err_data.get("error_description") or err_data.get("error") or response.text
        except Exception:
            err_desc = response.text
        raise ValueError(f"Token verification failed (HTTP {response.status_code}): {err_desc}")

    token_info = response.json()
    if not isinstance(token_info, dict) or "error" in token_info:
        raise ValueError(token_info.get("error_description", "Invalid token payload"))
    return token_info


def check_mcp_oauth(
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]],
    config: Optional[SeiConfig] = None,
) -> AuthCheckResult:
    """Enforces OAuth on MCP requests following the Gemini Enterprise MCP pattern.

    1. Tool discovery requests (`initialize`, `notifications/initialized`, `ping`,
       `tools/list`, etc.) are permitted without blocking discovery, allowing
       Gemini Enterprise "Validate & Save" / "Reload custom actions" to always succeed.
    2. Tool execution requests (`tools/call`) require Google OAuth 2.0 Bearer token
       authentication when `oauth_enabled` is True.
    """
    cfg = config or get_sei_config()

    if not isinstance(body, dict):
        return AuthCheckResult(allowed=True)

    method = body.get("method")
    req_id = body.get("id")

    if not cfg.oauth_enabled or method != TOOLS_CALL_METHOD:
        return AuthCheckResult(allowed=True)

    # Case-insensitive lookup for Authorization header
    auth_header = ""
    for k, v in headers.items():
        if k.lower() == "authorization":
            auth_header = v
            break

    if not auth_header or not auth_header.startswith("Bearer "):
        return AuthCheckResult(
            allowed=False,
            status_code=401,
            error_payload={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": (
                        "Authentication required. Please provide a Bearer token "
                        "in the Authorization header."
                    ),
                },
                "id": req_id,
            },
        )

    token = auth_header[7:].strip()
    if not token:
        return AuthCheckResult(
            allowed=False,
            status_code=401,
            error_payload={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": (
                        "Authentication required. Please provide a Bearer token "
                        "in the Authorization header."
                    ),
                },
                "id": req_id,
            },
        )

    try:
        token_info = verify_google_access_token(token)
        audience = cfg.oauth_client_id
        token_aud = token_info.get("aud") or token_info.get("azp")

        if audience and token_aud != audience:
            logger.warning("Token audience mismatch: %s vs %s", token_aud, audience)
            return AuthCheckResult(
                allowed=False,
                status_code=403,
                error_payload={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32001,
                        "message": f"Invalid audience: expected {audience}",
                    },
                    "id": req_id,
                },
            )

        return AuthCheckResult(allowed=True, status_code=200, user_info=token_info)

    except Exception as exc:
        logger.error("Error verifying OAuth token: %s", exc)
        return AuthCheckResult(
            allowed=False,
            status_code=401,
            error_payload={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": "Invalid or expired OAuth token.",
                    "data": str(exc),
                },
                "id": req_id,
            },
        )
