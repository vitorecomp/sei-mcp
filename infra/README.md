# Infrastructure: GCP Load Balancer for Cloud Run MCP Server

This directory contains Terraform code to provision a Google Cloud **External Application Load Balancer** fronting the **Cloud Run** MCP Server via a **Serverless Network Endpoint Group (NEG)**.

---

## Architecture Overview

```
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

5. **Retrieve External IP**:
   Terraform will output the Load Balancer IP (`load_balancer_ip`) and the SSE endpoint URL (`mcp_sse_endpoint_http`).

---

## Outputs

- `load_balancer_ip`: External static IP allocated to the Load Balancer.
- `mcp_sse_endpoint_http`: Full SSE endpoint URL to configure in **Gemini Enterprise**.
