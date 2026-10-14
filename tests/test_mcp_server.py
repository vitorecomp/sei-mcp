"""Unit and integration tests for MCP JSON-RPC engine and OAuth 2.0 gate."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from src.auth import check_mcp_oauth
from src.config import SeiConfig
from src.mcp_server import create_mcp_server


class TestMcpServerAndOAuth(unittest.TestCase):
    """Tests MCP protocol methods (initialize, tools/list, tools/call) and OAuth 2.0 middleware."""

    def setUp(self) -> None:
        self.server = create_mcp_server()
        self.prod_config = SeiConfig(
            sei_ws_url="https://sei.exemplo.gov.br/sei/controlador_ws.php?servico=sei",
            sei_wsdl_path="sei-documentation/sei.wsdl",
            sip_ws_url="https://sei.exemplo.gov.br/sip/controlador_ws.php?servico=wsdl",
            rh_ws_url="",
            sigla_sistema="SISTEMA_PROD",
            identificacao_servico="TOKEN_PROD",
            id_unidade="110000001",
            soap_encoding="UTF-8",
            verify_ssl=True,
            timeout=60,
            port=3000,
            host="0.0.0.0",
            environment="production",
            oauth_enabled=True,
            oauth_client_id="my-client-id.apps.googleusercontent.com",
            oauth_protected_resource="https://mcp-demo-sei.aidemo.space",
            oauth_authorization_server="https://accounts.google.com",
        )

    def test_all_72_tools_registered(self) -> None:
        """Server must register all 72 tools (get_system_info + 67 SEI WSDL + 3 SIP + 1 RH)."""
        self.assertEqual(len(self.server.tools), 72)

    def test_initialize_and_tools_list(self) -> None:
        """MCP initialize and tools/list return valid JSON-RPC 2.0 responses."""
        init_resp = self.server.handle_jsonrpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"},
            }
        )
        self.assertIsNotNone(init_resp)
        assert init_resp is not None
        self.assertEqual(init_resp["result"]["serverInfo"]["name"], "SEI MCP Server")

        list_resp = self.server.handle_jsonrpc(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
        self.assertIsNotNone(list_resp)
        assert list_resp is not None
        self.assertEqual(len(list_resp["result"]["tools"]), 72)

    def test_call_get_system_info(self) -> None:
        """Calling get_system_info returns healthy status and registeredToolsCount=72."""
        call_resp = self.server.handle_jsonrpc(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "get_system_info", "arguments": {}},
            }
        )
        self.assertIsNotNone(call_resp)
        assert call_resp is not None
        content_text = call_resp["result"]["content"][0]["text"]
        info = json.loads(content_text)
        self.assertEqual(info["status"], "healthy")
        self.assertEqual(info["registeredToolsCount"], 72)

    def test_oauth_allows_discovery_in_production_without_token(self) -> None:
        """initialize, tools/list, and ping must bypass OAuth even when OAUTH_ENABLED=true."""
        for method in ("initialize", "tools/list", "ping"):
            res = check_mcp_oauth(
                headers={},
                body={"jsonrpc": "2.0", "id": 1, "method": method},
                config=self.prod_config,
            )
            self.assertTrue(res.allowed, f"{method} should be allowed without OAuth token")

    def test_oauth_blocks_unauthenticated_tools_call_in_production(self) -> None:
        """tools/call without Bearer token must return 401 when OAUTH_ENABLED=true."""
        res = check_mcp_oauth(
            headers={},
            body={
                "jsonrpc": "2.0",
                "id": 99,
                "method": "tools/call",
                "params": {"name": "sei_listar_unidades", "arguments": {}},
            },
            config=self.prod_config,
        )
        self.assertFalse(res.allowed)
        self.assertEqual(res.status_code, 401)
        assert res.error_payload is not None
        self.assertEqual(res.error_payload["error"]["code"], -32001)

    @patch("src.auth.verify_google_access_token")
    def test_oauth_validates_audience_in_production(self, mock_verify: unittest.mock.MagicMock) -> None:
        """tools/call with mismatched audience returns 403; matching audience returns 200."""
        mock_verify.return_value = {"aud": "wrong-client.apps.googleusercontent.com"}
        res_bad = check_mcp_oauth(
            headers={"Authorization": "Bearer fake-token"},
            body={"jsonrpc": "2.0", "id": 10, "method": "tools/call"},
            config=self.prod_config,
        )
        self.assertFalse(res_bad.allowed)
        self.assertEqual(res_bad.status_code, 403)

        mock_verify.return_value = {"aud": "my-client-id.apps.googleusercontent.com"}
        res_ok = check_mcp_oauth(
            headers={"Authorization": "Bearer valid-token"},
            body={"jsonrpc": "2.0", "id": 11, "method": "tools/call"},
            config=self.prod_config,
        )
        self.assertTrue(res_ok.allowed)
        self.assertEqual(res_ok.status_code, 200)


if __name__ == "__main__":
    unittest.main()
