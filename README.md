# SEI MCP Server (Sistema Eletrônico de Informações)

A production-ready **Model Context Protocol (MCP)** server built with **Node.js**, **Express**, and **TypeScript** providing full integration with the **SEI (Sistema Eletrônico de Informações)** APIs of the São Paulo State Government (**IntegradorSP / Rota.SP**).

Equipped with dual transports (**StreamableHTTP** on `/mcp` and **SSE** on `/sse`), OAuth 2.0 discovery endpoints, and comprehensive tools for **Gemini Enterprise**, Claude, and MCP clients.

---

## 🏛️ SEI Architecture & APIs Integrated

The server integrates with the three core SEI OpenAPI specifications located in [`sei-documentation/`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/sei-documentation):

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Gemini Enterprise / MCP Client                       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ StreamableHTTP (/mcp) or SSE (/sse)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             SEI MCP Server                              │
│         (Auth Token Management, Header Injection & Tool Handler)        │
└────────────┬───────────────────────┼───────────────────────────┬────────┘
             │                       │                           │
             ▼                       ▼                           ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│     sei-processos       │ │     sei-documentos      │ │     sei-parametros      │
│  - Listar Processos     │ │  - Incluir Documentos   │ │  - Listar Unidades      │
│  - Consultar Processo   │ │  - Consultar Documentos │ │  - Listar Usuários      │
│  - Gerar Processo       │ │  - Obter Conteúdo (B64) │ │  - Listar Contatos      │
│  - Tramitar / Enviar    │ │  - Download Anexo (PDF) │ │  - Gerenciar Blocos     │
│  - Concluir / Reabrir   │ │  - Upload de Arquivos   │ │  - Séries Documentais   │
│  - Marcadores & Prazos  │ │  - Envio de E-mails     │ │  - Hipóteses Legais     │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

---

## ⚙️ Configuration & Environment Variables

Configure your credentials in `.env` (refer to [`.env.example`](file:///usr/local/google/home/vieiravitor/workspace/opensource/sei-mcp/.env.example)):

```bash
# Server Configuration
PORT=3000
HOST=0.0.0.0
NODE_ENV=development
OAUTH_ENABLED=false

# SEI API Base URLs (IntegradorSP / Rota.SP)
SEI_PROCESSOS_URL=https://sei-processos.api-hml.rota.sp.gov.br
SEI_DOCUMENTOS_URL=https://sei-documentos.api-hml.rota.sp.gov.br
SEI_PARAMETROS_URL=https://sei-parametros.api-hml.rota.sp.gov.br

# IDP.SP Authentication (OAuth 2.0 Client Credentials or Direct Bearer Token)
IDPSP_TOKEN_URL=https://rhsso.idp-hml.sp.gov.br/auth/realms/idpsp/protocol/openid-connect/token
IDPSP_CLIENT_ID=your-idpsp-client-id
IDPSP_CLIENT_SECRET=your-idpsp-client-secret
# Or direct static token:
# SEI_BEARER_TOKEN=eyJhbGci...

# SEI Required System Headers
SEI_SIGLA_SISTEMA=INTEGRACAOCLIENTES
SEI_IDENTIFICACAO_SERVICO=your-sei-service-token-hash
SEI_ID_UNIDADE=110000384
# SEI_REGIONAL=
```

---

## 🛠️ Complete MCP Tools Catalog

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

## 🚀 Local Development & Execution

```bash
# 1. Install dependencies
npm install

# 2. Build TypeScript
npm run build

# 3. Run in Development Mode (Hot Reload)
npm run dev

# 4. Run in Production Mode
npm start
```

### Health Check:
```bash
curl http://localhost:3000/health
```

---

## ☁️ Deployment to Google Cloud Run & Gemini Enterprise

```bash
# Build and deploy with gcloud
gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/sei-mcp-server:latest .

gcloud run deploy sei-mcp-server \
  --image gcr.io/YOUR_GCP_PROJECT_ID/sei-mcp-server:latest \
  --region southamerica-east1 \
  --platform managed \
  --allow-unauthenticated \
  --port 3000
```

---

## 📄 License

MIT License.
