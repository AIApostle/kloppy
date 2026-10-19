# Kloppy database

This folder contains the reviewed Supabase Postgres schema for Kloppy.

## Execution order

Run the SQL files in numeric order through the Supabase MCP `execute_sql`
operation. Each file starts with a preflight query that checks the current
catalog before making its idempotent change. Review the preflight result and
the SQL before executing it against the project.

The schema is tenant-first:

- `tenants` is the business boundary.
- `tenant_memberships` is the server-controlled authorization boundary.
- Tenant-owned records carry `tenant_id` and use membership-based RLS.
- Authorization never relies on editable `raw_user_meta_data`.
- The service-role key is not required for the application schema and must not
  be sent to the browser.

The first migration creates the core campaign, conversation, knowledge,
integration, execution, and audit records needed by the current product. It
does not create fake users or seed demo tenant data. `003_user_settings.sql`
stores each authenticated user's editable profile and approval preference;
RLS scopes every read and write to `auth.uid()`. The application verifies the
Supabase access token and reads this row before processing every agent turn.
`004_remove_chat_modes.sql` removes the legacy message mode column for
databases that applied the earlier core schema.
