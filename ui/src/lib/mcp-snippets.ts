// ── MCP client configuration snippets ───────────────────────────────────────
// Kept out of any one screen: the Seeker MCP section was folded into
// Environment, which offers the same "copy a client config" affordance.

export const DEFAULT_STDIO_COMMAND = 'python -m skill_seekers.mcp.server_fastmcp';
export const DEFAULT_HTTP_URL = 'http://127.0.0.1:8000/sse';

/** `.mcp.json` entry for agents that spawn the server themselves (Claude Code). */
export const STDIO_SNIPPET = JSON.stringify(
  { mcpServers: { 'skill-seekers': { command: 'python', args: ['-m', 'skill_seekers.mcp.server_fastmcp'] } } },
  null,
  2,
);

/** Config entry for agents that connect over HTTP/SSE (Cursor, Windsurf). */
export const httpSnippet = (url: string) =>
  JSON.stringify({ mcpServers: { 'skill-seekers': { url } } }, null, 2);
