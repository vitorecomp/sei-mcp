# Enterprise Node.js MCP Server for Gemini Enterprise

A production-ready **Model Context Protocol (MCP)** server built with **Node.js**, **Express**, and **TypeScript**. It provides Server-Sent Events (SSE) transport and token authentication, designed specifically for integration with **Gemini Enterprise** custom tools and extensions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Gemini Enterprise                             │
│                  (Admin Console / Extensions / Tools)                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                 HTTPS / SSE Request with OAuth Bearer Token
                 `Authorization: Bearer <OAUTH_ACCESS_TOKEN>`
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 GCP External Application Load Balancer                  │
│                (Global Static IP + Managed SSL via Terraform)           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Serverless NEG / Google Cloud Run                     │
│                        (Container on Port 3000)                         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
       ┌─────────────────────────────┴─────────────────────────────┐
       │                                                           │
       ▼                                                           ▼
┌──────────────────────────────┐            ┌──────────────────────────────┐
│         GET /health          │            │  GET /sse & POST /messages   │
│   (Unauthenticated Probe)    │            │  (Google OAuth 2.0 Auth Gate)│
└──────────────────────────────┘            └──────────────┬───────────────┘
                                                           │
                                                           ▼
                                            ┌──────────────────────────────┐
                                            │      MCP Server Actions      │
                                            │   - calculate                │
                                            │   - get_system_info          │
                                            │   - echo                     │
                                            └──────────────────────────────┘
```

---

## Prerequisites

- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and authenticated.
- [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) (>= 1.5.0).
- [Node.js](https://nodejs.org/) (v20.x or v22.x LTS) & npm (for local development).
- A Google Cloud Project with billing enabled and the following APIs enabled:
  ```bash
  gcloud services enable run.googleapis.com compute.googleapis.com cloudbuild.googleapis.com
  ```

---

## Configuration

Server behavior and environment settings:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `NODE_ENV` | When set to `production` (default in cloud), enforces Google OAuth 2.0 authentication. When set to `dev` or `development`, authentication is disabled. | `production` |
| `OAUTH_CLIENT_ID` | Google OAuth 2.0 Client ID for token audience verification in production | *(none)* |
| `PORT` | Listening port for the application | `3000` |
| `HOST` | Binding address | `0.0.0.0` |

---

## Streamlined Setup: Gemini Enterprise with Terraform

Follow these steps to deploy the MCP server and connect it to Gemini Enterprise.

### Step 1: Build & Deploy Container to Cloud Run

Build the multi-stage Docker image using Google Cloud Build and deploy it to Cloud Run:

```bash
# 1. Ensure you are in the project root directory
cd /path/to/sei-mcp

# 2. Set your GCP project
gcloud config set project YOUR_GCP_PROJECT_ID

# 3. Build Docker container image via Cloud Build
gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/sei-mcp-server:latest .

# 4. Deploy to Cloud Run (Google OAuth 2.0 authentication enforced in production)
gcloud run deploy sei-mcp-server \
  --image gcr.io/YOUR_GCP_PROJECT_ID/sei-mcp-server:latest \
  --region southamerica-east1 \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --set-env-vars NODE_ENV=production,OAUTH_CLIENT_ID="YOUR_OAUTH_CLIENT_ID.apps.googleusercontent.com" \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 300
```

> [!NOTE]
> - In **production** (`NODE_ENV=production`), the server strictly enforces **Google OAuth 2.0 authentication** on all `/sse` and `/messages` endpoints.
> - In **development** (`NODE_ENV=dev`), authentication is disabled for frictionless local development.

---

### Step 2: Provision Load Balancer & Static IP with Terraform

Use the included Terraform module in [`infra/`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/infra/README.md) to provision an External Application Load Balancer with a Serverless NEG pointing to your Cloud Run service.

1. Navigate to the infrastructure folder:
   ```bash
   cd infra
   ```

2. Create and configure your `terraform.tfvars`:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. Edit [`infra/terraform.tfvars`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/infra/terraform.tfvars.example):
   ```hcl
   project_id             = "YOUR_GCP_PROJECT_ID"
   region                 = "southamerica-east1"
   cloud_run_service_name = "sei-mcp-server"

   # Optional: Set to true if you have a custom domain pointing to the Load Balancer IP
   enable_ssl  = false
   domain_name = ""
   ```

4. Initialize and apply Terraform:
   ```bash
   terraform init
   terraform apply
   ```

5. Note the outputs:
   - `load_balancer_ip`: Static IP of the Load Balancer (e.g. `34.120.x.x`).
   - `mcp_sse_endpoint_http`: SSE endpoint URL (e.g. `http://34.120.x.x/sse` or `https://<YOUR-DOMAIN>/sse`).

---

### Step 3: Register Extension in Gemini Enterprise (OAuth 2.0)

When adding an MCP Server in **Gemini Enterprise** (or Vertex AI Extensions / Custom Tools), configure the OAuth 2.0 authentication fields:

