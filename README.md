# Enterprise Node.js MCP Server with Authentication

A simple, production-ready **Model Context Protocol (MCP)** server built with **Node.js**, **Express**, and **TypeScript**. It supports HTTP Server-Sent Events (SSE) transport and flexible token authentication for seamless integration with **Gemini Enterprise**, **Claude Desktop**, **Cursor**, and other MCP-compliant clients.

---

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Local Development](#local-development)
- [Testing & Verification](#testing--verification)
- [Deployment Guide](#deployment-guide)
  - [Option 1: Deploy Directly to Google Cloud Run (CLI)](#option-1-deploy-directly-to-google-cloud-run-cli)
  - [Option 2: Deploy with Google Cloud Build (CI/CD)](#option-2-deploy-with-google-cloud-build-cicd)
  - [Option 3: Enterprise Infrastructure with Terraform (Load Balancer + NEG + SSL)](#option-3-enterprise-infrastructure-with-terraform-load-balancer--neg--ssl)
  - [Option 4: Docker / Generic Container Deployment](#option-4-docker--generic-container-deployment)
- [Client Configuration](#client-configuration)
  - [Gemini Enterprise Integration](#gemini-enterprise-integration)
  - [Claude Desktop Integration](#claude-desktop-integration)
  - [Cursor / IDE Integration](#cursor--ide-integration)
  - [MCP Inspector](#mcp-inspector)
- [API & Endpoint Reference](#api--endpoint-reference)
- [Built-in Tools](#built-in-tools)
- [Extending & Adding Custom Tools](#extending--adding-custom-tools)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [License](#license)

---

## Architecture

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │                     Clients                            │
                                  │  Gemini Enterprise / Claude / Cursor / MCP Inspector   │
                                  └──────────────────────────┬─────────────────────────────┘
                                                             │
                                      HTTP / SSE with Auth Header or Query Param
                                      (Bearer Token / x-api-key / ?token=...)
                                                             │
                                                             ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │          GCP External Application Load Balancer        │
                                  │          (Optional: Static IP + Managed SSL Cert)      │
                                  └──────────────────────────┬─────────────────────────────┘
                                                             │
                                                             ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │            Serverless NEG / Google Cloud Run           │
                                  │              (Container on Port 3000)                  │
                                  └──────────────────────────┬─────────────────────────────┘
                                                             │
                               ┌─────────────────────────────┴─────────────────────────────┐
                               │                                                           │
                               ▼                                                           ▼
                ┌──────────────────────────────┐                            ┌──────────────────────────────┐
                │        GET /health           │                            │    GET /sse & POST /messages │
                │   (Unauthenticated Probe)    │                            │  (Token Authentication Gate) │
                └──────────────────────────────┘                            └──────────────┬───────────────┘
                                                                                           │
                                                                                           ▼
                                                                            ┌──────────────────────────────┐
                                                                            │         MCP Server           │
                                                                            │     (@modelcontextprotocol)  │
                                                                            │  - get_system_info           │
                                                                            │  - echo                      │
                                                                            │  - calculate                 │
                                                                            └──────────────────────────────┘
```

---

## Features

- ⚡ **Standard MCP Implementation**: Built on official [`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk).
- 📡 **HTTP / SSE Transport**: Supports Server-Sent Events (`/sse`) for bidirectional streaming and `/messages` for JSON-RPC POST requests.
- 🔐 **Multi-Method Authentication Middleware**:
  - `Authorization: Bearer <AUTH_TOKEN>` header
  - `x-api-key: <AUTH_TOKEN>` custom header
  - `?token=<AUTH_TOKEN>` URL query parameter (convenient for SSE browser/EventSource clients)
- 🛠️ **Built-in Sample Tools**:
  - `get_system_info`: Returns server status, Node.js version, uptime, and environment.
  - `echo`: Echoes input messages.
  - `calculate`: Evaluates basic arithmetic operations (`add`, `subtract`, `multiply`, `divide`).
- 🏥 **Health Check Endpoint**: `/health` unauthenticated endpoint for Cloud Run readiness/liveness probes and load balancer health checks.
- 🐳 **Optimized Multi-Stage Dockerfile**: Slim, secure Node.js Alpine image ready for Cloud Run, Kubernetes, or standalone Docker.
- ☁️ **Infrastructure as Code**: Complete Terraform configuration in [`infra/`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/infra/README.md) for deploying a Global External HTTP(S) Load Balancer with Serverless Network Endpoint Groups (NEG) and optional Google-managed SSL.

---

## Prerequisites

- **Node.js**: v20.x or v22.x LTS installed ([Node.js downloads](https://nodejs.org/)).
- **npm**: v10+ (bundled with Node.js).
- **Docker** *(optional)*: For building and testing container images locally.
- **Google Cloud SDK (`gcloud`)** *(optional)*: For deploying to GCP Cloud Run and Cloud Build.
- **Terraform CLI (>= 1.5.0)** *(optional)*: For provisioning GCP infrastructure.

---

## Configuration

Server behavior and security are controlled via environment variables.

### Environment Variables

| Variable | Type | Default | Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| `PORT` | `number` | `3000` | No | Port on which the HTTP/SSE server listens. |
| `HOST` | `string` | `0.0.0.0` | No | Network interface binding (use `0.0.0.0` for containers/cloud). |
| `AUTH_TOKEN` | `string` | *(none)* | **Yes** (if auth is enabled) | Secret token required to authenticate requests to `/sse` and `/messages`. |
| `REQUIRE_AUTH` | `boolean` | `true` | No | Set to `false` to disable token verification (e.g. for isolated local testing). Set to `true` for production. |
| `NODE_ENV` | `string` | `development` | No | Runtime environment mode (`development` or `production`). |

### Setting Up Environment Variables

1. Copy the sample environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit [`.env`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/.env.example):
   ```env
   # Server Configuration
   PORT=3000
   HOST=0.0.0.0

   # Security / Authentication
   AUTH_TOKEN=your-strong-secret-mcp-token-here
   REQUIRE_AUTH=true
   ```

---

## Local Development

### 1. Install Dependencies

```bash
npm install
```

### 2. Run in Development Mode (Live Reload)

Runs the TypeScript source code directly with `tsx`:

```bash
npm run dev
```

### 3. Build and Run in Production Mode

Compiles TypeScript to JavaScript in `dist/` and runs the production build:

```bash
npm run build
npm start
```

---

## Testing & Verification

Once the server is running locally (e.g. at `http://localhost:3000`), you can test the endpoints using `curl` or browser tools.

### 1. Health Check (Unauthenticated)

```bash
curl -i http://localhost:3000/health
```

**Expected Response (`200 OK`)**:
```json
{
  "status": "healthy",
  "service": "sei-mcp-server",
  "authRequired": true,
  "activeSessions": 0
}
```

### 2. Unauthenticated Request to `/sse` (Should Fail)

```bash
curl -i http://localhost:3000/sse
```

**Expected Response (`401 Unauthorized`)**:
```json
{
  "error": "Unauthorized",
  "message": "Missing authentication token. Provide Authorization header (Bearer <token>) or x-api-key."
}
```

### 3. Authenticated SSE Stream with Bearer Token

```bash
curl -N -i -H "Authorization: Bearer your-strong-secret-mcp-token-here" http://localhost:3000/sse
```

**Expected Stream Output**:
```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: endpoint
data: /messages?sessionId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 4. Authenticated SSE Stream with `x-api-key` Header

```bash
curl -N -i -H "x-api-key: your-strong-secret-mcp-token-here" http://localhost:3000/sse
```

### 5. Authenticated SSE Stream with Query Parameter

```bash
curl -N -i "http://localhost:3000/sse?token=your-strong-secret-mcp-token-here"
```

---

## Deployment Guide

### Option 1: Deploy Directly to Google Cloud Run (CLI)

The fastest way to deploy the MCP server to Google Cloud is using the `gcloud` CLI with source-based deployment:

1. **Authenticate and set your GCP project**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_GCP_PROJECT_ID
   ```

2. **Deploy directly from source**:
   ```bash
   gcloud run deploy sei-mcp-server \
     --source . \
     --region southamerica-east1 \
     --platform managed \
     --allow-unauthenticated \
     --port 3000 \
     --set-env-vars REQUIRE_AUTH=true,AUTH_TOKEN="your-strong-secret-mcp-token-here" \
     --min-instances 0 \
     --max-instances 5 \
     --timeout 300
   ```

   > [!NOTE]
   > `--allow-unauthenticated` allows Cloud Run ingress to receive traffic publicly. Access to MCP tools is secured by the application's authentication middleware via `AUTH_TOKEN`.

3. **Obtain Service URL**:
   After deployment, `gcloud` outputs your Service URL (e.g. `https://sei-mcp-server-xyz-uc.a.run.app`). Your SSE endpoint will be:
   ```
   https://sei-mcp-server-xyz-uc.a.run.app/sse
   ```

---

### Option 2: Deploy with Google Cloud Build (CI/CD)

The repository includes a ready-to-use [`cloudbuild.yaml`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/cloudbuild.yaml) pipeline that builds the container image, pushes it to Google Container/Artifact Registry, and deploys it to Cloud Run.

1. **Submit Cloud Build with Substitutions**:
   ```bash
   gcloud builds submit --config=cloudbuild.yaml \
     --substitutions=_SERVICE_NAME="sei-mcp-server",_REGION="southamerica-east1",_AUTH_TOKEN="your-strong-secret-mcp-token-here",_TAG="latest"
   ```

2. **Automated Trigger (Optional)**:
   You can connect your GitHub repository to Cloud Build triggers to automatically deploy on every push to `main`.

---

### Option 3: Enterprise Infrastructure with Terraform (Load Balancer + NEG + SSL)

For enterprise production deployments requiring a **Static IP address**, **Custom Domain**, and **Google-managed SSL Certificate**, use the Terraform configuration in [`infra/`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/infra/README.md).

#### Infrastructure Architecture
- **Global Static IP Address**: Dedicated IPv4 entry point.
- **External HTTP(S) Load Balancer**: Distributes traffic and manages SSL termination.
- **Serverless NEG**: Connects the Load Balancer directly to the Cloud Run service.
- **Managed SSL Certificate**: Automatic provisioning and renewal via Google Cloud.

#### Step-by-Step Provisioning:

1. **Deploy the Cloud Run service** first using Option 1 or Option 2.
2. **Navigate to the infrastructure directory**:
   ```bash
   cd infra
   ```
3. **Configure Terraform Variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
   Edit [`infra/terraform.tfvars`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/infra/terraform.tfvars.example):
   ```hcl
   project_id             = "your-gcp-project-id"
   region                 = "southamerica-east1"
   cloud_run_service_name = "sei-mcp-server"

   # Set to true if you have a custom domain pointing to the Load Balancer IP
   enable_ssl  = false
   domain_name = "mcp.example.com"
   ```
4. **Initialize and Apply Terraform**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```
5. **Inspect Outputs**:
   ```
   load_balancer_ip      = "34.120.x.x"
   mcp_sse_endpoint_http = "http://34.120.x.x/sse"
   ```

---

### Option 4: Docker / Generic Container Deployment

The [`Dockerfile`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/Dockerfile) uses a multi-stage build:

1. **Build the image**:
   ```bash
   docker build -t sei-mcp-server .
   ```

2. **Run container with environment variables**:
   ```bash
   docker run -d \
     --name sei-mcp-server \
     -p 3000:3000 \
     -e PORT=3000 \
     -e HOST=0.0.0.0 \
     -e REQUIRE_AUTH=true \
     -e AUTH_TOKEN=your-strong-secret-mcp-token-here \
     sei-mcp-server
   ```

3. **Check container logs**:
   ```bash
   docker logs -f sei-mcp-server
   ```

---

## Client Configuration

### Gemini Enterprise Integration

Gemini Enterprise supports integrating custom tools via remote Model Context Protocol (MCP) HTTP/SSE endpoints.

#### Step-by-Step Setup:

1. **Open the Admin Console**:
   - Navigate to the **Gemini Enterprise Admin Console** (or Vertex AI Agent Builder / Extensions).
   - Go to **Extensions** > **Custom Tools / MCP** > **Add Custom Extension**.

2. **Configure Connection Parameters**:
   - **Name**: `Enterprise MCP Server` (or descriptive name).
   - **Transport Type**: `Server-Sent Events (SSE)` or `Remote HTTP / MCP`.
   - **Server Endpoint URL**: `https://<YOUR-CLOUD-RUN-URL>/sse` (e.g. `https://sei-mcp-server-xyz-uc.a.run.app/sse`).
   - **Authentication Type**: `Bearer Token` or `API Key Header`.
   - **Header Key**: `Authorization` (Value: `Bearer your-strong-secret-mcp-token-here`) or `x-api-key` (Value: `your-strong-secret-mcp-token-here`).

3. **Save and Discover Tools**:
   - Click **Save / Validate Connection**.
   - Gemini Enterprise will connect to `/sse`, perform protocol handshake, and discover all registered tools (`get_system_info`, `echo`, `calculate`).
   - The tools are now immediately usable in Gemini Enterprise prompts and agent workflows.

---

### Claude Desktop Integration

To connect Claude Desktop to your remote MCP server, configure your `claude_desktop_config.json`:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add the server configuration using `mcp-remote` bridge or direct SSE:

```json
{
  "mcpServers": {
    "enterprise-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://<YOUR-HOST>/sse",
        "--header",
        "Authorization: Bearer your-strong-secret-mcp-token-here"
      ]
    }
  }
}
```

---

### Cursor / IDE Integration

For IDEs supporting MCP (such as Cursor, Windsurf, or VS Code MCP extensions):

Add the server configuration to your workspace `.cursor/mcp.json` or global MCP settings:

```json
{
  "mcpServers": {
    "enterprise-mcp": {
      "url": "https://<YOUR-HOST>/sse",
      "headers": {
        "Authorization": "Bearer your-strong-secret-mcp-token-here"
      }
    }
  }
}
```

---

### MCP Inspector

You can inspect, debug, and test tools interactively using the official MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

In the Inspector UI:
- **Transport Type**: `SSE`
- **URL**: `http://localhost:3000/sse?token=your-strong-secret-mcp-token-here` (or pass headers via the configuration dialog).
- Click **Connect** to explore tools, send test arguments, and view JSON-RPC request/response payloads.

---

## API & Endpoint Reference

| Endpoint | HTTP Method | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| [`/health`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/server.ts#L20-L27) | `GET` | No | Unauthenticated health status, session count, and service info. |
| [`/sse`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/server.ts#L30-L51) | `GET` | **Yes** | Establishes the Server-Sent Events (SSE) streaming transport. |
| [`/messages`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/server.ts#L54-L74) | `POST` | **Yes** | Receives JSON-RPC client messages for an active session (`?sessionId=...`). |

### Authentication Schemes Supported

The [`authenticateRequest`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/auth.ts#L10-L54) middleware checks credentials in the following order:

1. **Bearer Token**: `Authorization: Bearer <AUTH_TOKEN>`
2. **API Key Header**: `x-api-key: <AUTH_TOKEN>`
3. **Query Parameter**: `?token=<AUTH_TOKEN>`

### Error Codes

| Status Code | Reason | Cause / Resolution |
| :--- | :--- | :--- |
| `401 Unauthorized` | Missing token | Provide credentials via `Authorization` header, `x-api-key`, or `?token=`. |
| `403 Forbidden` | Invalid token | Provided token does not match the configured `AUTH_TOKEN`. |
| `404 Not Found` | Session expired / invalid | The `sessionId` provided to `/messages` is invalid or the SSE connection closed. |
| `500 Internal Error` | Server misconfiguration | `AUTH_TOKEN` is not set on the server while `REQUIRE_AUTH=true`. |

---

## Built-in Tools

The server ships with sample tools defined in [`src/mcp.ts`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/mcp.ts):

### 1. `get_system_info`
Retrieves server status, Node.js version, uptime, and environment.
- **Parameters**: None
- **Sample Output**:
  ```json
  {
    "status": "healthy",
    "uptimeSeconds": 1420,
    "timestamp": "2026-08-11T16:00:00.000Z",
    "nodeVersion": "v22.13.4",
    "environment": "production"
  }
  ```

### 2. `echo`
Echoes back the provided message.
- **Parameters**:
  - `message` (`string`): The text to echo.
- **Sample Output**: `[MCP Server Echo]: Hello World`

### 3. `calculate`
Performs basic arithmetic operations.
- **Parameters**:
  - `operation` (`"add" | "subtract" | "multiply" | "divide"`): Arithmetic operation.
  - `a` (`number`): First operand.
  - `b` (`number`): Second operand.
- **Sample Output**: `Calculation result: 10 multiply 5 = 50`

---

## Extending & Adding Custom Tools

To add new custom tools, open [`src/mcp.ts`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/mcp.ts) and register them on the [`McpServer`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/mcp.ts#L7-L99) instance using [`zod`](https://zod.dev) for parameter schemas:

```typescript
import { z } from "zod";

export function createMcpServer(): McpServer {
  const server = new McpServer({
    name: "Enterprise Node MCP Server",
    version: "1.0.0",
  });

  // Register a custom tool
  server.registerTool(
    "search_database",
    {
      description: "Query company internal knowledge base or database",
      inputSchema: {
        query: z.string().describe("Search query string"),
        limit: z.number().optional().default(5).describe("Max results to return"),
      },
    },
    async ({ query, limit }) => {
      // Your custom business logic here (e.g. database query, API call)
      const results = [`Result 1 for "${query}"`, `Result 2 for "${query}"`].slice(0, limit);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    }
  );

  return server;
}
```

---

## Troubleshooting & FAQ

### 1. `401 Unauthorized` or `403 Forbidden`
- Ensure that `AUTH_TOKEN` is set in your Cloud Run or local `.env` environment variables.
- Verify that your client sends `Authorization: Bearer <AUTH_TOKEN>` or the `x-api-key` header with matching case and exact value.

### 2. SSE Connection Drops or Times Out
- When running behind Cloud Run or Load Balancers, ensure connection timeout is appropriately configured (`--timeout 300` or higher).
- Cloud Run natively supports HTTP/2 and Server-Sent Events streaming. Ensure response buffering is disabled on intermediate reverse proxies.

### 3. Session Expired (`404 Session not found`)
- SSE sessions are ephemeral and kept in-memory. If the Cloud Run container restarts or scales to a new instance, the client must re-establish the `/sse` stream.
- For high-availability multi-instance setups, ensure session affinity is configured on the Load Balancer or use a single minimum instance (`--min-instances 1`).

---

## License

This project is licensed under the [MIT License](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/LICENSE).
