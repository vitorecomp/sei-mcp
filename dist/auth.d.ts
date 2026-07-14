import { Request, Response, NextFunction } from "express";
/**
 * Express middleware to validate authentication credentials for MCP endpoint requests.
 * Supports:
 *  1. Header: `Authorization: Bearer <token>`
 *  2. Header: `x-api-key: <token>`
 *  3. Query param: `?token=<token>` (useful for browsers / native EventSource clients)
 */
export declare function authenticateRequest(req: Request, res: Response, next: NextFunction): void;
