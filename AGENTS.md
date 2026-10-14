# AGENTS.md — AI Agent & Developer Guide for `sei-mcp`

This document provides architectural context, operational rules, coding conventions, and verification procedures for AI coding agents and developers working in the `sei-mcp` repository.

---

## 1. Project Overview

`sei-mcp` is a **Python** implementation of a **Model Context Protocol (MCP)** server that bridges **Google Cloud Gemini Enterprise** (and other MCP-compliant clients) with the Brazilian **SEI (Sistema Eletrônico de Informações)** standard SOAP Web Services (`SEI-WebServices-v3.1.pdf` and `sei.wsdl`), **SIP (Sistema de Permissões)** Web Services, and **External RH** Web Services.

- **Language & Runtime**: Python 3.11+ (compatible with Python 3.11, 3.12, and 3.13).
- **MCP Protocol Version**: `2024-11-05` (JSON-RPC 2.0 over StreamableHTTP `POST /mcp`, Server-Sent Events `GET /sse` + `POST /messages`, and `--stdio`).
- **Registered Tools**: **72 MCP Tools** (`1` diagnostic tool + `67` SEI WSDL operations + `3` SIP operations + `1` External RH operation).

---

## 2. Core Architectural Invariants (DO NOT BREAK)

### 2.1 Gemini Enterprise OAuth 2.0 Discovery & Handshake Contract
When Google Cloud Gemini Enterprise registers or refreshes an MCP server ("Validate & Save" / "Reload custom actions"), its control plane sends unauthenticated MCP discovery requests before any end-user OAuth token exists.
- **Unauthenticated Endpoints (`GET`)**:
  - `/health`
  - `/.well-known/oauth-protected-resource`
  - `/.well-known/oauth-authorization-server`
- **Unauthenticated JSON-RPC Methods (`POST /mcp` and `POST /messages`)**:
  - `initialize`
  - `notifications/initialized`
  - `ping`
  - `tools/list`
- **Authenticated JSON-RPC Methods (`POST /mcp` and `POST /messages`)**:
  - `tools/call` — When `config.is_oauth_enforced` is `True` (`OAUTH_ENABLED=true`, or `ENV=production` with `OAUTH_ENABLED != "false"`), `src/auth.py:check_mcp_oauth` **must** verify the `Authorization: Bearer <token>` header against `https://oauth2.googleapis.com/tokeninfo` and validate `OAUTH_CLIENT_ID` (if set).

### 2.2 StreamableHTTP Content-Negotiation Rules (`POST /mcp`)
- `GET /mcp` **must** return `HTTP 405 Method Not Allowed` with a JSON-RPC error object.
- `POST /mcp` **must** check that the `Accept` header includes `text/event-stream` (returning `HTTP 406 Not Acceptable` otherwise), matching the MCP StreamableHTTP transport specification.
- Before returning an early error response (`400`, `404`, `406`) on any `POST` request in `src/server.py`, always call `self._drain_body()` so HTTP/1.1 keep-alive connections remain clean.

### 2.3 SEI SOAP 1.1 RPC/Encoded Serialization (`src/client/sei_client.py`)
- SEI's PHP `SoapServer` (`/sei/controlador_ws.php?servico=sei`) uses `style="rpc"` and `use="encoded"` (`http://schemas.xmlsoap.org/soap/encoding/`).
- **Positional Parameter Ordering**: PHP's `SoapServer` passes `<wsdl:part>` child elements of the SOAP Body operation element **positionally** to the underlying PHP method in `SeiWS.php`.
- Therefore, `SeiSoapClient.build_soap_envelope()` **must always** iterate over `WsdlOperation.parts` in the exact order defined in `sei-documentation/sei.wsdl`, emitting `<xsi:nil="true"/>` for omitted trailing/optional parameters rather than skipping middle positional parameters.
- **SEI Credentials Injection**: `SiglaSistema` (`SEI_SIGLA_SISTEMA`), `IdentificacaoServico` (`SEI_IDENTIFICACAO_SERVICO`), and default `IdUnidade` (`SEI_ID_UNIDADE`) are automatically injected into every SOAP call unless explicitly overridden in tool arguments.
- **SOAP Array Encoding**: Complex array parameters (`ArrayOf*`) serialize each item inside an `<item>` element.

---

## 3. Repository Map