#### 1. Create OAuth 2.0 Credentials in Google Cloud Console
1. Go to **Google Cloud Console** > **APIs & Services** > **Credentials**.
2. Click **Create Credentials** > **OAuth client ID**.
3. Select Application type: **Web application**.
4. Set Name: `Gemini Enterprise MCP Extension`.
5. Under **Authorized redirect URIs**, add both of the following authoritative redirect URIs:
   - `https://vertexaisearch.cloud.google.com/oauth-redirect`
   - `https://vertexaisearch.cloud.google.com/static/oauth/oauth.html`
6. Click **Create** and copy your **Client ID** and **Client Secret**.

#### 2. Fill in Gemini Enterprise Extension Form

| Field | Value / Description | Example |
| :--- | :--- | :--- |
| **MCP Server URL** | Your deployed StreamableHTTP or SSE endpoint URL | `https://mcp-demo-sei.aidemo.space/mcp` *(or `/sse`)* |
| **Authorization URL** | Google OAuth 2.0 Authorization Endpoint | `https://accounts.google.com/o/oauth2/v2/auth` |
| **Authorization URL Parameters** | Offline access & consent prompt query params | `&access_type=offline&prompt=consent` |
| **Token URL** | Google OAuth 2.0 Token Exchange Endpoint | `https://oauth2.googleapis.com/token` |
| **Client ID** | OAuth 2.0 Client ID from GCP Credentials | `xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.apps.googleusercontent.com` |
| **Client Secret** | OAuth 2.0 Client Secret from GCP Credentials | `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx` |
| **Scopes** | Space-separated list of OAuth scopes | `openid email profile` |

3. Click **Validate / Save**. Gemini Enterprise connects to `/mcp`, performs protocol discovery, and registers all actions (`calculate`, `get_system_info`, `echo`).

---

### Step 4: Verify in Gemini Enterprise Chat

Once registered, users can invoke the MCP tools directly from Gemini Enterprise chat prompts:
- *"What is the server system status?"* &rarr; invokes `get_system_info`
- *"Calculate 42 multiplied by 18"* &rarr; invokes `calculate`
- *"Echo test message"* &rarr; invokes `echo`

---

## Local Development & Testing

### 1. Install & Run Locally

```bash
# Install dependencies
npm install

# Run with hot-reload
npm run dev
```

### 2. Verify Endpoints with `curl`

- **Health Check**:
  ```bash
  curl -i http://localhost:3000/health
  ```

- **SSE Stream with Google OAuth Access Token**:
  ```bash
  curl -N -i -H "Authorization: Bearer $(gcloud auth print-access-token)" http://localhost:3000/sse
  ```

- **Testing with Authentication Disabled (Local Only)**:
  ```bash
  REQUIRE_AUTH=false npm run dev
  curl -N -i http://localhost:3000/sse
  ```

---

## Built-in Actions & Tools Reference

Actions are registered in [`src/mcp.ts`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/mcp.ts) using [`server.registerTool(...)`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/mcp.ts#L14-L105):

| Action Name | Display Title | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `calculate` | **Calculate** | `operation: string`, `a: number`, `b: number` | Performs arithmetic calculations (addition, subtraction, multiplication, division). |
| `get_system_info` | **Get System Info** | None | Returns server health status, Node.js version, uptime, and environment. |
| `echo` | **Echo Message** | `message: string` | Echoes the input message back to the client. |

---

## Adding Custom Tools

To add new tools for Gemini Enterprise, edit [`src/mcp.ts`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/mcp.ts) and register them with [`server.registerTool`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/src/mcp.ts#L14-L96):

```typescript
import { z } from "zod";

server.registerTool(
  "lookup_customer",
  {
    title: "Lookup Customer",
    description: "Lookup customer details by account ID",
    inputSchema: {
      customerId: z.string().describe("The unique customer account ID"),
    },
  },
  async ({ customerId }) => {
    // Custom business logic / database query
    const data = { id: customerId, name: "Acme Corp", tier: "Enterprise" };

    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  }
);
```

After updating tools, redeploy to Cloud Run:
```bash
gcloud run deploy sei-mcp-server --source .
```

---

## Troubleshooting

- **`401 Unauthorized` / `403 Forbidden`**:
  - `401 Unauthorized`: Missing `Authorization: Bearer <token>` header in the request.
  - `403 Forbidden`: The OAuth 2.0 token is invalid, expired, or failed audience verification against `OAUTH_CLIENT_ID`. Verify that the OAuth client credentials in Gemini Enterprise match the GCP project settings.
- **Connection Timeout**:
  Ensure the Cloud Run service `--timeout` is set to `300` seconds or higher to support long-lived Server-Sent Events connections.
- **Health Check Endpoint**:
  Load balancers and cloud probes can monitor `/health` (unauthenticated, returns HTTP `200 OK`).

---

## License

This project is licensed under the [MIT License](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/LICENSE).

