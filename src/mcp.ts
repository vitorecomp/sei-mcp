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

  // Tool 1: System info & health action
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

  // Tool 2: Echo message action
  server.registerTool(
    "echo",
    {
      title: "Echo Message",
      description: "Echoes a message string back to the user. Useful for connectivity verification.",
      inputSchema: {
        message: z.string().describe("The message string to echo back"),
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

  // Tool 3: Mathematical calculator action
  server.registerTool(
    "calculate",
    {
      title: "Calculate",
      description:
        "Performs arithmetic calculations (addition, subtraction, multiplication, division). Use this action whenever a user asks to calculate, compute, add, subtract, multiply, or divide numbers.",
      inputSchema: {
        operation: z
          .enum(["add", "subtract", "multiply", "divide"])
          .describe("The arithmetic operation to execute: 'add', 'subtract', 'multiply', or 'divide'"),
        a: z.number().describe("The first number (left operand)"),
        b: z.number().describe("The second number (right operand)"),
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
