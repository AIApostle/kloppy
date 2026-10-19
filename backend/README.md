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
one server for each service you use, such as Drive, Figma, Notion, or an ads
platform.

The agent can create a Markdown document draft inside a conversation. The
frontend renders that draft and lets the user download it. These drafts are
conversation outputs; persistent document storage and external write actions
need a configured provider and an explicit approval workflow.

The chat WebSocket emits activity events for tool calls and work stages. It
does not stream private model reasoning.
