# SEI MCP Server for Gemini Enterprise

A production-ready **Model Context Protocol (MCP)** server built with **Node.js**, **Express**, and **TypeScript** providing full integration with the **SEI (Sistema Eletrônico de Informações)** APIs of the São Paulo State Government (**IntegradorSP / Rota.SP**).

Equipped with dual transports (**StreamableHTTP** on `/mcp` and **SSE** on `/sse`), Google OAuth 2.0 discovery endpoints, automated IDP.SP token management, and comprehensive tools for **Gemini Enterprise**, Claude, and MCP clients.

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Gemini Enterprise                             │
│                  (Admin Console / Extensions / Tools)                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                 HTTPS / SSE Request with Google OAuth Bearer Token
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
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│      GET /health      │  │      POST /mcp      │  │     GET /sse &      │
│(Unauthenticated Probe)│  │  (StreamableHTTP)   │  │   POST /messages    │
└───────────────────────┘  └──────────┬──────────┘  └──────────┬──────────┘
                                      │                        │
                                      ▼                        ▼
                       ┌──────────────────────────────────────────────┐
                       │                SEI Client                    │
                       │ (IDP.SP OAuth Auth Gate + Request Headers)   │
                       └──────┬───────────────┬──────────────┬────────┘
                              │               │              │
                              ▼               ▼              ▼
                   ┌──────────────────┐ ┌───────────┐ ┌───────────────┐
                   │  sei-processos   │ │sei-docum. │ │sei-parametros │
                   │(Gestão Processos)│ │(Documentos│ │(Unidades,     │
                   │                  │ │ e Anexos) │ │Contatos,etc.) │
                   └──────────────────┘ └───────────┘ └───────────────┘
```

---

## 📋 Prerequisites

- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and authenticated.
- [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) (>= 1.5.0).
- [Node.js](https://nodejs.org/) (v20.x or v22.x LTS) & npm (for local development).
- A Google Cloud Project with billing enabled and the following APIs activated:
  ```bash
  gcloud services enable run.googleapis.com compute.googleapis.com cloudbuild.googleapis.com
  ```
- SEI Credentials (IDP.SP client credentials / token, SiglaSistema, Identificação de Serviço, ID Unidade).

---

## ⚙️ Configuration & Environment Variables

Configure server behavior and SEI integration parameters in `.env` (refer to [`.env.example`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/.env.example)):

### Server & Security Settings

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | Listening port for the application | `3000` |
| `HOST` | Binding network address | `0.0.0.0` |
| `NODE_ENV` | Environment mode (`production`, `development`, `dev`) | `production` |
| `OAUTH_ENABLED` | When set to `true`, enforces Google OAuth 2.0 token verification on `tools/call`. Default is enabled in `production`. | `false` (dev) / `true` (prod) |
| `OAUTH_CLIENT_ID` | Google OAuth 2.0 Client ID for audience verification | *(none)* |

### SEI APIs & IDP.SP Authentication

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `SEI_PROCESSOS_URL` | Base URL for `sei-processos` API | `https://sei-processos.api-hml.rota.sp.gov.br` |
| `SEI_DOCUMENTOS_URL` | Base URL for `sei-documentos` API | `https://sei-documentos.api-hml.rota.sp.gov.br` |
| `SEI_PARAMETROS_URL` | Base URL for `sei-parametros` API | `https://sei-parametros.api-hml.rota.sp.gov.br` |
| `IDPSP_TOKEN_URL` | IDP.SP OAuth 2.0 token exchange endpoint | `https://rhsso.idp-hml.sp.gov.br/auth/realms/idpsp/protocol/openid-connect/token` |
| `IDPSP_CLIENT_ID` | IDP.SP Client ID for automated token generation | `your-idpsp-client-id` |
| `IDPSP_CLIENT_SECRET` | IDP.SP Client Secret | `your-idpsp-client-secret` |
| `SEI_BEARER_TOKEN` | Static JWT Bearer Token (alternative to client credentials) | *(optional)* |
| `SEI_SIGLA_SISTEMA` | Sigla do Sistema cadastrado no SEI | `INTEGRACAOCLIENTES` |
| `SEI_IDENTIFICACAO_SERVICO` | Token / Chave de serviço cadastrada no SEI | `your-service-token-hash` |
| `SEI_ID_UNIDADE` | ID da Unidade executora no SEI | `110000384` |
| `SEI_REGIONAL` | Regional do Município (obrigatório apenas para SEI Cidades) | *(opcional)* |

