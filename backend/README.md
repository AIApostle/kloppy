## Run the API

From `backend/`, use the module attribute syntax required by Uvicorn:

```bash
uv run uvicorn main:app --reload --port 8000
```

The liveness endpoints are `/health`, `/ping`, and `/keepalive`.

The hosted frontend's default API endpoint is
`https://kloppy-dd2u.onrender.com/api`. Set `VITE_API_URL` in the frontend
deployment environment at build time only when pointing it at a different API.
In production, the frontend health-checks configured endpoints and falls back
to the hosted API if an endpoint is unavailable.
The API allows the configured frontend origins from `FRONTEND_ORIGINS`; add
the deployed frontend's origin there if it is not already listed.

# Agent memory: Walrus Memory

Kloppy can recall relevant conversation facts between sessions with the
official Walrus Memory Python SDK (`memwal`). Set `MEMWAL_PRIVATE_KEY` and
`MEMWAL_ACCOUNT_ID` in the backend environment; optionally set
`MEMWAL_SERVER_URL` (defaults to the Walrus Memory production relayer). Create
an account and delegate key at [memory.walrus.xyz](https://memory.walrus.xyz).
The delegate key must stay server-side.

The API verifies the Supabase bearer token before deriving opaque, stable
Walrus namespaces for the user workspace and each selected project (the
campaign ID). Agent turns recall from the workspace and current project only,
then submit the user's message for fact extraction; assistant-generated text
is not written to memory. The agent also has a project-scoped memory tool for
explicitly retaining concise, durable user-provided project facts. Writes are
queued and idempotent per fact. If Walrus is not configured or unavailable,
the current turn continues without recalled memory. User messages and facts
sent for memory processing are transmitted to the configured Walrus Memory
relayer over HTTPS.

The integration uses `MemWalSync`, `RecallParams`, `recall()`, `analyze()`,
and `remember()` from the Python SDK. See the
[Python SDK project on PyPI](https://pypi.org/project/memwal/) and the
[Walrus Memory documentation](https://memory.walrus.xyz).

# Agent tools: Qloo and MCP

Kloppy can expose server-side Qloo cultural research and allowlisted tools from
external MCP servers to the Strands agent. Set `QLOO_API_KEY` to enable Qloo.
Qloo credentials stay on the backend; the browser never receives the key.

## Agent web research and campaign documents

Set `TAVILY_API_KEY` in the backend environment to enable Kloppy's web search
tool. Search results include source titles, URLs, snippets, and publication
dates when provided; Kloppy should cite only sources returned by the search.
Without this key, web search is not exposed to the agent. Keep the key server
side and out of frontend configuration.

Substantial campaign deliverables are generated as `.docx` Word documents.
Each includes Overview, Audience, Strategy, and Launch & Learn, and the
campaign workspace saves the corresponding section content so each tab
reflects the same campaign work.

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

Qloo uses the server-only `QLOO_API_KEY` and `QLOO_API_URL` (defaults to
`https://api.qloo.com`). It is a built-in audience-research capability, not a
user-configurable integration. The authenticated `/api/qloo/run` route
supports entity enrichment, taste analysis, cross-category recommendations,
location-based insights and heatmaps, explainable agent grounding, and
downloadable snapshots for browser-local re-ranking. Qloo credentials are
never sent to the browser. Results are directional cultural-affinity evidence,
not proof of purchase intent or individual attributes.
The implementation follows Qloo's [API overview](https://docs.qloo.com/reference/api-overview),
[entity search](https://docs.qloo.com/reference/get-search),
[entity lookup](https://docs.qloo.com/reference/get-entities),
[taste analysis](https://docs.qloo.com/reference/taste-analysis),
[location insights](https://docs.qloo.com/reference/insights-with-location-use-case),
and [heatmap](https://docs.qloo.com/reference/heatmaps-use-case) guides.

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

The agent creates `.docx` document drafts inside a conversation. The
frontend renders a review preview and lets the user download the Word file.
These drafts are conversation outputs; persistent document storage and
external write actions need a configured provider and an explicit approval
workflow.

The chat WebSocket emits activity events for tool calls and work stages. It
does not stream private model reasoning.
