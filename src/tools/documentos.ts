import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { getSeiClient, SeiClient } from "../client/sei-client.js";

/**
 * Registers all Document-related tools for SEI (sei-documentos API)
 */
export function registerDocumentosTools(server: McpServer): void {
  const client = getSeiClient();

  const ParticipantSchema = z.object({
    idContato: z.string().optional().describe("Identificador do participante"),
    cpf: z.string().optional().describe("CPF do participante"),
    cnpj: z.string().optional().describe("CNPJ do participante em formato alfanumérico"),
    sigla: z.string().optional().describe("Sigla do participante"),
    nome: z.string().optional().describe("Nome do participante"),
  });

  const CampoSchema = z.object({
    nome: z.string().describe("Nome do campo do formulário"),
    valor: z.string().describe("Valor do campo do formulário"),
  });

  // 1. Incluir Documento
  server.registerTool(
    "sei_incluir_documento",
    {
      title: "Incluir Documento no Processo (SEI)",
      description:
        "Inclui um novo documento gerado (Tipo G com conteúdo HTML em base64 ou texto claro) ou documento externo/recebido (Tipo R com idArquivo previamente enviado via upload ou anexo) em um processo do SEI.",
      inputSchema: {
        tipo: z
          .enum(["G", "R"])
          .describe(
            "G = Documento Gerado (HTML criado diretamente no SEI) | R = Documento Recebido/Externo (PDF/upload)"
          ),
        protocoloProcedimento: z
          .string()
          .optional()
          .describe("Número do processo onde o documento será inserido (ex: 12.1.000000077-4)"),
        idProcedimento: z
          .string()
          .optional()
          .describe("ID interno do processo (opcional se protocoloProcedimento for informado)"),
        idSerie: z
          .string()
          .describe("Identificador do tipo de documento / série (obtido via sei_listar_series)"),
        numero: z
          .string()
          .optional()
          .describe(
            "Número do documento. Obrigatório para documentos externos; para gerados, informar apenas se numeração for manual."
          ),
        nomeArvore: z
          .string()
          .optional()
          .describe("Nome complementar a ser exibido na árvore de documentos do processo"),
        data: z
          .string()
          .optional()
          .describe("Data do documento (DD/MM/AAAA) - obrigatório para documentos externos"),
        descricao: z
          .string()
          .optional()
          .describe("Descrição do documento (para documentos gerados)"),
        idTipoConferencia: z
          .string()
          .optional()
          .describe("ID do tipo de conferência associada (para documentos externos)"),
        sinArquivamento: z
          .enum(["S", "N"])
          .optional()
          .default("N")
          .describe("S/N - Indica se o documento deve ser arquivado"),
        remetente: ParticipantSchema.optional().describe("Dados do remetente"),
        interessados: z
          .array(ParticipantSchema)
          .optional()
          .describe("Lista de interessados no documento"),
        destinatarios: z
          .array(ParticipantSchema)
          .optional()
          .describe("Lista de destinatários"),
        observacao: z
          .string()
          .optional()
          .describe("Texto da observação da unidade"),
        nomeArquivo: z
          .string()
          .optional()
          .describe("Nome do arquivo (obrigatório para documentos externos, ex: 'relatorio.pdf')"),
        nivelAcesso: z
          .enum(["0", "1", "2"])
          .optional()
          .describe("0 = Público, 1 = Restrito, 2 = Sigiloso. Se omitido, assume o padrão do processo."),
        idHipoteseLegal: z
          .string()
          .optional()
          .describe("ID da hipótese legal associada (obrigatório se nivelAcesso for 1)"),
        conteudo: z
          .string()
          .optional()
          .describe(
            "Conteúdo do documento. Pode ser passado como string HTML/texto (será convertido para Base64 automaticamente caso não seja Base64) ou Base64 direto."
          ),
        idArquivo: z
          .string()
          .optional()
          .describe("Identificador do arquivo externo obtido através do serviço sei_upload_arquivo"),
        campos: z
          .array(CampoSchema)
          .optional()
          .describe("Campos associados ao formulário do documento"),
        sinBloqueado: z
          .enum(["S", "N"])
          .optional()
          .default("N")
          .describe("S/N - Se 'S', bloqueia o documento contra alterações e exclusão"),
      },
    },
    async (args) => {
      let base64Content = args.conteudo;
      if (base64Content) {
        // Check if already valid base64, otherwise encode it
        const isBase64 =
          /^[A-Za-z0-9+/=]+$/.test(base64Content.replace(/\s/g, "")) &&
          base64Content.length % 4 === 0;
        if (!isBase64) {
          base64Content = SeiClient.toBase64(base64Content);
        }
      }

      const body: any = {
        tipo: args.tipo,
        idProcedimento: args.idProcedimento,
        protocoloProcedimento: args.protocoloProcedimento,
        idSerie: args.idSerie,
        numero: args.numero,
        nomeArvore: args.nomeArvore,
        data: args.data,
        descricao: args.descricao,
        idTipoConferencia: args.idTipoConferencia,
        sinArquivamento: args.sinArquivamento,
        remetente: args.remetente
          ? {
              IdContato: args.remetente.idContato,
              Cpf: args.remetente.cpf,
              Cnpj: args.remetente.cnpj,
              sigla: args.remetente.sigla,
              nome: args.remetente.nome,
            }
          : undefined,
        interessados: args.interessados?.map((i) => ({
          IdContato: i.idContato,
          Cpf: i.cpf,
          Cnpj: i.cnpj,
          sigla: i.sigla,
          nome: i.nome,
        })),
        destinatarios: args.destinatarios?.map((d) => ({
          IdContato: d.idContato,
          Cpf: d.cpf,
          Cnpj: d.cnpj,
          sigla: d.sigla,
          nome: d.nome,
        })),
        observacao: args.observacao,
        nomeArquivo: args.nomeArquivo,
        nivelAcesso: args.nivelAcesso,
        idHipoteseLegal: args.idHipoteseLegal,
        conteudo: base64Content,
        idArquivo: args.idArquivo,
        campos: args.campos,
        sinBloqueado: args.sinBloqueado,
      };

      const data = await client.request({
        service: "documentos",
        path: "/documentos",
        method: "POST",
        body,
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }
  );

  // 2. Consultar Documento
  server.registerTool(
    "sei_consultar_documento",
    {
      title: "Consultar Metadados do Documento (SEI)",
      description:
        "Busca informações detalhadas de um documento no SEI (andamentos, assinaturas, publicações e campos).",
      inputSchema: {
        protocoloDocumento: z
          .string()
          .describe("Identificador / número do documento (ex: 0003934 ou ID interno)"),
        retornarAndamento: z
          .enum(["S", "N"])
          .optional()
          .default("N")
          .describe("S/N - Retorna histórico/andamento de geração"),
        retornarAssinaturas: z
          .enum(["S", "N"])
          .optional()
          .default("N")
          .describe("S/N - Retorna assinaturas do documento"),
        retornarpublicacao: z
          .enum(["S", "N"])
          .optional()
          .default("N")
          .describe("S/N - Retorna dados de publicação"),
        retornarCampos: z
          .enum(["S", "N"])
          .optional()
          .default("N")
          .describe("S/N - Retorna campos do formulário"),
      },
    },
    async (args) => {
      const { protocoloDocumento, ...params } = args;
      const clean = encodeURIComponent(protocoloDocumento);
      const data = await client.request({
        service: "documentos",
        path: `/documentos/${clean}`,
        method: "GET",
        params,
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }
  );

  // 3. Excluir Documento
  server.registerTool(
    "sei_excluir_documento",
    {
      title: "Excluir Documento (SEI)",
      description: "Exclui um documento do SEI (se ainda não assinado/bloqueado).",
      inputSchema: {
        protocoloDocumento: z.string().describe("Identificador / protocolo do documento a excluir"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloDocumento);
      const data = await client.request({
        service: "documentos",
        path: `/documentos/${clean}`,
        method: "DELETE",
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }
  );

  // 4. Cancelar Documento
  server.registerTool(
    "sei_cancelar_documento",
    {
      title: "Cancelar Documento (SEI)",
      description: "Cancela um documento formalmente no SEI com justificativa.",
      inputSchema: {
        protocoloDocumento: z.string().describe("Identificador do documento a cancelar"),
        motivo: z.string().describe("Motivo do cancelamento"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloDocumento);
      const data = await client.request({
        service: "documentos",
        path: `/documentos/${clean}/cancelamento`,
        method: "PUT",
        params: {
          motivo: args.motivo,
        },
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }
  );

  // 5. Obter Conteúdo do Documento
  server.registerTool(
    "sei_obter_conteudo_documento",
    {
      title: "Obter Conteúdo do Documento em Base64 / Texto (SEI)",
      description:
        "Consulta e recupera o conteúdo de um documento do SEI em Base64, fornecendo também a decodificação em texto UTF-8.",
      inputSchema: {
        protocoloFormatado: z
          .string()
          .describe("Identificador do documento formatado (ex: 00000396)"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloFormatado);
      const data = await client.request<{ idDocumento: string; conteudo: string }>({
        service: "documentos",
        path: `/documentos/${clean}/conteudo`,
        method: "GET",
      });

      let decodedText: string | null = null;
      try {
        if (data.conteudo) {
          decodedText = SeiClient.fromBase64(data.conteudo);
        }
      } catch {
        decodedText = null;
      }

      const result = {
        ...data,
        conteudoDecodificadoUtf8: decodedText,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    }
  );

  // 6. Download Anexo do Documento
  server.registerTool(
    "sei_download_anexo_documento",
    {
      title: "Download de Arquivo Anexo do Documento (SEI)",
      description: "Faz o download do arquivo anexo binário (PDF) de um documento no SEI em Base64.",
      inputSchema: {
        protocoloFormatado: z
          .string()
          .describe("Identificador do documento formatado (ex: 00000396)"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloFormatado);
      const data = await client.request({
        service: "documentos",
        path: `/documentos/${clean}/anexos`,
        method: "GET",
        responseType: "binary",
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                protocoloFormatado: args.protocoloFormatado,
                contentType: data.contentType,
                contentDisposition: data.contentDisposition,
                sizeBytes: data.sizeBytes,
                base64Preview: data.base64 ? `${data.base64.substring(0, 100)}...` : "",
                base64: data.base64,
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // 7. Upload de Arquivo Anexo (Inicial / < 10MB)
  server.registerTool(
    "sei_upload_arquivo",
    {
      title: "Upload de Arquivo Anexo (SEI)",
      description:
        "Envia um arquivo anexo externo (ex: PDF até 10MB) para o SEI. Retorna o 'idArquivo' que deve ser utilizado no campo idArquivo de sei_incluir_documento. O hash MD5 e tamanho são calculados automaticamente se não informados.",
      inputSchema: {
        nome: z.string().describe("Nome do arquivo com extensão (ex: 'edital_2026.pdf')"),
        conteudoBase64: z
          .string()
          .describe("Conteúdo do arquivo codificado em Base64 (ou texto cru a ser codificado)"),
        tamanho: z
          .string()
          .optional()
          .describe("Tamanho total em bytes (calculado automaticamente se omitido)"),
        hash: z
          .string()
          .optional()
          .describe("Hash MD5 do conteúdo total (calculado automaticamente se omitido)"),
      },
    },
    async (args) => {
      let b64 = args.conteudoBase64;
      const isBase64 =
        /^[A-Za-z0-9+/=]+$/.test(b64.replace(/\s/g, "")) && b64.length % 4 === 0;
      if (!isBase64) {
        b64 = SeiClient.toBase64(b64);
      }

      const buffer = Buffer.from(b64, "base64");
      const calculatedSize = buffer.length.toString();
      const calculatedHash = SeiClient.calculateMd5(buffer);

      const body = {
        nome: args.nome,
        tamanho: args.tamanho || calculatedSize,
        hash: args.hash || calculatedHash,
        conteudo: b64,
      };

      const data = await client.request({
        service: "documentos",
        path: "/arquivos",
        method: "POST",
        body,
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }
  );

  // 8. Upload de Arquivo em Partes (> 10MB)
  server.registerTool(
    "sei_upload_arquivo_conteudo",
    {
      title: "Upload de Partes Subsequentes de Arquivo (> 10MB) (SEI)",
      description:
        "Envia partes subsequentes (até 5MB cada) de um arquivo grande para complementar o upload iniciado em sei_upload_arquivo.",
      inputSchema: {
        idArquivo: z
          .string()
          .describe("ID do arquivo obtido no upload da primeira parte (sei_upload_arquivo)"),
        conteudoBase64: z
          .string()
          .describe("Conteúdo da parte atual em Base64"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "documentos",
        path: "/arquivos/conteudo",
        method: "POST",
        body: {
          idArquivo: args.idArquivo,
          conteudo: args.conteudoBase64,
        },
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }
  );

  // 9. Enviar E-mail a partir do Processo
  server.registerTool(
    "sei_enviar_email",
    {
      title: "Enviar E-mail pelo SEI",
      description:
        "Envia e-mail oficial a partir de um processo do SEI, com anexos selecionados dos documentos do processo.",
      inputSchema: {
        protocoloProcedimento: z
          .string()
          .describe("Número do processo visível para o usuário (ex: 12.1.000000077-4)"),
        de: z.string().describe("Endereço de e-mail do remetente"),
        para: z
          .string()
          .describe("Endereços de destinatários separados por ponto e vírgula ';'"),
        cco: z
          .string()
          .optional()
          .describe("Endereços em cópia oculta separados por ponto e vírgula ';'"),
        assunto: z.string().describe("Assunto da mensagem"),
        mensagem: z.string().describe("Conteúdo do corpo da mensagem"),
        idDocumentos: z
          .array(z.string())
          .optional()
          .describe("Lista de IDs internos dos documentos do processo a serem anexados"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "documentos",
        path: "/emails",
        method: "POST",
        body: {
          protocoloProcedimento: args.protocoloProcedimento,
          de: args.de,
          para: args.para,
          cco: args.cco || "",
          assunto: args.assunto,
          mensagem: args.mensagem,
          idDocumentos: args.idDocumentos || [],
        },
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }
  );
}
