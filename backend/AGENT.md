# Backend engineering rules

## Security first

- Treat every request as untrusted. Validate all external input with Pydantic.
- Derive identity and tenant membership from verified Supabase Auth tokens and
  server-controlled membership rows; never trust a client-provided tenant ID,
  role, email, or metadata claim for authorization.
- Never use `SUPABASE_SERVICE_ROLE_KEY` in the frontend or a request-scoped
  client. The backend currently uses only the Supabase publishable key for
  user auth. Privileged workflows require a separately reviewed server-side
  adapter and explicit audit coverage.
- Do not log passwords, access tokens, refresh tokens, API keys, MCP payloads,
  or customer content.
- Fail closed when required production configuration is missing. Do not fall
  back to demo sessions in authentication or authorization paths.
- Use generic authentication errors where revealing account existence would
  create an enumeration leak.

## Structure

- Keep `backend/main.py` as the Uvicorn entry point.
- Keep related code together: routes in `src/app/routes/`, integrations in
  `src/app/services/`, domain-specific schemas in `src/app/schemas/`, and
  configuration in `src/app/config.py`. Authentication endpoints belong in
  `src/app/routes/auth/`; do not grow a monolithic routes or schemas module.
- Route handlers validate and translate HTTP concerns. Services own provider
  calls and domain behavior. Do not put Supabase, Qloo, Strands, or MCP calls
  directly in route handlers.
- Define provider-neutral interfaces before adding provider-specific adapters.
  Qloo is an audience-signal provider; Strands orchestrates agents; MCP
  adapters connect external applications and in-house resources.
- Keep mode prompts in `src/app/prompts/`, one module per mode. The agent
  service owns Strands and OpenRouter construction; routes own transport only.
- OpenRouter credentials are server-only. Use `openrouter/free` when no
  explicit model is selected and fail closed when `OPENROUTER_API_KEY` is
  missing.

## Data and tenancy

- Every tenant-owned query must carry verified tenant context and be protected
  by Supabase RLS.
- Use typed repositories/services instead of module-global mutable state.
- Preserve campaign, evidence, approval, execution, and audit relationships.
- Consequential actions require an explicit permission decision and idempotency.

## Verification

- Read official provider documentation before relying on an unfamiliar API.
- Add focused tests for success, invalid input, provider failure, expired
  token, and cross-tenant denial.
- Run `uv run python -m compileall -q main.py src` and the smallest relevant
  test selection before declaring a backend change complete.
