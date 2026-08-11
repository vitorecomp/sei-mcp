import { Request, Response, NextFunction } from "express";
/**
 * Middleware to enforce OAuth on MCP requests following the Google Chrome Enterprise Premium MCP pattern:
 * 1. Tool discovery requests (`initialize`, `tools/list`, etc.) are permitted without blocking discovery,
 *    allowing Gemini Enterprise "Reload custom actions" to always succeed.
 * 2. Tool execution requests (`tools/call`) require authentication if OAuth is enabled.
 */
export declare function oauthMiddleware(req: Request, res: Response, next: NextFunction): Promise<void>;
