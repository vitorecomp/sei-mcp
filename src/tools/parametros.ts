import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { getSeiClient } from "../client/sei-client.js";

/**
 * Registers all Parameter and Utility tools for SEI (sei-parametros API)
 */
export function registerParametrosTools(server: McpServer): void {
  const client = getSeiClient();

  // 1. Listar Unidades
  server.registerTool(
    "sei_listar_unidades",
    {
      title: "Listar Unidades (SEI)",
      description:
        "Lista e filtra as unidades do SEI por tipo de procedimento, série documental, órgão ou paginação.",
      inputSchema: {
        idTipoProcedimento: z
          .string()
          .optional()
          .describe("ID do tipo de procedimento para filtrar unidades habilitadas"),
        idSerie: z
          .string()
          .optional()
          .describe("ID da série documental para filtrar unidades habilitadas"),
        idOrgao: z.string().optional().describe("ID do órgão"),
        siglaOrgao: z.string().optional().describe("Sigla do órgão"),
        start: z.string().optional().describe("Página inicial de paginação"),
        limit: z.string().optional().describe("Limite de registros por página"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/unidades",
        method: "GET",
        params: {
          IdTipoProcedimento: args.idTipoProcedimento,
          idSerie: args.idSerie,
          idOrgao: args.idOrgao,
          siglaOrgao: args.siglaOrgao,
          start: args.start,
          limit: args.limit,
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

  // 2. Listar Usuários
  server.registerTool(
    "sei_listar_usuarios",
    {
      title: "Listar Usuários da Unidade (SEI)",
      description: "Lista os usuários cadastrados na unidade atual ou consulta um usuário específico por ID.",
      inputSchema: {
        idUsuario: z.string().optional().describe("ID do usuário para consulta individual"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/usuarios",
        method: "GET",
        params: args,
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

  // 3. Replicar Usuário
  server.registerTool(
    "sei_replicar_usuario",
    {
      title: "Replicar Usuário (SEI)",
      description: "Replicar dados de usuário entre instâncias/unidades do SEI.",
      inputSchema: {
        idReplicacao: z.string().optional().describe("ID da replicação"),
        usuario: z
          .object({
            staOperacao: z.string().optional().describe("Status da operação"),
            idUsuario: z.string().describe("Identificador do usuário"),
            idOrigem: z.string().optional().describe("ID de origem no SIP"),
            idOrgao: z.string().optional().describe("ID do órgão"),
            sigla: z.string().describe("Sigla do usuário"),
            nome: z.string().describe("Nome do usuário"),
            cpf: z.string().optional().describe("CPF do usuário"),
            email: z.string().optional().describe("E-mail do usuário"),
            sinAtivo: z.enum(["S", "N"]).default("S").describe("S/N - Indicador se está ativo"),
          })
          .describe("Dados do usuário"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/replica-usuario",
        method: "POST",
        body: args,
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

  // 4. Listar Tipos de Conferência
  server.registerTool(
    "sei_listar_tipos_conferencia",
    {
      title: "Listar Tipos de Conferência de Documento Externo (SEI)",
      description: "Lista os tipos de conferência válidos para autenticação de documentos externos no SEI.",
    },
    async () => {
      const data = await client.request({
        service: "parametros",
        path: "/tipos-conferencia",
        method: "GET",
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

  // 5. Listar Contatos
  server.registerTool(
    "sei_listar_contatos",
    {
      title: "Listar e Pesquisar Contatos (SEI)",
      description: "Pesquisa contatos cadastrados no SEI por nome, CPF, sigla, matrícula ou tipo de contato.",
      inputSchema: {
        idTipoContato: z.string().optional().describe("ID do tipo de contato"),
        paginaRegistros: z
          .number()
          .optional()
          .describe("Quantidade de itens por página retornada"),
        paginaAtual: z.string().optional().describe("Página atual (mínimo 1)"),
        sigla: z.string().optional().describe("Sigla do usuário/contato"),
        nome: z.string().optional().describe("Nome do usuário/contato para busca"),
        cpf: z.string().optional().describe("CPF do contato para pesquisa"),
        matricula: z.string().optional().describe("Matrícula do contato"),
        idContatos: z.string().optional().describe("Lista de IDs de contatos separados por vírgula"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/contatos",
        method: "GET",
        params: args,
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

  // 6. Criar ou Atualizar Contatos
  server.registerTool(
    "sei_criar_ou_atualizar_contatos",
    {
      title: "Criar ou Atualizar Contatos (SEI)",
      description:
        "Cria novos contatos ou atualiza contatos existentes no SEI (se idContato for fornecido, realiza alteração).",
      inputSchema: {
        contatos: z
          .array(
            z.object({
              idContato: z
                .string()
                .optional()
                .describe("Se informado, realiza alteração; se omitido, realiza inclusão"),
              idTipoContato: z.string().optional().describe("ID do tipo de contato"),
              sigla: z.string().optional().describe("Sigla do contato"),
              nome: z.string().describe("Nome completo do contato"),
              nomeSocial: z.string().optional().describe("Nome social"),
              staNatureza: z
                .enum(["F", "J"])
                .optional()
                .describe("F = Pessoa Física, J = Pessoa Jurídica"),
              cpf: z.string().optional().describe("CPF sem formatação"),
              cnpj: z.string().optional().describe("CNPJ sem formatação"),
              rg: z.string().optional().describe("Número do RG"),
              orgaoExpedidor: z.string().optional().describe("Órgão expedidor do RG"),
              matricula: z.string().optional().describe("Número de matrícula"),
              matriculaOab: z.string().optional().describe("Matrícula OAB"),
              email: z.string().optional().describe("E-mail"),
              telefoneComercial: z.string().optional().describe("Telefone comercial"),
              telefoneCelular: z.string().optional().describe("Telefone celular"),
              endereco: z.string().optional().describe("Endereço"),
              complemento: z.string().optional().describe("Complemento"),
              bairro: z.string().optional().describe("Bairro"),
              idCidade: z.string().optional().describe("ID da cidade"),
              idEstado: z.string().optional().describe("ID do estado"),
              idPais: z.string().optional().describe("ID do país"),
              cep: z.string().optional().describe("CEP"),
              staGenero: z.enum(["F", "M"]).optional().describe("F = Feminino, M = Masculino"),
              idCargo: z.string().optional().describe("ID do cargo"),
              expressaoCargo: z.string().optional().describe("Descrição do cargo"),
              observacao: z.string().optional().describe("Observações"),
              sinAtivo: z.enum(["S", "N"]).default("S").describe("S/N - Indicador se ativo"),
            })
          )
          .describe("Lista de contatos a serem criados/atualizados"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/contatos",
        method: "POST",
        body: args.contatos,
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

  // 7. Excluir / Desativar / Reativar Contato
  server.registerTool(
    "sei_excluir_desativar_contato",
    {
      title: "Excluir, Desativar ou Reativar Contato (SEI)",
      description: "Executa operação de exclusão, desativação ou reativação de um contato.",
      inputSchema: {
        idContato: z.string().describe("ID do contato"),
        staOperacao: z
          .enum(["E", "D", "R"])
          .describe("E = Exclusão, D = Desativação, R = Reativação"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.idContato);
      const data = await client.request({
        service: "parametros",
        path: `/contatos/${clean}`,
        method: "DELETE",
        params: {
          staOperacao: args.staOperacao,
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

  // 8. Consultar Bloco
  server.registerTool(
    "sei_consultar_bloco",
    {
      title: "Consultar Bloco de Assinatura / Interno (SEI)",
      description: "Consulta informações e documentos de um bloco no SEI.",
      inputSchema: {
        idBloco: z.string().describe("ID do bloco"),
        sinRetornarProtocolos: z
          .enum(["S", "N"])
          .default("N")
          .describe("S/N - Retorna os processos e documentos incluídos no bloco"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.idBloco);
      const data = await client.request({
        service: "parametros",
        path: `/blocos/${clean}`,
        method: "GET",
        params: {
          sinRetornarProtocolos: args.sinRetornarProtocolos,
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

  // 9. Excluir Bloco
  server.registerTool(
    "sei_excluir_bloco",
    {
      title: "Excluir Bloco (SEI)",
      description: "Exclui um bloco no SEI.",
      inputSchema: {
        idBloco: z.string().describe("ID do bloco"),
        sinRetornarProtocolos: z.enum(["S", "N"]).default("N").describe("S/N"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.idBloco);
      const data = await client.request({
        service: "parametros",
        path: `/blocos/${clean}`,
        method: "DELETE",
        params: {
          sinRetornarProtocolos: args.sinRetornarProtocolos,
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

  // 10. Disponibilizar Bloco
  server.registerTool(
    "sei_disponibilizar_bloco",
    {
      title: "Disponibilizar Bloco para Outras Unidades (SEI)",
      description: "Disponibiliza um bloco de assinatura para as unidades configuradas.",
      inputSchema: {
        idBloco: z.string().describe("ID do bloco"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.idBloco);
      const data = await client.request({
        service: "parametros",
        path: `/blocos/${clean}/disponibilizacao`,
        method: "POST",
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

  // 11. Cancelar Disponibilização de Bloco
  server.registerTool(
    "sei_cancelar_disponibilizacao_bloco",
    {
      title: "Cancelar Disponibilização de Bloco (SEI)",
      description: "Cancela a disponibilização de um bloco.",
      inputSchema: {
        idBloco: z.string().describe("ID do bloco"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.idBloco);
      const data = await client.request({
        service: "parametros",
        path: `/blocos/${clean}/disponibilizacao`,
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

  // 12. Incluir Documento em Bloco
  server.registerTool(
    "sei_incluir_documento_bloco",
    {
      title: "Incluir Documento em Bloco (SEI)",
      description: "Inclui um documento em um bloco com anotação opcional.",
      inputSchema: {
        idBloco: z.string().describe("ID do bloco"),
        protocoloDocumento: z.string().describe("Identificador do documento"),
        anotacao: z.string().optional().describe("Texto de anotação no bloco"),
      },
    },
    async (args) => {
      const cleanBloco = encodeURIComponent(args.idBloco);
      const cleanDoc = encodeURIComponent(args.protocoloDocumento);
      const data = await client.request({
        service: "parametros",
        path: `/blocos/${cleanBloco}/documentos/${cleanDoc}`,
        method: "POST",
        body: {
          anotacao: args.anotacao || "",
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

  // 13. Remover Documento de Bloco
  server.registerTool(
    "sei_remover_documento_bloco",
    {
      title: "Remover Documento de Bloco (SEI)",
      description: "Remove um documento de um bloco.",
      inputSchema: {
        idBloco: z.string().describe("ID do bloco"),
        protocoloDocumento: z.string().describe("Identificador do documento"),
      },
    },
    async (args) => {
      const cleanBloco = encodeURIComponent(args.idBloco);
      const cleanDoc = encodeURIComponent(args.protocoloDocumento);
      const data = await client.request({
        service: "parametros",
        path: `/blocos/${cleanBloco}/documentos/${cleanDoc}`,
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

  // 14. Incluir Processo em Bloco
  server.registerTool(
    "sei_incluir_processo_bloco",
    {
      title: "Incluir Processo em Bloco (SEI)",
      description: "Inclui um processo completo em um bloco.",
      inputSchema: {
        idBloco: z.string().describe("ID do bloco"),
        protocoloProcedimento: z.string().describe("Número do processo"),
        anotacao: z.string().optional().describe("Texto de anotação no bloco"),
      },
    },
    async (args) => {
      const cleanBloco = encodeURIComponent(args.idBloco);
      const cleanProc = encodeURIComponent(args.protocoloProcedimento);
      const data = await client.request({
        service: "parametros",
        path: `/blocos/${cleanBloco}/processos/${cleanProc}`,
        method: "POST",
        body: {
          anotacao: args.anotacao || "",
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

  // 15. Remover Processo de Bloco
  server.registerTool(
    "sei_remover_processo_bloco",
    {
      title: "Remover Processo de Bloco (SEI)",
      description: "Remove um processo de um bloco.",
      inputSchema: {
        idBloco: z.string().describe("ID do bloco"),
        protocoloProcedimento: z.string().describe("Número do processo"),
      },
    },
    async (args) => {
      const cleanBloco = encodeURIComponent(args.idBloco);
      const cleanProc = encodeURIComponent(args.protocoloProcedimento);
      const data = await client.request({
        service: "parametros",
        path: `/blocos/${cleanBloco}/processos/${cleanProc}`,
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

  // 16. Listar Séries Documentais
  server.registerTool(
    "sei_listar_series",
    {
      title: "Listar Séries / Tipos de Documento (SEI)",
      description:
        "Lista os tipos de documento (séries) cadastrados no SEI, com indicação de aplicabilidade (T=Internos e Externos, I=Internos, E=Externos, F=Formulários).",
      inputSchema: {
        idTipoProcedimento: z
          .number()
          .optional()
          .describe("ID do tipo de procedimento para filtrar séries vinculadas"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/series",
        method: "GET",
        params: args,
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

  // 17. Listar Hipóteses Legais
  server.registerTool(
    "sei_listar_hipoteses_legais",
    {
      title: "Listar Hipóteses Legais de Sigilo / Restrição (SEI)",
      description: "Lista as hipóteses legais cadastradas no SEI para processos ou documentos restritos/sigilosos.",
      inputSchema: {
        nivelAcesso: z
          .number()
          .optional()
          .describe("1 = Restrito, 2 = Sigiloso"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/hipoteses",
        method: "GET",
        params: args,
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

  // 18. Listar Assuntos
  server.registerTool(
    "sei_listar_assuntos",
    {
      title: "Listar e Pesquisar Assuntos (SEI)",
      description: "Pesquisa assuntos de classificação arquivística no SEI por palavras-chave.",
      inputSchema: {
        palavrasPesquisa: z.string().optional().describe("Palavras-chave para busca"),
        idAssunto: z.string().optional().describe("ID do assunto para detalhamento"),
        start: z.string().optional().describe("Página inicial"),
        limit: z.string().optional().describe("Limite de registros"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/assuntos",
        method: "GET",
        params: args,
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

  // 19. Listar Textos Padrão
  server.registerTool(
    "sei_listar_textos_padrao",
    {
      title: "Listar Textos Padrão da Unidade (SEI)",
      description: "Lista modelos de textos padrão cadastrados na unidade.",
      inputSchema: {
        palavrasPesquisa: z.string().optional().describe("Palavras-chave para filtro"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/textos-padrao",
        method: "GET",
        params: args,
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

  // 20. Consultar Conteúdo do Texto Padrão
  server.registerTool(
    "sei_consultar_texto_padrao",
    {
      title: "Consultar Conteúdo de Texto Padrão (SEI)",
      description: "Retorna o conteúdo completo de um modelo de texto padrão por ID.",
      inputSchema: {
        idTextoPadrao: z.string().describe("ID do texto padrão"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.idTextoPadrao);
      const data = await client.request({
        service: "parametros",
        path: `/textos-padrao/${clean}`,
        method: "GET",
      });

      return {
        content: [
          {
            type: "text",
            text: typeof data === "string" ? data : JSON.stringify(data, null, 2),
          },
        ],
      };
    }
  );

  // 21. Listar Cargos
  server.registerTool(
    "sei_listar_cargos",
    {
      title: "Listar Cargos (SEI)",
      description: "Lista os cargos cadastrados no SEI com expressões de tratamento e vocativo.",
      inputSchema: {
        idCargo: z.number().optional().describe("ID do cargo"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/cargos",
        method: "GET",
        params: args,
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

  // 22. Listar Países
  server.registerTool(
    "sei_listar_paises",
    {
      title: "Listar Países (SEI)",
      description: "Lista os países cadastrados no SEI.",
    },
    async () => {
      const data = await client.request({
        service: "parametros",
        path: "/paises",
        method: "GET",
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

  // 23. Listar Estados
  server.registerTool(
    "sei_listar_estados",
    {
      title: "Listar Estados de um País (SEI)",
      description: "Lista os estados a partir do ID de um país.",
      inputSchema: {
        idPais: z.number().describe("ID do país"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/estados",
        method: "GET",
        params: args,
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

  // 24. Listar Cidades
  server.registerTool(
    "sei_listar_cidades",
    {
      title: "Listar Cidades de um Estado (SEI)",
      description: "Lista as cidades a partir do ID de um país e ID de um estado.",
      inputSchema: {
        idPais: z.number().describe("ID do país"),
        idEstado: z.number().describe("ID do estado"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/cidades",
        method: "GET",
        params: args,
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

  // 25. Listar Feriados
  server.registerTool(
    "sei_listar_feriados",
    {
      title: "Listar Feriados do Órgão (SEI)",
      description: "Lista feriados cadastrados para um órgão em um intervalo de datas.",
      inputSchema: {
        idOrgao: z.number().describe("ID do órgão"),
        dataInicial: z.number().describe("Data inicial para filtro (numérico ou timestamp)"),
        dataFinal: z.number().describe("Data final para filtro (numérico ou timestamp)"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/feriados",
        method: "GET",
        params: args,
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

  // 26. Listar Extensões de Arquivo Permitidas
  server.registerTool(
    "sei_listar_extensoes_permitidas",
    {
      title: "Listar Extensões de Arquivo Permitidas para Upload (SEI)",
      description: "Lista as extensões de arquivos autorizadas para anexo no SEI.",
      inputSchema: {
        idArquivoExtensao: z.number().optional().describe("ID da extensão para filtro"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "parametros",
        path: "/extensoes",
        method: "GET",
        params: args,
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
