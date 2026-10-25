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

# API and provider logs

The API writes structured request logs for HTTP routes and WebSocket chat
connections, including status, elapsed time, and a generated request ID.
External calls log provider, operation, outcome, upstream status when known,
and duration. These logs intentionally omit request bodies, query strings,
authorization headers, credentials, and provider response content. WebSocket
authentication is sent in the first frame rather than the URL to keep bearer
tokens out of access logs. Search logs will report Tavily as unavailable until
`TAVILY_API_KEY` is configured in the backend environment.

# Agent memory: Walrus Memory

Kloppy can recall relevant conversation facts between sessions with the
official Walrus Memory Python SDK (`memwal`). Set `MEMWAL_PRIVATE_KEY` and
`MEMWAL_ACCOUNT_ID` in the backend environment; optionally set
`MEMWAL_SERVER_URL` (defaults to the Walrus Memory production relayer). Create
an account and delegate key at [memory.walrus.xyz](https://memory.walrus.xyz).
The delegate key must stay server-side.

The API verifies the Supabase bearer token and derives opaque, stable Walrus
namespaces from the verified user ID and scope. Each user's workspace has its
own namespace; each selected project (campaign ID) has a separate namespace
that also includes that user ID, preventing cross-user memory sharing. The SDK
client is initialized with the user's workspace namespace and every recall,
analysis, and remember call explicitly supplies its intended namespace. Agent
turns recall from the workspace and current project only,
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
[Walrus Memory documentation](https://memory.walrus.xyz). The SDK documents
namespace as a client setting and as an optional argument to individual memory
operations; Kloppy uses both to keep each operation scoped explicitly.

# Agent tools: Qloo and MCP

Kloppy can expose server-side Qloo cultural research and allowlisted tools from
external MCP servers to the Strands agent. Set `QLOO_API_KEY` to enable Qloo.
Qloo credentials stay on the backend; the browser never receives the key.

## Agent web research and campaign documents

Set `TAVILY_API_KEY` in the backend environment to enable Kloppy's built-in
web-search and web-image-search tools. The key is required: create one in the
[Tavily dashboard](https://app.tavily.com), then configure it as `TAVILY_API_KEY`
in the backend's local environment and deployed API environment (for example,
Render). Keep it server-side and out of frontend configuration. Without this
key, both tools report that search is unavailable.

The backend uses Tavily's official `tavily-python` SDK. Web search is available
to the agent on every turn, but prompt instructions restrict it to requests
needing current, specialized, or explicitly requested research. Results include
source titles, URLs, snippets, and publication dates when provided. Image search
uses Tavily's `include_images` and `include_image_descriptions` options and
returns a small set of attributed visual examples in chat when the user asks
for images or references. The images remain third-party content; links lead to
their source pages where available. See the
[Tavily Python SDK quickstart](https://docs.tavily.com/sdk/python/quick-start),
[SDK reference](https://docs.tavily.com/sdk/python/reference), and
[Search API reference](https://docs.tavily.com/documentation/api-reference/endpoint/search).

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
