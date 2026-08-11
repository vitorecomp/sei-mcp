import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

/**
 * Factory function to instantiate and register tools/resources/prompts on the MCP Server.
 */
export function createMcpServer(): McpServer {
  const server = new McpServer({
    name: "Enterprise Node MCP Server",
    version: "1.0.0",
  });

  // Tool 1: System info & health
  server.registerTool(
    "get_system_info",
    {
      description: "Retrieve server status, node version, and system runtime info",
    },
    async () => {
      const info = {
        status: "healthy",
        uptimeSeconds: Math.floor(process.uptime()),
        timestamp: new Date().toISOString(),
        nodeVersion: process.version,
        environment: process.env.NODE_ENV || "development",
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

  // Tool 2: Echo tool
  server.registerTool(
    "echo",
    {
      description: "Returns the provided string back to the user",
      inputSchema: {
        message: z.string().describe("Message to echo"),
      },
    },
    async ({ message }) => {
      return {
        content: [
          {
            type: "text",
            text: `[MCP Server Echo]: ${message}`,
          },
        ],
      };
    }
  );

  // Tool 3: Mathematical calculator tool
  server.registerTool(
    "calculate",
    {
      description: "Performs arithmetic operations (add, subtract, multiply, divide)",
      inputSchema: {
        operation: z.enum(["add", "subtract", "multiply", "divide"]).describe("Operation type"),
        a: z.number().describe("First number"),
        b: z.number().describe("Second number"),
      },
    },
    async ({ operation, a, b }) => {
      let result: number;
      switch (operation) {
        case "add":
          result = a + b;
          break;
        case "subtract":
          result = a - b;
          break;
        case "multiply":
          result = a * b;
          break;
        case "divide":
          if (b === 0) {
            return {
              isError: true,
              content: [{ type: "text", text: "Error: Division by zero is not allowed." }],
            };
          }
          result = a / b;
          break;
      }
      return {
        content: [
          {
            type: "text",
            text: `Calculation result: ${a} ${operation} ${b} = ${result}`,
          },
        ],
      };
    }
  );

  return server;
}
