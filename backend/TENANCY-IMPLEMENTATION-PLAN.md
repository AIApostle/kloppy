# Kloppy Tenant Isolation Implementation Plan

## Purpose

Make Kloppy safe for multiple businesses sharing the same application and
database. A request must never read, mutate, search, stream, or authorize data
from another tenant. The frontend may display the active tenant context, but
the backend and database remain the source of truth for authorization.

This is a review plan only. The current demo routes and in-memory data must not
be treated as production tenant isolation.

## Security boundary

- A tenant is a business/account, not a browser-selected string.
- The authenticated identity comes from Supabase Auth.
- Membership in a tenant is stored in a server-owned membership table.
- Every tenant-owned row carries `tenant_id` and references the tenant table.
- The active tenant is selected only from memberships returned by the server.
- The backend derives `user_id`, `tenant_id`, and role from the verified access
  token and membership lookup; clients cannot override them in request bodies,
  query parameters, or headers.
- Cross-tenant resource IDs return the same not-found response as unknown IDs
  where practical, avoiding existence leaks.

## Proposed data model

1. `tenants`
   - `id uuid primary key`
   - `name text not null`
   - `slug text unique not null`
   - timestamps
2. `tenant_memberships`
   - `tenant_id uuid references tenants(id) on delete cascade`
   - `user_id uuid references auth.users(id) on delete cascade`
   - `role text check (role in ('owner', 'admin', 'member', 'viewer'))`
   - unique `(tenant_id, user_id)`
3. `tenant_invitations`
   - tenant, invited email, role, hashed invite token, expiry, accepted time
4. Tenant-owned tables:
   - `campaigns`, `campaign_members`, `conversations`, `messages`
   - `knowledge_entries`, `integrations`, `integration_credentials`
   - `audience_segments`, `strategies`, `creative_assets`
   - `launch_actions`, `approvals`, `execution_runs`, `audit_events`

Use UUID primary keys, foreign keys, `NOT NULL` constraints, and indexes that
start with `tenant_id` for tenant-scoped access paths. Never use a global
mutable demo singleton such as the current `INTEGRATIONS` list in production.

## Supabase/RLS design

- Enable RLS on every exposed tenant-owned table.
- Add membership-based policies using `TO authenticated`; do not use only
  authentication as authorization.
- Centralize membership checks in a small, reviewed helper function in a
  non-exposed schema or use an `EXISTS` membership predicate in policies.
- `SELECT` policies must constrain `tenant_id` through the current user's
  membership.
- `INSERT` policies must require `tenant_id` to equal the authorized tenant.
- `UPDATE` policies require both `USING` and `WITH CHECK` so rows cannot be
  moved between tenants.
- `DELETE` policies must independently enforce membership and role.
- Keep authorization data in `raw_app_meta_data` or database membership rows;
  never authorize from editable `raw_user_meta_data`.
- Use `security_invoker` for views or keep tenant-sensitive views out of the
  exposed schema.
- Do not use `SECURITY DEFINER` as a shortcut around RLS.
- Add storage policies keyed by tenant path, for example
  `tenant_id/campaign_id/asset_id`, and validate both object ownership and
  membership.

## Backend implementation phases

### Phase 1 — Identity and request context

- Replace demo sessions with Supabase token verification.
- Add a FastAPI dependency that returns a typed `RequestContext` containing
  `user_id`, selected `tenant_id`, membership role, and request ID.
- Resolve the tenant only from a server-validated membership lookup.
- Reject missing, expired, malformed, or cross-tenant context with explicit
  `401`/`403` responses.
- Add structured audit logging without logging tokens or credentials.

### Phase 2 — Repository boundary

- Introduce repositories/services that require `RequestContext` for every
  tenant-owned read and write.
- Require `tenant_id` in repository predicates; never expose unscoped
  `get_by_id` helpers.
- Replace route access to module globals with repository calls.
- Ensure list, search, aggregation, background job, and export paths are
  tenant-scoped.
- Add pagination and tenant-leading indexes for all list endpoints.

### Phase 3 — Database and migrations

- Create the tenant and membership tables.
- Add `tenant_id` and foreign keys to every tenant-owned table.
- Enable RLS and add policies before exposing tables through the Data API.
- Grant only the roles required by the API.
- Add migration checks that fail if a tenant-owned table lacks RLS or a
  tenant-leading index.
- Run Supabase security/performance advisors and review every finding.

### Phase 4 — Integrations and secrets

- Store only encrypted provider credentials or Supabase Vault references.
- Keep provider refresh tokens server-side; never return them to the frontend.
- Scope every integration to one tenant and, where needed, one campaign.
- Add role checks for connect, disconnect, credential rotation, and execution.
- Record consent, scopes, actor, timestamp, provider, and outcome in
  `audit_events`.

### Phase 5 — Agent, jobs, and realtime

- Pass `RequestContext` into every agent tool and prompt assembly path.
- Build retrieval filters with mandatory `tenant_id` and campaign scope.
- Ensure background jobs serialize tenant context and re-check membership when
  executing; do not trust stale queued authorization.
- Apply tenant filters to realtime channels and unsubscribe on tenant switch.
- Enforce idempotency keys for consequential actions.

## Frontend hardening

- Treat server-returned tenant metadata as display-only context.
- Never send a user-entered tenant ID as an authorization mechanism.
- Clear campaign, chat, search, and cached integration state on logout or
  tenant switch before rendering the next tenant.
- Namespace client cache keys by authenticated user and tenant ID.
- Do not render fallback demo records after an authenticated tenant request
  fails; show a clear loading/error state instead.
- Keep tenant and membership switching behind an explicit control with the
  server-provided membership list.
- Avoid putting sensitive tenant data in URLs, localStorage, analytics events,
  or error messages.

## Verification plan

- Unit-test token verification, membership lookup, role checks, and repository
  predicates.
- Add RLS tests for two tenants and two users:
  - tenant A cannot select, update, delete, search, or aggregate tenant B data
  - a member cannot perform owner/admin actions
  - a forged tenant ID in the body/header/query is ignored or rejected
  - storage objects cannot cross tenant prefixes
- Add API integration tests for every route, including assistant tools,
  exports, webhooks, jobs, and realtime authorization.
- Run negative tests in CI with a second tenant fixture on every migration.
- Add audit assertions for denied cross-tenant attempts without exposing
  resource existence.

## Review decisions required

1. Should a user have one active tenant at a time, or can one session operate
   across multiple tenant tabs?
2. Which roles may invite members, connect integrations, approve actions, and
   manage billing?
3. Should campaigns be visible to every tenant member or require explicit
   campaign membership?
4. Which provider credentials need campaign-level scope in addition to tenant
   scope?
5. What retention and deletion policy applies to conversations, assets, and
   audit events?
