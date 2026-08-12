import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { getSeiClient } from "../client/sei-client.js";

/**
 * Registers all Process-related tools for SEI (sei-processos API)
 */
export function registerProcessosTools(server: McpServer): void {
  const client = getSeiClient();

  // 1. Listar Processos (Mesa de Controle de Processos da Unidade)
  server.registerTool(
    "sei_listar_processos",
    {
      title: "Listar Processos da Unidade (SEI)",
      description:
        "Lista os processos da unidade atual no SEI (equivalente à mesa de Controle de Processos). Permite filtrar por tipo (G=gerados, R=recebidos), usuário atribuído, apenasMeus, e paginar.",
      inputSchema: {
        usuario: z
          .string()
          .optional()
          .describe("ID do usuário de atribuição no SEI"),
        tipo: z
          .enum(["G", "R"])
          .optional()
          .describe("Informe 'G' para processos gerados ou 'R' para recebidos"),
        apenasMeus: z
          .enum(["S", "N"])
          .optional()
          .describe("Se 'S', retorna apenas os processos atribuídos ao usuário autenticado"),
        sinRetornarCiencias: z
          .enum(["S", "N"])
          .optional()
          .describe("Se 'S', retorna informações de ciência no processo"),
        sinRetornarMarcadores: z
          .enum(["S", "N"])
          .optional()
          .describe("Se 'S', retorna os marcadores/etiquetas do processo"),
        sinRetornarAnotacoes: z
          .enum(["S", "N"])
          .optional()
          .describe("Se 'S', retorna as anotações registradas no processo"),
        sinRetornarStatus: z
          .enum(["S", "N"])
          .optional()
          .describe("Se 'S', retorna indicadores detalhados de status"),
        sinRetornarUltimaMovimentacao: z
          .enum(["S", "N"])
          .optional()
          .describe("Se 'S', retorna a quantidade de dias da última movimentação"),
        start: z
          .string()
          .optional()
          .describe("Número da página para paginação (inicia em 0)"),
        limit: z
          .string()
          .optional()
          .describe("Quantidade de itens por página (ex: 50)"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "processos",
        path: "/processos",
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

  // 2. Consultar Processo Específico
  server.registerTool(
    "sei_consultar_processo",
    {
      title: "Consultar Processo por Número (SEI)",
      description:
        "Consulta detalhes completos de um processo no SEI a partir do seu protocolo (ex: 12.1.000000077-4 ou somente dígitos).",
      inputSchema: {
        protocoloProcedimento: z
          .string()
          .describe("Número do processo (ex: 12.1.000000077-4 ou 1210000000774)"),
        sinRetornarAssuntos: z
          .boolean()
          .optional()
          .describe("Se true, retorna assuntos vinculados ao processo"),
        sinRetornarInteressados: z
          .boolean()
          .optional()
          .describe("Se true, retorna participantes interessados"),
        sinRetornarObservacoes: z
          .boolean()
          .optional()
          .describe("Se true, retorna observações das unidades"),
        sinRetornarAndamentoGeracao: z
          .boolean()
          .optional()
          .describe("Se true, retorna andamento inicial de geração"),
        sinRetornarAndamentoConclusao: z
          .boolean()
          .optional()
          .describe("Se true, retorna andamento de conclusão"),
        sinRetornarUltimoAndamento: z
          .boolean()
          .optional()
          .describe("Se true, retorna o último andamento"),
        sinRetornarUnidadesProcedimentoAberto: z
          .boolean()
          .optional()
          .describe("Se true, retorna as unidades onde o processo está aberto"),
        sinRetornarProcedimentosRelacionados: z
          .boolean()
          .optional()
          .describe("Se true, retorna processos relacionados"),
        sinRetornarProcedimentosAnexados: z
          .boolean()
          .optional()
          .describe("Se true, retorna processos anexados"),
      },
    },
    async (args) => {
      const { protocoloProcedimento, ...params } = args;
      const cleanProtocolo = encodeURIComponent(protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}`,
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

  // 3. Gerar Novo Processo
  server.registerTool(
    "sei_gerar_processo",
    {
      title: "Gerar / Criar Novo Processo (SEI)",
      description:
        "Cria um novo processo administrativo no SEI com tipo, especificação, nível de acesso, interessados e assuntos.",
      inputSchema: {
        idTipoProcedimento: z
          .string()
          .describe("Identificador do tipo de processo (obtido via sei_listar_tipos_processo)"),
        especificacao: z
          .string()
          .optional()
          .describe("Especificação ou resumo do objeto do processo"),
        nivelAcesso: z
          .enum(["0", "1", "2"])
          .describe("Nível de acesso: '0' = Público, '1' = Restrito, '2' = Sigiloso"),
        idHipoteseLegal: z
          .string()
          .optional()
          .describe("ID da hipótese legal (obrigatório se nivelAcesso for 1 - restrito)"),
        observacao: z
          .string()
          .optional()
          .describe("Texto de observação da unidade"),
        numeroProtocolo: z
          .string()
          .optional()
          .describe("Número customizado do processo (deixar vazio para gerar automaticamente)"),
        dataAutuacao: z
          .string()
          .optional()
          .describe("Data de autuação (formato DD/MM/AAAA)"),
        assuntos: z
          .array(
            z.object({
              codigoEstruturado: z.string().describe("Código estruturado do assunto (ex: 001.01.01.002)"),
              descricao: z.string().describe("Descrição do assunto"),
            })
          )
          .optional()
          .describe("Lista de assuntos do processo"),
        interessados: z
          .array(
            z.object({
              sigla: z.string().describe("Sigla do interessado"),
              nome: z.string().describe("Nome do interessado"),
            })
          )
          .optional()
          .describe("Lista de interessados"),
        procedimentosRelacionados: z
          .array(z.string())
          .optional()
          .describe("IDs de processos a serem relacionados automaticamente"),
        unidadesEnvio: z
          .array(z.string())
          .optional()
          .describe("IDs de unidades para tramitar/enviar o processo logo após a criação"),
        sinManterAbertoUnidade: z
          .boolean()
          .optional()
          .default(true)
          .describe("Se true, mantém o processo aberto na unidade geradora"),
        sinEnviarEmailNotificacao: z
          .boolean()
          .optional()
          .default(false)
          .describe("Se true, envia e-mail de aviso para as unidades destinatárias"),
        dataRetornoProgramado: z
          .string()
          .optional()
          .describe("Data para Retorno Programado (DD/MM/AAAA)"),
        diasRetornoProgramado: z
          .string()
          .optional()
          .describe("Número de dias para Retorno Programado"),
        sinDiasUteisRetornoProgramado: z
          .boolean()
          .optional()
          .describe("Se true, contagem de retorno programado é em dias úteis"),
        idMarcador: z
          .string()
          .optional()
          .describe("ID de marcador da unidade para aplicar ao processo"),
        textoMarcador: z
          .string()
          .optional()
          .describe("Texto explicativo para o marcador"),
        dataControlePrazo: z
          .string()
          .optional()
          .describe("Data certa para Controle de Prazo (DD/MM/AAAA)"),
        diasControlePrazo: z
          .string()
          .optional()
          .describe("Número de dias para o Controle de Prazo"),
        sinDiasUteisControlePrazo: z
          .boolean()
          .optional()
          .describe("Se true, prazo é contado em dias úteis"),
      },
    },
    async (args) => {
      const payload: any = {
        procedimento: {
          idTipoProcedimento: args.idTipoProcedimento,
          especificacao: args.especificacao || "",
          nivelAcesso: args.nivelAcesso,
          idHipoteseLegal: args.idHipoteseLegal,
          observacao: args.observacao || "",
          numeroProtocolo: args.numeroProtocolo,
          dataAutuacao: args.dataAutuacao,
          assuntos: args.assuntos || [],
          interessados: args.interessados || [],
        },
        procedimentosRelacionados: args.procedimentosRelacionados,
        unidadesEnvio: args.unidadesEnvio,
        sinManterAbertoUnidade: args.sinManterAbertoUnidade,
        sinEnviarEmailNotificacao: args.sinEnviarEmailNotificacao,
        dataRetornoProgramado: args.dataRetornoProgramado,
        diasRetornoProgramado: args.diasRetornoProgramado,
        sinDiasUteisRetornoProgramado: args.sinDiasUteisRetornoProgramado,
        idMarcador: args.idMarcador,
        textoMarcador: args.textoMarcador,
        dataControlePrazo: args.dataControlePrazo,
        diasControlePrazo: args.diasControlePrazo,
        sinDiasUteisControlePrazo: args.sinDiasUteisControlePrazo,
      };

      const data = await client.request({
        service: "processos",
        path: "/processos",
        method: "POST",
        body: payload,
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

  // 4. Excluir Processo
  server.registerTool(
    "sei_excluir_processo",
    {
      title: "Excluir Processo (SEI)",
      description: "Exclui um processo no SEI a partir do seu protocolo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo a ser excluído"),
      },
    },
    async (args) => {
      const cleanProtocolo = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}`,
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

  // 5. Listar Documentos do Processo
  server.registerTool(
    "sei_listar_documentos_processo",
    {
      title: "Listar Documentos de um Processo (SEI)",
      description: "Lista todos os documentos (gerados e anexados) inseridos em um processo no SEI.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        start: z.string().optional().describe("Página inicial para paginação"),
        limit: z.string().optional().describe("Limite de registros por página"),
        sinRetornarStatus: z
          .enum(["S", "N"])
          .optional()
          .describe("Se 'S', retorna status detalhados de cada documento"),
      },
    },
    async (args) => {
      const { protocoloProcedimento, ...params } = args;
      const cleanProtocolo = encodeURIComponent(protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}/documentos`,
        method: "GET",
        params: {
          start: params.start,
          limit: params.limit,
          SinRetornarStatus: params.sinRetornarStatus,
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

  // 6. Concluir Processo
  server.registerTool(
    "sei_concluir_processo",
    {
      title: "Concluir Processo na Unidade (SEI)",
      description: "Conclui a tramitação do processo na unidade atual.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo a ser concluído"),
      },
    },
    async (args) => {
      const cleanProtocolo = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}/conclusao`,
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

  // 7. Reabrir Processo
  server.registerTool(
    "sei_reabrir_processo",
    {
      title: "Reabrir Processo Concluído (SEI)",
      description: "Reabre um processo que estava concluído na unidade atual.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo a ser reaberto"),
      },
    },
    async (args) => {
      const cleanProtocolo = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}/reabertura`,
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

  // 8. Enviar / Tramitar Processo
  server.registerTool(
    "sei_enviar_processo",
    {
      title: "Enviar / Tramitar Processo para Unidades (SEI)",
      description:
        "Tramita/envia um processo para uma ou mais unidades de destino no SEI, com controle de retorno programado e opções de manter aberto.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo a ser enviado"),
        unidadesDestino: z
          .array(
            z.object({
              idUnidade: z.string().describe("ID da unidade de destino no SEI"),
            })
          )
          .describe("Lista de unidades destinatárias"),
        sinManterAbertoUnidade: z
          .boolean()
          .default(false)
          .describe("Se true, mantém o processo aberto na unidade remetente"),
        sinRemoverAnotacao: z
          .boolean()
          .default(false)
          .describe("Se true, remove anotações ao tramitar"),
        sinEnviarEmailNotificacao: z
          .boolean()
          .default(false)
          .describe("Se true, envia e-mail de notificação aos destinatários"),
        dataRetornoProgramado: z
          .string()
          .optional()
          .describe("Data de retorno programado (DD/MM/AAAA)"),
        diasRetornoProgramado: z
          .string()
          .optional()
          .describe("Quantidade de dias para retorno programado"),
        sinDiasUteisRetornoProgramado: z
          .boolean()
          .default(false)
          .describe("Se true, prazo é em dias úteis"),
        sinReabrir: z
          .boolean()
          .default(false)
          .describe("Se true, reabre o processo caso esteja concluído"),
      },
    },
    async (args) => {
      const { protocoloProcedimento, ...body } = args;
      const cleanProtocolo = encodeURIComponent(protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}/envio`,
        method: "POST",
        body: {
          protocoloProcedimento,
          ...body,
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

  // 9. Bloquear Processo
  server.registerTool(
    "sei_bloquear_processo",
    {
      title: "Bloquear Processo (SEI)",
      description: "Bloqueia um processo para impedir alterações ou exclusão.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo a bloquear"),
      },
    },
    async (args) => {
      const cleanProtocolo = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}/bloqueio`,
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

  // 10. Receber Processo
  server.registerTool(
    "sei_receber_processo",
    {
      title: "Receber Processo na Unidade (SEI)",
      description: "Registra o recebimento formal de um processo tramitado para a unidade.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
      },
    },
    async (args) => {
      const cleanProtocolo = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}/recebimento`,
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

  // 11. Atribuir Processo a Usuário
  server.registerTool(
    "sei_atribuir_processo",
    {
      title: "Atribuir Processo a Usuário da Unidade (SEI)",
      description: "Atribui a responsabilidade de um processo a um usuário específico na unidade.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        idUsuario: z.string().describe("ID do usuário na unidade"),
        sinReabrir: z
          .enum(["S", "N"])
          .default("N")
          .describe("Se 'S', reabre o processo caso esteja concluído"),
      },
    },
    async (args) => {
      const cleanProtocolo = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanProtocolo}/atribuicao`,
        method: "PUT",
        body: {
          IdUsuario: args.idUsuario,
          SinReabrir: args.sinReabrir,
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

  // 12. Listar Atribuições de Processos por CPF
  server.registerTool(
    "sei_listar_atribuicoes_usuario",
    {
      title: "Consultar Processos Atribuídos por CPF (SEI)",
      description: "Consulta a lista de processos atribuídos a um usuário no sistema a partir do seu CPF.",
      inputSchema: {
        cpf: z.string().describe("Número do CPF do usuário (apenas dígitos)"),
        sinRetornarRecebidos: z.boolean().optional().describe("Se true, inclui processos recebidos"),
        sinRetornarGerados: z.boolean().optional().describe("Se true, inclui processos gerados"),
      },
    },
    async (args) => {
      const cleanCpf = encodeURIComponent(args.cpf.replace(/\D/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanCpf}/atribuicao`,
        method: "GET",
        params: {
          sinRetornarRecebidos: args.sinRetornarRecebidos,
          sinRetornarGerados: args.sinRetornarGerados,
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

  // 13. Relacionar Processos
  server.registerTool(
    "sei_relacionar_processos",
    {
      title: "Relacionar Dois Processos (SEI)",
      description: "Cria um vínculo de relacionamento bilateral entre dois processos no SEI.",
      inputSchema: {
        protocoloProcedimento1: z.string().describe("Número do primeiro processo"),
        protocoloProcedimento2: z.string().describe("Número do segundo processo"),
      },
    },
    async (args) => {
      const clean1 = encodeURIComponent(args.protocoloProcedimento1.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean1}/relacionamento`,
        method: "POST",
        body: {
          protocoloProcedimento2: args.protocoloProcedimento2,
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

  // 14. Remover Relacionamento entre Processos
  server.registerTool(
    "sei_remover_relacionamento_processos",
    {
      title: "Remover Relacionamento entre Processos (SEI)",
      description: "Remove o vínculo de relacionamento entre dois processos.",
      inputSchema: {
        protocoloProcedimento1: z.string().describe("Número do primeiro processo"),
        protocoloProcedimento2: z.string().describe("Número do segundo processo vinculado"),
      },
    },
    async (args) => {
      const clean1 = encodeURIComponent(args.protocoloProcedimento1.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean1}/relacionamento`,
        method: "DELETE",
        params: {
          protocoloProcedimento2: args.protocoloProcedimento2,
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

  // 15. Anexar Processo
  server.registerTool(
    "sei_anexar_processo",
    {
      title: "Anexar Processo a Outro (SEI)",
      description: "Anexa um processo secundário (filho) a um processo principal (pai).",
      inputSchema: {
        protocoloProcedimentoPrincipal: z.string().describe("Número do processo principal"),
        protocoloProcedimentoAnexado: z.string().describe("Número do processo a ser anexado"),
      },
    },
    async (args) => {
      const cleanPrincipal = encodeURIComponent(
        args.protocoloProcedimentoPrincipal.replace(/[.\-/]/g, "")
      );
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanPrincipal}/anexacao`,
        method: "POST",
        body: {
          protocoloProcedimentoAnexado: args.protocoloProcedimentoAnexado,
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

  // 16. Desanexar Processo
  server.registerTool(
    "sei_desanexar_processo",
    {
      title: "Desanexar Processo (SEI)",
      description: "Desanexa um processo com justificativa de motivo.",
      inputSchema: {
        protocoloProcedimentoPrincipal: z.string().describe("Número do processo principal"),
        protocoloProcedimentoAnexado: z.string().describe("Número do processo anexado a desanexar"),
        motivo: z.string().describe("Motivo da desanexação"),
      },
    },
    async (args) => {
      const cleanPrincipal = encodeURIComponent(
        args.protocoloProcedimentoPrincipal.replace(/[.\-/]/g, "")
      );
      const data = await client.request({
        service: "processos",
        path: `/processos/${cleanPrincipal}/anexacao`,
        method: "DELETE",
        params: {
          protocoloProcedimentoAnexado: args.protocoloProcedimentoAnexado,
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

  // 17. Sobrestar Processo
  server.registerTool(
    "sei_sobrestar_processo",
    {
      title: "Sobrestar Processo (SEI)",
      description: "Suspende / sobresta o andamento de um processo com motivo e opcional vínculo a outro processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo a sobrestar"),
        motivo: z.string().describe("Motivo do sobrestamento"),
        protocoloProcedimentoVinculado: z
          .string()
          .optional()
          .describe("Número de outro processo ao qual o sobrestamento está condicionado"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/sobrestamento`,
        method: "POST",
        body: {
          protocoloProcedimento: args.protocoloProcedimento,
          motivo: args.motivo,
          protocoloProcedimentoVinculado: args.protocoloProcedimentoVinculado,
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

  // 18. Remover Sobrestamento de Processo
  server.registerTool(
    "sei_remover_sobrestamento_processo",
    {
      title: "Remover Sobrestamento de Processo (SEI)",
      description: "Remove o sobrestamento de um processo, reativando sua tramitação normal.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/sobrestamento`,
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

  // 19. Definir Controle de Prazo
  server.registerTool(
    "sei_definir_controle_prazo",
    {
      title: "Definir Controle de Prazo de Processo (SEI)",
      description: "Define ou atualiza o controle de prazo para resposta/ação em um processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        dataPrazo: z.string().optional().describe("Data final do prazo (DD/MM/AAAA)"),
        dias: z.string().optional().describe("Número de dias para o prazo"),
        sinDiasUteis: z
          .enum(["S", "N"])
          .default("N")
          .describe("Se 'S', indica que a contagem é em dias úteis"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/prazo`,
        method: "POST",
        body: {
          protocolosProcedimentos: [
            {
              protocoloProcedimento: args.protocoloProcedimento,
              dataPrazo: args.dataPrazo || "",
              dias: args.dias || "0",
              sinDiasUteis: args.sinDiasUteis,
            },
          ],
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

  // 20. Remover Controle de Prazo
  server.registerTool(
    "sei_remover_controle_prazo",
    {
      title: "Remover Controle de Prazo de Processo (SEI)",
      description: "Remove o controle de prazo ativo de um processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/prazo`,
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

  // 21. Concluir Controle de Prazo
  server.registerTool(
    "sei_concluir_controle_prazo",
    {
      title: "Concluir Controle de Prazo de Processo (SEI)",
      description: "Finaliza o controle de prazo de um processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/prazo/conclusao`,
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

  // 22. Definir Marcador no Processo
  server.registerTool(
    "sei_definir_marcador_processo",
    {
      title: "Definir Marcador / Tag no Processo (SEI)",
      description: "Aplica um marcador colorido/etiqueta a um processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        idMarcador: z.number().describe("ID do marcador (obtido via sei_listar_marcadores_unidade)"),
        texto: z.string().optional().describe("Texto descritivo associado ao marcador"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/marcador/definicao`,
        method: "POST",
        body: {
          idMarcador: args.idMarcador,
          texto: args.texto || "",
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

  // 23. Listar Marcadores da Unidade
  server.registerTool(
    "sei_listar_marcadores_unidade",
    {
      title: "Listar Marcadores da Unidade (SEI)",
      description: "Retorna todos os marcadores/etiquetas disponíveis para uso na unidade.",
    },
    async () => {
      const data = await client.request({
        service: "processos",
        path: "/processos/marcadores",
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

  // 24. Listar Andamentos dos Marcadores
  server.registerTool(
    "sei_listar_andamentos_marcadores",
    {
      title: "Listar Histórico de Marcadores do Processo (SEI)",
      description: "Lista o histórico de alterações e aplicações de marcadores em um processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        marcadores: z.number().optional().describe("Filtrar por ID do marcador"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/andamentos/marcadores`,
        method: "GET",
        params: {
          marcadores: args.marcadores,
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

  // 25. Alterar Nível de Acesso do Processo
  server.registerTool(
    "sei_alterar_nivel_acesso_processo",
    {
      title: "Alterar Nível de Acesso do Processo (SEI)",
      description: "Altera o nível de acesso de um processo (0=Público, 1=Restrito) e respectiva hipótese legal.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        nivelAcesso: z.enum(["0", "1"]).describe("0 = Público, 1 = Restrito"),
        hipotese: z.string().describe("ID da hipótese legal associada"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/nivelacesso`,
        method: "PUT",
        body: {
          nivelAcesso: args.nivelAcesso,
          hipotese: args.hipotese,
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

  // 26. Lançar Andamento Manual no Processo
  server.registerTool(
    "sei_lancar_andamento",
    {
      title: "Lançar Andamento Manual no Processo (SEI)",
      description: "Insere um registro customizado de andamento no histórico do processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        idTarefa: z.string().describe("ID da tarefa/ação correspondente"),
        idTarefaModulo: z.string().optional().describe("ID da tarefa de módulo"),
        atributos: z
          .array(
            z.object({
              nome: z.string().describe("Nome do atributo variável (ex: @DOCUMENTO@, @USUARIO@)"),
              valor: z.string().describe("Valor atribuído"),
              idOrigem: z.string().optional().describe("Identificador auxiliar"),
            })
          )
          .describe("Atributos variáveis da mensagem"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/andamento`,
        method: "POST",
        body: {
          protocoloProcedimento: args.protocoloProcedimento,
          idTarefa: args.idTarefa,
          idTarefaModulo: args.idTarefaModulo || "",
          atributos: args.atributos,
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

  // 27. Listar Andamentos do Processo
  server.registerTool(
    "sei_listar_andamentos",
    {
      title: "Listar Andamentos / Histórico do Processo (SEI)",
      description: "Consulta a lista de andamentos realizados no processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        retornaAtributos: z.enum(["S", "N"]).optional().describe("Se 'S', retorna os atributos"),
        andamentos: z.string().optional().describe("Identificador interno do andamento para filtro"),
        tarefas: z.string().optional().describe("Identificador da tarefa para filtro"),
        tarefasModulos: z.string().optional().describe("Identificador da tarefa de módulo"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "processos",
        path: "/processos/andamentos",
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

  // 28. Listar Andamentos Completo (Filtros Avançados)
  server.registerTool(
    "sei_listar_andamentos_completo",
    {
      title: "Listar Andamentos Completo com Filtros Avançados (SEI)",
      description:
        "Consulta o histórico detalhado do processo com múltiplos filtros (período de datas, tipo de histórico, unidade de origem/destino, usuário).",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        tipoHistorico: z
          .enum(["T", "P", "R", "Z"])
          .optional()
          .describe("T = Total, P = Parcial, R = Resumido, Z = Personalizado"),
        retornaAtributos: z.enum(["S", "N"]).optional().describe("Se 'S', retorna atributos"),
        tarefas: z.string().optional().describe("Lista separada por vírgulas dos IDs das tarefas"),
        idUsuario: z.string().optional().describe("ID do usuário ou sistema gerador da atividade"),
        idUnidadeOrigem: z.string().optional().describe("ID da unidade de origem da operação"),
        idUnidadeDestino: z.string().optional().describe("ID da unidade de destino (trâmite)"),
        filtroNomeTarefa: z.string().optional().describe("Texto a pesquisar na descrição"),
        filtroValorAtributoAndamento: z.string().optional().describe("Texto a pesquisar nos atributos"),
        idTipoProcedimentoProtocolo: z.string().optional().describe("ID do tipo de processo"),
        retornaDescricaoTipoProcesso: z.enum(["S", "N"]).optional().describe("Se 'S', retorna descrição do tipo"),
        dataInicio: z.string().optional().describe("Data inicial (DD/MM/AAAA)"),
        dataFim: z.string().optional().describe("Data final (DD/MM/AAAA)"),
        start: z.string().optional().describe("Página inicial"),
        limit: z.string().optional().describe("Limite de registros"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "processos",
        path: "/andamentos/completo",
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

  // 29. Listar Tipos de Procedimento
  server.registerTool(
    "sei_listar_tipos_processo",
    {
      title: "Listar Tipos de Processo (SEI)",
      description: "Retorna a listagem de todos os tipos de processos configurados no SEI.",
    },
    async () => {
      const data = await client.request({
        service: "processos",
        path: "/processos/tipos",
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

  // 30. Disponibilizar Acesso Externo
  server.registerTool(
    "sei_disponibilizar_acesso_externo",
    {
      title: "Disponibilizar Acesso Externo ao Processo (SEI)",
      description: "Gera credencial e link de disponibilização de acesso externo a um processo ou documento.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        idProcedimento: z.string().optional().describe("ID interno do processo"),
        emailUnidade: z.string().describe("E-mail cadastrado na unidade geradora"),
        destinatario: z.string().optional().describe("Nome do destinatário externo isolado"),
        emailDestinatario: z.string().describe("E-mail do destinatário"),
        idContato: z.string().optional().describe("ID do contato"),
        idParticipante: z.string().optional().describe("Código do participante interessado"),
        idUsuarioExterno: z.string().optional().describe("ID do usuário externo"),
        motivo: z.string().describe("Motivo da disponibilização"),
        tipo: z.enum(["I", "E", "D"]).optional().describe("I = Interessado, E = Usuário Externo, D = Destinatário"),
        sinInclusao: z.enum(["S", "N"]).default("N").describe("Se 'S', permite que o usuário externo inclua documentos"),
        series: z.string().optional().describe("IDs das séries que podem ser incluídas"),
        protocolos: z.string().optional().describe("Número do documento específico se aplicável"),
        senha: z.string().describe("Senha de confirmação do sistema integrador"),
        dias: z.string().describe("Prazo em dias para a disponibilização"),
      },
    },
    async (args) => {
      const { protocoloProcedimento, ...body } = args;
      const clean = encodeURIComponent(protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/disponibilizacaoAcessoExterno`,
        method: "POST",
        body: {
          protocoloProcedimento,
          IdProcedimento: body.idProcedimento,
          EmailUnidade: body.emailUnidade,
          Destinatario: body.destinatario,
          EmailDestinatario: body.emailDestinatario,
          IdContato: body.idContato,
          IdParticipante: body.idParticipante,
          IdUsuarioExterno: body.idUsuarioExterno,
          Motivo: body.motivo,
          Tipo: body.tipo,
          SinInclusao: body.sinInclusao,
          Series: body.series,
          Protocolos: body.protocolos,
          Senha: body.senha,
          Dias: body.dias,
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

  // 31. Listar Disponibilizações de Acesso Externo
  server.registerTool(
    "sei_listar_disponibilizacoes_acesso_externo",
    {
      title: "Listar Disponibilizações de Acesso Externo do Processo (SEI)",
      description: "Lista todas as disponibilizações de acesso externo ativas e expiradas de um processo.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/disponibilizacaoAcessoExterno`,
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

  // 32. Cancelar Disponibilização de Acesso Externo
  server.registerTool(
    "sei_cancelar_disponibilizacao_acesso_externo",
    {
      title: "Cancelar Disponibilização de Acesso Externo (SEI)",
      description: "Cancela uma disponibilização de acesso externo ativa.",
      inputSchema: {
        protocoloProcedimento: z.string().describe("Número do processo"),
        idAcessoExterno: z.string().describe("ID do acesso externo a ser cancelado"),
        motivo: z.string().describe("Motivo do cancelamento"),
      },
    },
    async (args) => {
      const clean = encodeURIComponent(args.protocoloProcedimento.replace(/[.\-/]/g, ""));
      const data = await client.request({
        service: "processos",
        path: `/processos/${clean}/disponibilizacaoAcessoExterno/${encodeURIComponent(args.idAcessoExterno)}`,
        method: "DELETE",
        headers: {
          Motivo: args.motivo,
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

  // 33. Consultar Processos Individuais
  server.registerTool(
    "sei_consultar_processos_individuais",
    {
      title: "Consultar Processos Individuais por Usuário Interessado (SEI)",
      description: "Consulta processos individuais vinculados a um usuário interessado.",
      inputSchema: {
        idOrgaoProcedimento: z.string().describe("Identificador do órgão do processo"),
        idTipoProcedimento: z.string().describe("Identificador do tipo do processo"),
        idOrgaoUsuario: z.string().describe("Identificador do órgão do usuário"),
        siglaUsuario: z.string().describe("Sigla do usuário"),
      },
    },
    async (args) => {
      const data = await client.request({
        service: "processos",
        path: "/processos/individual",
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
