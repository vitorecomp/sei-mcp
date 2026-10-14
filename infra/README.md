# Infrastructure: GCP Load Balancer for Cloud Run SEI MCP Server

This directory contains Terraform code to provision a Google Cloud **External Application Load Balancer** fronting the **Cloud Run** SEI MCP Server via a **Serverless Network Endpoint Group (NEG)**.

---

## Architecture Overview

```text
[Gemini Enterprise / MCP Client]
              │
              ▼
  [Global Static IP Address]
              │
              ▼
 [GCP External HTTP(S) Load Balancer]
              │
              ▼
[Serverless NEG (southamerica-east1)]
              │
              ▼
     [GCP Cloud Run Service]
              │
              ▼
 [SEI SOAP Web Services (SeiWS)]
```

---

## Prerequisites

1. [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) (>= 1.5.0 installed).
2. [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) authenticated:
   ```bash
   gcloud auth application-default login
   ```
3. An existing Cloud Run service (deployed via `gcloud` or `cloudbuild.yaml`).

---

## Deployment Instructions

1. **Initialize Terraform**:
   ```bash
   cd infra
   terraform init
   ```

2. **Configure Variables**:
   Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
   Edit `terraform.tfvars` and set your `project_id` and `cloud_run_service_name`.

3. **Preview Infrastructure**:
   ```bash
   terraform plan
   ```

4. **Apply Infrastructure**:
   ```bash
   terraform apply
   ```

5. **Retrieve External IP and Endpoints**:
   Terraform will output the Load Balancer IP (`load_balancer_ip`), StreamableHTTP endpoint (`mcp_http_endpoint` / `mcp_https_endpoint`), and SSE endpoint (`mcp_sse_endpoint_http` / `mcp_sse_endpoint_https`).

---

## Note on SEI Server IP Whitelisting (`Servidores`)

According to the SEI Web Services v3.1 specification (Section 1.3 — *Cadastrar um novo serviço para o sistema*), SEI validates the source IP/hostname of the client calling `controlador_ws.php?servico=sei` against the **Servidores** list registered in `Administração > Sistemas > Serviços`.
If your SEI instance restricts incoming connections by IP in production (instead of `*`), attach a **Direct VPC Egress** + **Cloud NAT with a static external IP** to your Cloud Run service and register that Cloud NAT IP in the SEI service configuration.

---

## Outputs

- `load_balancer_ip`: External static IP allocated to the Load Balancer.
- `mcp_http_endpoint`: StreamableHTTP endpoint URL (HTTP).
- `mcp_https_endpoint`: StreamableHTTP endpoint URL (HTTPS, when SSL is enabled).
- `mcp_sse_endpoint_http`: Full SSE endpoint URL (HTTP) to configure in **Gemini Enterprise**.
- `mcp_sse_endpoint_https`: Full SSE endpoint URL (HTTPS, when SSL is enabled) to configure in **Gemini Enterprise**.
