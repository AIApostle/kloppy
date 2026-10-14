# Kloppy technology stack

Kloppy is an AI-first, tenant-isolated marketing operating system. The stack
is intentionally provider-neutral at the model layer while keeping campaign
context, permissions, and auditability in Kloppy.

## Product surfaces

- **Frontend:** React 19, TypeScript, Vite, CSS, responsive campaign shell.
- **Chat:** a full-page composer with Research, Plan, and Execute modes.
- **Documents:** generated artifacts are returned as typed records and opened
  in an in-product document viewer.
- **Context controls:** the composer can explicitly attach files, knowledge
  sources, and campaign skills.
- **Permissions:** every chat has an `ask` or `auto` execution policy. Live
  publishing, spending, targeting changes, and credential changes must still
  pass server-side authorization and audit checks.

## Runtime

- **API:** Python 3.11 and FastAPI.
- **Agent orchestration:** Strands Agents SDK. Strands owns the agent loop,
  tool routing, specialist handoffs, and MCP client connections.
- **Model gateway:** OpenRouter through Strands' OpenAI-compatible model
  adapter. The default model is `openrouter/free`; the OpenRouter key stays
  server-side in `OPENROUTER_API_KEY`.
- **MCP:** external applications and in-house resources are exposed through
  scoped MCP connectors. Connector credentials remain server-side.
- **Realtime chat:** FastAPI WebSockets for interactive turns and execution
  events, with HTTP chat as a reconnect/fallback path.
- **Memory:** Memwal stores durable, tenant-scoped memory. Conversation
  messages and campaign artifacts remain in the application data model;
  memory writes are explicit, attributable, and removable.

## Data and security

- **Database:** Supabase Postgres with tenant-leading foreign keys, indexes,
  and Row Level Security on every exposed tenant-owned table.
- **Auth:** Supabase Auth. The API verifies bearer tokens and derives the
  active tenant from server-controlled memberships; client-provided tenant IDs
  are never authorization inputs.
- **Storage:** Supabase Storage with tenant-scoped paths and matching
  read/write policies.
- **Audit:** immutable approval, tool-call, execution, permission, and model
  selection events.

## Model abstraction

The UI model selector is backed by a provider-neutral model registry. A model
entry includes provider, capabilities, context limits, availability, cost
metadata, and whether it can call tools. The initial demo registry includes
Kloppy balanced, Claude Sonnet, GPT-5, and Gemini Pro; production availability
must come from the backend rather than a hardcoded client assumption.

## Configuration

Backend environment variables include `SUPABASE_URL`,
`SUPABASE_PUBLISHABLE_KEY`, `MEMWAL_URL`, `MEMWAL_API_KEY`, and
`STRANDS_MODEL_ID`. Secret or service-role keys must never be sent to the
browser. See [TENANCY-IMPLEMENTATION-PLAN.md](./backend/TENANCY-IMPLEMENTATION-PLAN.md)
before replacing the current demo state with production persistence.