---

## 🚀 Streamlined Deployment: Gemini Enterprise with Terraform

Follow these step-by-step instructions to deploy the SEI MCP server to Google Cloud and connect it to Gemini Enterprise.

### Step 1: Build & Deploy Container to Cloud Run

Build the multi-stage Docker image using Google Cloud Build and deploy it to Google Cloud Run:

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
  --set-env-vars NODE_ENV=production,OAUTH_CLIENT_ID="YOUR_OAUTH_CLIENT_ID.apps.googleusercontent.com",SEI_SIGLA_SISTEMA="INTEGRACAOCLIENTES",SEI_IDENTIFICACAO_SERVICO="YOUR_SEI_TOKEN",SEI_ID_UNIDADE="110000384",IDPSP_CLIENT_ID="YOUR_IDPSP_ID",IDPSP_CLIENT_SECRET="YOUR_IDPSP_SECRET" \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 300
```

> [!NOTE]
> - In **production** (`NODE_ENV=production`), the server enforces **Google OAuth 2.0 authentication** on all `tools/call` invocations while keeping tool discovery unblocked for seamless synchronization in Gemini Enterprise.
> - In **development** (`NODE_ENV=dev`), authentication is disabled for frictionless local testing.

---

### Step 2: Provision Load Balancer & Static IP with Terraform

Use the included Terraform module in [`infra/`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/infra/README.md) to provision an External Application Load Balancer with a Serverless NEG pointing to your Cloud Run service.

1. Navigate to the infrastructure directory:
   ```bash
   cd infra
   ```

2. Create your `terraform.tfvars`:
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

5. Retrieve the outputs:
   - `load_balancer_ip`: Static IP of the Load Balancer (e.g. `34.120.x.x`).
   - `mcp_sse_endpoint_http`: SSE endpoint URL (e.g. `http://34.120.x.x/sse` or `https://<YOUR-DOMAIN>/sse`).
   - `mcp_http_endpoint`: StreamableHTTP endpoint URL (e.g. `https://<YOUR-DOMAIN>/mcp`).

---

### Step 3: Configure Google OAuth 2.0 Credentials in GCP Console

When integrating with Gemini Enterprise, configure the OAuth 2.0 client credentials:

1. Open **Google Cloud Console** > **APIs & Services** > **Credentials**.
2. Click **Create Credentials** > **OAuth client ID**.
3. Select Application type: **Web application**.
4. Set Name: `Gemini Enterprise SEI MCP Extension`.
5. Under **Authorized redirect URIs**, add both of the following redirect URIs:
   - `https://vertexaisearch.cloud.google.com/oauth-redirect`
   - `https://vertexaisearch.cloud.google.com/static/oauth/oauth.html`
6. Click **Create** and copy your **Client ID** and **Client Secret**.

---

### Step 4: Register Extension in Gemini Enterprise

In the **Gemini Enterprise Admin Console** (or Vertex AI Extensions / Custom Tools), add a new MCP Server extension using the following values:

| Field | Value / Description | Example |
| :--- | :--- | :--- |
| **MCP Server URL** | Your deployed StreamableHTTP or SSE endpoint URL | `https://mcp-demo-sei.aidemo.space/mcp` *(or `/sse`)* |
| **Authorization URL** | Google OAuth 2.0 Authorization Endpoint | `https://accounts.google.com/o/oauth2/v2/auth` |
| **Authorization URL Parameters** | Offline access & consent prompt query params | `&access_type=offline&prompt=consent` |
| **Token URL** | Google OAuth 2.0 Token Exchange Endpoint | `https://oauth2.googleapis.com/token` |
| **Client ID** | OAuth 2.0 Client ID from GCP Credentials | `xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.apps.googleusercontent.com` |
| **Client Secret** | OAuth 2.0 Client Secret from GCP Credentials | `GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx` |
| **Scopes** | Space-separated list of OAuth scopes | `openid email profile` |