| Path | Responsibility |
| :--- | :--- |
| `src/config.py` | Loads `.env` and environment variables into the immutable `SeiConfig` dataclass (`get_sei_config()`). |
| `src/auth.py` | Implements `verify_google_access_token()` and `check_mcp_oauth()` with unauthenticated discovery bypass for `UNAUTHENTICATED_MCP_METHODS`. |
| `src/client/sei_client.py` | Parses `sei-documentation/sei.wsdl` (`load_wsdl_operations()`), constructs SOAP 1.1 RPC/Encoded envelopes (`SeiSoapClient.build_soap_envelope()`), parses SOAP responses/multirefs (`parse_soap_response()`), and provides `encode_text_to_base64()` and `compute_md5_hex()`. |
| `src/mcp_server.py` | Core `McpServer` class managing tool definitions (`ToolDefinition`), JSON Schema generation, and JSON-RPC 2.0 dispatch (`handle_jsonrpc()`). |
| `src/tools/__init__.py` | Entry point `register_all_tools()` registering `get_system_info` plus all process, document, block, catalog, SIP, and RH tools (72 total). |
| `src/tools/processos.py` | 25 SEI process & workflow tools (`gerarProcedimento`, `consultarProcedimento`, `enviarProcesso`, etc.). |
| `src/tools/documentos.py` | 13 SEI document, chunked file upload, publication, and email tools (`incluirDocumento`, `consultarDocumento`, `adicionarArquivo`, etc.). |
| `src/tools/parametros.py` | 12 Block tools + 17 Catalog/Parameter tools + 3 SIP tools (`sip_*`) + 1 External RH tool (`rh_listarCargoFuncao`). |
| `src/server.py` | Multi-threaded HTTP/1.1 (`ThreadingHTTPServer`) and `--stdio` server implementing `/mcp`, `/sse`, `/messages`, `/health`, and `/.well-known/*`. |
| `tests/test_wsdl_and_soap.py` | Unit tests verifying all 71 SOAP operations, credential injection, complex nested structures, `href` multiref resolution, and SOAP Fault handling. |
| `tests/test_mcp_server.py` | Unit tests verifying all 72 registered MCP tools, JSON-RPC dispatch, and OAuth 2.0 enforcement/bypass behavior. |
| `scripts/test-mcp-curl.sh` | End-to-end 13-assertion cURL test script validating `/health`, `/.well-known/*`, `/mcp`, and `/sse` + `/messages`. |
| `infra/` | Terraform configuration for Google Cloud Run v2, Serverless NEG, Global External Application Load Balancer, Static IP, and Managed SSL Certificate. |
| `sei-documentation/` | Reference `SEI-WebServices-v3.1.pdf` manual and `sei.wsdl` specification. |

---

## 4. How to Add or Modify an MCP Tool

1. **Check the WSDL Signature**:
   Inspect `sei-documentation/sei.wsdl` (or `SEI-WebServices-v3.1.pdf`) to verify the operation's exact `<wsdl:message>` parts and complex type fields (`xsd:all` / `SOAP-ENC:Array`).
2. **Register the Tool**:
   Add or update the tool in `src/tools/processos.py`, `src/tools/documentos.py`, or `src/tools/parametros.py` using `server.register_tool(...)`.
   - Use `_with_optional_unidade(...)` for operations that accept `IdUnidade` so the LLM can omit `IdUnidade` and rely on `SEI_ID_UNIDADE`.
   - Provide clear Portuguese/English descriptions and `enum` constraints (e.g., `["S", "N"]`, `["0", "1", "2"]`) matching the SEI PDF documentation.
3. **Add Unit Tests**:
   Update `tests/test_wsdl_and_soap.py` and `tests/test_mcp_server.py` (including the expected total tool count if adding a new tool).

---

## 5. Verification Checklist (Run Before Every Commit)

Always run these commands from the repository root (`/usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp`):

```bash
# 1. Run all unit tests
python3 -m unittest discover -s tests -v

# 2. Run the end-to-end cURL test suite against a local server instance
python3 -c '
import threading, time, subprocess
from http.server import ThreadingHTTPServer
from src.server import SeiMcpHttpRequestHandler
httpd = ThreadingHTTPServer(("127.0.0.1", 13099), SeiMcpHttpRequestHandler)
httpd.daemon_threads = True
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(0.2)
res = subprocess.run(["./scripts/test-mcp-curl.sh", "--url", "http://127.0.0.1:13099"], check=True)
httpd.shutdown()
'

# 3. Validate Terraform formatting
terraform -chdir=infra fmt -check
```
