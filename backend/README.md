## Run the API

From `backend/`, use the module attribute syntax required by Uvicorn:

```bash
uv run uvicorn main:app --reload --port 8000
```

The liveness endpoints are `/health`, `/ping`, and `/keepalive`.

# Agent tools: Qloo and MCP

Kloppy can expose server-side Qloo cultural research and allowlisted tools from
external MCP servers to the Strands agent. Set `QLOO_API_KEY` to enable Qloo.
Qloo credentials stay on the backend; the browser never receives the key.

Configure remote HTTPS or local loopback Streamable HTTP MCP servers through
`MCP_SERVERS_JSON` as JSON. Each server entry must include `allowed_tools` with
exact tool names. Kloppy only passes through tools that the server marks as
read-only. This prevents an
unreviewed MCP server from publishing, sending, spending, or changing external
accounts. Use `${env:VARIABLE_NAME}` for secrets in server headers and define
those variables in the backend process environment. For local development,
export referenced variables in the shell before starting the API. Configure
one server for each service you use. The integrations page lists the supported
providers: Meta Ads, Google Ads, HubSpot, Mailchimp, Canva, Figma, Google Drive,
Notion, Google Analytics 4, and Shopify. The generic MCP client does not supply
provider endpoints, OAuth grants, or credentials; configure those from each
provider's current MCP offering before its tools can appear in `AVAILABLE_TOOLS`.
Only read-only MCP tools are currently passed to the agent, so external write
actions still require an approved write-capable integration path.

For example, configure separate entries in `MCP_SERVERS_JSON` using the MCP
endpoint and exact read-only tool names provided by each service:

```json
{
  "mcpServers": {
    "google_drive": {
      "url": "https://<provider-mcp-endpoint>/mcp",
      "headers": {"Authorization": "Bearer ${env:GOOGLE_DRIVE_MCP_TOKEN}"},
      "allowed_tools": ["search_files", "get_file"]
    },
    "notion": {
      "url": "https://<provider-mcp-endpoint>/mcp",
      "headers": {"Authorization": "Bearer ${env:NOTION_MCP_TOKEN}"},
      "allowed_tools": ["search", "fetch"]
    }
  }
}
```

The agent can create a Markdown document draft inside a conversation. The
frontend renders that draft and lets the user download it. These drafts are
conversation outputs; persistent document storage and external write actions
need a configured provider and an explicit approval workflow.

The chat WebSocket emits activity events for tool calls and work stages. It
does not stream private model reasoning.