Click **Validate & Save**. Gemini Enterprise connects to the endpoint, performs protocol handshake and tool discovery, and registers all 68+ SEI tools automatically.

---

### Step 5: Verify in Gemini Enterprise Chat

Once registered, users can invoke the SEI tools naturally from Gemini Enterprise prompts:
- *"Liste os processos abertos na minha unidade no SEI"* &rarr; invokes `sei_listar_processos`
- *"Consulte o andamento do processo 03.110000147.0000001/2024-99"* &rarr; invokes `sei_consultar_processo`
- *"Crie um novo processo administrativo de Compras e Serviços"* &rarr; invokes `sei_gerar_processo`
- *"Inclua um parecer em HTML no processo"* &rarr; invokes `sei_incluir_documento`
- *"Quais são as séries documentais disponíveis?"* &rarr; invokes `sei_listar_series`
- *"Qual o status de saúde do servidor MCP?"* &rarr; invokes `get_system_info`

---

## 🛠️ Complete MCP Tools Catalog

The server exports all operations from the SEI API documentation across three domains:

### 1. Processos (`sei-processos`)

| Tool Name | Description | Key Parameters |
| :--- | :--- | :--- |
| `sei_listar_processos` | Lista a mesa de processos da unidade | `tipo` (G/R), `usuario`, `apenasMeus`, `start`, `limit` |
| `sei_consultar_processo` | Consulta processo por número de protocolo | `protocoloProcedimento`, flags de andamento/interessados/assuntos |
| `sei_gerar_processo` | Cria novo processo administrativo no SEI | `idTipoProcedimento`, `especificacao`, `nivelAcesso`, `idHipoteseLegal`, `interessados`, `assuntos` |
| `sei_excluir_processo` | Exclui um processo | `protocoloProcedimento` |
| `sei_listar_documentos_processo` | Lista todos os documentos de um processo | `protocoloProcedimento`, `start`, `limit`, `sinRetornarStatus` |
| `sei_enviar_processo` | Tramita/envia processo para outras unidades | `protocoloProcedimento`, `unidadesDestino`, `dataRetornoProgramado` |
| `sei_concluir_processo` | Conclui o processo na unidade atual | `protocoloProcedimento` |
| `sei_reabrir_processo` | Reabre um processo concluído | `protocoloProcedimento` |
| `sei_bloquear_processo` | Bloqueia processo contra alterações | `protocoloProcedimento` |
| `sei_receber_processo` | Recebe formalmente o processo na unidade | `protocoloProcedimento` |
| `sei_atribuir_processo` | Atribui responsabilidade do processo a usuário | `protocoloProcedimento`, `idUsuario`, `sinReabrir` |
| `sei_listar_atribuicoes_usuario` | Consulta processos atribuídos por CPF | `cpf`, `sinRetornarRecebidos`, `sinRetornarGerados` |
| `sei_relacionar_processos` | Cria relacionamento bilateral entre processos | `protocoloProcedimento1`, `protocoloProcedimento2` |
| `sei_remover_relacionamento_processos` | Remove relacionamento entre processos | `protocoloProcedimento1`, `protocoloProcedimento2` |
| `sei_anexar_processo` | Anexa processo secundário a um principal | `protocoloProcedimentoPrincipal`, `protocoloProcedimentoAnexado` |
| `sei_desanexar_processo` | Desanexa processo com justificativa | `protocoloProcedimentoPrincipal`, `protocoloProcedimentoAnexado`, `motivo` |
| `sei_sobrestar_processo` | Sobresta/suspende andamento do processo | `protocoloProcedimento`, `motivo`, `protocoloProcedimentoVinculado` |
| `sei_remover_sobrestamento_processo` | Remove sobrestamento do processo | `protocoloProcedimento` |
| `sei_definir_controle_prazo` | Define ou atualiza controle de prazo | `protocoloProcedimento`, `dataPrazo`, `dias`, `sinDiasUteis` |
| `sei_remover_controle_prazo` | Remove controle de prazo | `protocoloProcedimento` |
| `sei_concluir_controle_prazo` | Conclui controle de prazo | `protocoloProcedimento` |
| `sei_definir_marcador_processo` | Aplica marcador/tag colorida no processo | `protocoloProcedimento`, `idMarcador`, `texto` |
| `sei_listar_marcadores_unidade` | Lista marcadores disponíveis na unidade | *Nenhum* |
| `sei_listar_andamentos_marcadores` | Lista histórico de marcadores do processo | `protocoloProcedimento`, `marcadores` |
| `sei_alterar_nivel_acesso_processo` | Altera nível de acesso (Público/Restrito) | `protocoloProcedimento`, `nivelAcesso`, `hipotese` |
| `sei_lancar_andamento` | Insere andamento manual no histórico | `protocoloProcedimento`, `idTarefa`, `atributos` |
| `sei_listar_andamentos` | Lista andamentos do processo | `protocoloProcedimento`, `retornaAtributos`, `tarefas` |
| `sei_listar_andamentos_completo` | Consulta avançada de histórico e atividades | `protocoloProcedimento`, `tipoHistorico`, `dataInicio`, `dataFim`, `idUsuario`, `unidadeOrigem` |
| `sei_listar_tipos_processo` | Lista tipos de processos configurados | *Nenhum* |
| `sei_disponibilizar_acesso_externo` | Gera acesso externo para usuário/interessado | `protocoloProcedimento`, `emailUnidade`, `emailDestinatario`, `motivo`, `dias`, `senha` |
| `sei_listar_disponibilizacoes_acesso_externo` | Lista acessos externos de um processo | `protocoloProcedimento` |
| `sei_cancelar_disponibilizacao_acesso_externo` | Cancela acesso externo | `protocoloProcedimento`, `idAcessoExterno`, `motivo` |
| `sei_consultar_processos_individuais` | Consulta processos por usuário interessado | `idOrgaoProcedimento`, `idTipoProcedimento`, `siglaUsuario` |

