import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerProcessosTools } from "./processos.js";
import { registerDocumentosTools } from "./documentos.js";
import { registerParametrosTools } from "./parametros.js";

/**
 * Registers all SEI tools on the given MCP server instance.
 */
export function registerAllSeiTools(server: McpServer): void {
  registerProcessosTools(server);
  registerDocumentosTools(server);
  registerParametrosTools(server);
}

export * from "./processos.js";
export * from "./documentos.js";
export * from "./parametros.js";
