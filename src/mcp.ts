import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerAllSeiTools } from "./tools/index.js";

/**
 * Factory function to instantiate and register tools/resources/prompts on the MCP Server.
 */
export function createMcpServer(): McpServer {
  const server = new McpServer({
    name: "SEI MCP Server",
    version: "1.0.0",
  });

  // System info & health action
  server.registerTool(
    "get_system_info",
    {
      title: "Get System Info",
      description: "Retrieves server health status, Node.js runtime version, system uptime, and environment.",
    },
    async () => {
      const info = {
        status: "healthy",
        uptimeSeconds: Math.floor(process.uptime()),
        timestamp: new Date().toISOString(),
        nodeVersion: process.version,
        environment: process.env.NODE_ENV || "development",
        service: "sei-mcp-server",
        capabilities: [
          "sei-processos (gestão completa de processos)",
          "sei-documentos (criação, upload, download e envio)",
          "sei-parametros (unidades, usuários, contatos, blocos, séries, hipóteses)",
        ],
      };
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(info, null, 2),
          },
        ],
      };
    }
  );

  // Register all SEI API tools (Processos, Documentos, Parâmetros)
  registerAllSeiTools(server);

  return server;
}