---

### 2. Documentos (`sei-documentos`)

| Tool Name | Description | Key Parameters |
| :--- | :--- | :--- |
| `sei_incluir_documento` | Inclui documento gerado (HTML) ou externo (PDF) no processo | `tipo` (G/R), `protocoloProcedimento`, `idSerie`, `conteudo`, `idArquivo`, `nivelAcesso` |
| `sei_consultar_documento` | Consulta metadados de documento no SEI | `protocoloDocumento`, `retornarAndamento`, `retornarAssinaturas`, `retornarCampos` |
| `sei_excluir_documento` | Exclui documento não assinado/bloqueado | `protocoloDocumento` |
| `sei_cancelar_documento` | Cancela documento formalmente no SEI | `protocoloDocumento`, `motivo` |
| `sei_obter_conteudo_documento` | Obtém conteúdo do documento (Base64 + UTF-8) | `protocoloFormatado` |
| `sei_download_anexo_documento` | Baixa arquivo anexo binário em Base64 | `protocoloFormatado` |
| `sei_upload_arquivo` | Faz upload de arquivo anexo (< 10MB) | `nome`, `conteudoBase64` (MD5 e tamanho calculados automaticamente) |
| `sei_upload_arquivo_conteudo` | Envia partes adicionais de arquivos (> 10MB) | `idArquivo`, `conteudoBase64` |
| `sei_enviar_email` | Envia e-mail oficial com anexos do processo | `protocoloProcedimento`, `de`, `para`, `assunto`, `mensagem`, `idDocumentos` |

---

### 3. Parâmetros e Utilitários (`sei-parametros`)

