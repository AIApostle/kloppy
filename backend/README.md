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

Configure shared remote HTTPS or local loopback Streamable HTTP MCP servers
through `MCP_SERVERS_JSON`, or connect an individual user's MCP server from the
Integrations page. Per-user connections are tested before saving, encrypted
with `INTEGRATION_ENCRYPTION_KEY`, and scoped by Supabase RLS. Generate a key
with `uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
Set the same key in the local backend environment and the deployed API
environment; changing it makes previously stored MCP tokens unreadable.

The Integrations page supports Meta Ads, Google Ads, HubSpot, Mailchimp, Canva,
Figma, Google Drive, Notion, Google Analytics 4, Shopify, and custom MCP
servers. These are generic MCP connections, not built-in OAuth integrations:
provide the endpoint and authentication token from a provider's MCP offering.
Kloppy discovers available tools and permits only those explicitly selected
that the server marks read-only. The current connector layer cannot publish,
send, spend, or change external accounts. Those actions need dedicated
provider write adapters and an approval flow.

Qloo uses the server-only `QLOO_API_KEY` and is exposed to the agent as a
backend tool; it does not appear as a user-configurable browser integration.

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
