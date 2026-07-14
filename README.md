# Enterprise Node.js MCP Server with Authentication

A simple, production-ready **Model Context Protocol (MCP)** server built with **Node.js**, **Express**, and **TypeScript**, supporting HTTP/SSE transport and authentication for integration with **Gemini Enterprise** and external MCP clients.

---

## Features

- ⚡ **Model Context Protocol (MCP)** standard implementation (`@modelcontextprotocol/sdk`).
- 📡 **SSE Transport** (`/sse` & `/messages`) over HTTP for remote client connections.
- 🔐 **Authentication Middleware**: Bearer Token (`Authorization: Bearer <TOKEN>`), custom key (`x-api-key`), or URL query parameter (`?token=...`).
- 🛠️ **Sample Tools Included**:
  - `get_system_info`: Returns server status, node version, and system uptime.
  - `echo`: Echoes input message back.
  - `calculate`: Basic arithmetic operations (`add`, `subtract`, `multiply`, `divide`).
- 🏥 **Health Check Endpoint**: `/health` (Unauthenticated for load balancers / cloud probes).
- 🐳 **Docker Ready**: Included multi-stage `Dockerfile` optimized for GCP Cloud Run or Kubernetes.

---

## Quickstart

### 1. Installation

```bash
npm install
```

### 2. Environment Setup

Copy `.env.example` to `.env` and set your secret authentication token:

```bash
cp .env.example .env
```

Edit `.env`:

```env
PORT=3000
HOST=0.0.0.0
AUTH_TOKEN=your-secret-mcp-token-here
REQUIRE_AUTH=true
```

### 3. Run in Development Mode

```bash
npm run dev
```

### 4. Build and Run in Production Mode

```bash
npm run build
npm start
```

---

## Connecting to Gemini Enterprise

Gemini Enterprise allows integrating remote tools and custom extensions via standard remote HTTP/SSE endpoints.

### Step-by-Step Configuration:

1. **Deploy your Server to a Public Endpoint** (e.g. Google Cloud Run, GCP Compute Engine, or local tunnel like `ngrok`).
   - Cloud Run example deployment:
     ```bash
     gcloud run deploy mcp-server --source . --port 3000 --set-env-vars AUTH_TOKEN="your-secret-mcp-token-here"
     ```
   - Copy the deployed HTTPS URL (e.g., `https://mcp-server-xyz-uc.a.run.app`).

2. **Register Extension in Gemini Enterprise Console**:
   - Navigate to **Gemini Enterprise Admin Console** > **Extensions / Custom Tools** > **Add Custom Server / MCP**.
   - Set **Transport Type**: `Server-Sent Events (SSE)` or `Remote HTTP/MCP`.
   - Set **Server URL**: `https://<YOUR-HOST>/sse` (e.g., `https://mcp-server-xyz-uc.a.run.app/sse`).
   - Set **Authentication Type**: `Bearer Token` or `API Key Header`.
   - Set **Header Name**: `Authorization` (Value: `Bearer your-secret-mcp-token-here`) or `x-api-key` (Value: `your-secret-mcp-token-here`).

3. **Test Tool Invocation**:
   - Once saved, Gemini Enterprise will connect to `/sse`, discover tools (`get_system_info`, `echo`, `calculate`), and allow users to invoke them in chat prompts.

---

## Endpoint API Reference

| Endpoint | Method | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `/health` | GET | No | Returns health status and session metrics |
| `/sse` | GET | **Yes** | Establishes the Server-Sent Events stream connection |
| `/messages` | POST | **Yes** | Accepts JSON-RPC requests for active sessions (`?sessionId=...`) |

### Testing with `curl`

#### 1. Unauthenticated request (Fails with HTTP 401)
```bash
curl -i http://localhost:3000/sse
```

#### 2. Authenticated request with Bearer token
```bash
curl -N -i -H "Authorization: Bearer your-secret-mcp-token-here" http://localhost:3000/sse
```

#### 3. Health check endpoint
```bash
curl http://localhost:3000/health
```

---

## Extending the Server

To add new tools, modify [`src/mcp.ts`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/mcp.ts):

```typescript
import { z } from "zod";

server.tool(
  "my_custom_tool",
  "Tool description for LLM",
  {
    inputParam: z.string().describe("Parameter description"),
  },
  async ({ inputParam }) => {
    return {
      content: [{ type: "text", text: `Output: ${inputParam}` }],
    };
  }
);
```