| Tool Name | Description | Key Parameters |
| :--- | :--- | :--- |
| `sei_listar_unidades` | Lista e filtra unidades do SEI | `idTipoProcedimento`, `idSerie`, `idOrgao`, `start`, `limit` |
| `sei_listar_usuarios` | Lista usuários da unidade | `idUsuario` |
| `sei_replicar_usuario` | Replica usuário entre instâncias | `idReplicacao`, `usuario` |
| `sei_listar_series` | Lista séries/tipos de documento | `idTipoProcedimento` |
| `sei_listar_hipoteses_legais` | Lista hipóteses legais de sigilo/restrição | `nivelAcesso` (1=Restrito, 2=Sigiloso) |
| `sei_listar_assuntos` | Pesquisa assuntos arquivísticos | `palavrasPesquisa`, `start`, `limit` |
| `sei_listar_contatos` | Pesquisa contatos cadastrados | `nome`, `cpf`, `sigla`, `matricula`, `idTipoContato` |
| `sei_criar_ou_atualizar_contatos` | Cria ou altera contatos no SEI | `contatos` (array com dados cadastrais) |
| `sei_excluir_desativar_contato` | Exclui, desativa ou reativa contato | `idContato`, `staOperacao` (E/D/R) |
| `sei_consultar_bloco` | Consulta bloco de assinatura / interno | `idBloco`, `sinRetornarProtocolos` |
| `sei_excluir_bloco` | Exclui um bloco | `idBloco` |
| `sei_disponibilizar_bloco` | Disponibiliza bloco para outras unidades | `idBloco` |
| `sei_cancelar_disponibilizacao_bloco` | Cancela disponibilização de bloco | `idBloco` |
| `sei_incluir_documento_bloco` | Inclui documento em um bloco | `idBloco`, `protocoloDocumento`, `anotacao` |
| `sei_remover_documento_bloco` | Remove documento de um bloco | `idBloco`, `protocoloDocumento` |
| `sei_incluir_processo_bloco` | Inclui processo em um bloco | `idBloco`, `protocoloProcedimento`, `anotacao` |
| `sei_remover_processo_bloco` | Remove processo de um bloco | `idBloco`, `protocoloProcedimento` |
| `sei_listar_textos_padrao` | Lista modelos de texto padrão da unidade | `palavrasPesquisa` |
| `sei_consultar_texto_padrao` | Consulta conteúdo de texto padrão | `idTextoPadrao` |
| `sei_listar_cargos` | Lista cargos cadastrados com vocativo | `idCargo` |
| `sei_listar_paises` | Lista países cadastrados | *Nenhum* |
| `sei_listar_estados` | Lista estados por país | `idPais` |
| `sei_listar_cidades` | Lista cidades por país e estado | `idPais`, `idEstado` |
| `sei_listar_feriados` | Lista feriados de um órgão | `idOrgao`, `dataInicial`, `dataFinal` |
| `sei_listar_extensoes_permitidas` | Lista extensões de arquivo permitidas | `idArquivoExtensao` |
| `sei_listar_tipos_conferencia` | Lista tipos de conferência de documento externo | *Nenhum* |

---

## 💻 Local Development & Testing

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
  OAUTH_ENABLED=false npm run dev
  curl -N -i http://localhost:3000/sse
  ```

---

## 🔍 Troubleshooting

- **`401 Unauthorized` / `403 Forbidden`**:
  - `401 Unauthorized`: Missing `Authorization: Bearer <token>` header in the request.
  - `403 Forbidden`: The OAuth 2.0 token is invalid, expired, or failed audience verification against `OAUTH_CLIENT_ID`. Verify that the OAuth client credentials in Gemini Enterprise match the GCP project settings.
- **Connection Timeout**:
  Ensure the Cloud Run service `--timeout` is set to `300` seconds or higher to support long-lived Server-Sent Events connections.
- **Health Check Endpoint**:
  Load balancers and cloud probes can monitor `/health` (unauthenticated, returns HTTP `200 OK`).

---

## 📄 License

This project is licensed under the [MIT License](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/LICENSE).
