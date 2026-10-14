# Project Context & Coding Guidelines

## 1. Project Overview

Kloppy is an AI Marketing Officer that helps businesses move from product and
audience understanding to strategy, campaign asset production, authorized
execution, and performance-informed optimization.

The repository contains:

- A React/Vite frontend workspace for the marketing workspace UI.
- A Python 3.11 backend application using FastAPI, Supabase, and typed
  validation models.
- Project-scoped agent skills under `.agents/skills/`.
- Global Supabase MCP configuration managed outside the repository by VS Code.

The current product requirements are documented in
[PRD.md](./PRD.md), with the implementation plan in
[SOLUTION-APPROACH.md](./SOLUTION-APPROACH.md).

## 2. Executable Commands

Run commands from the directory shown.

### Frontend

Run from `frontend/`:

- **Build:** `npm run build`
- **Dev Server:** `npm run dev`
- **Linting:** `npm run lint`
- **Preview:** `npm run preview`

The frontend does not currently define an `npm test` script. Do not claim that
frontend tests passed unless a test runner is added and executed.

### Backend

Run from `backend/`:

- **Run the application entry point:** `uv run python main.py`
- **Start the FastAPI dev server:** `uv run uvicorn main:app --reload`
- **Dependency lock:** `uv lock`
- **Install or add a dependency:** `uv add <package>`
- **Run backend tests when present:** `uv run pytest`

The backend is pinned to Python 3.11 by `backend/.python-version`.

## 3. Technology Stack & Directory Structure

- `/frontend/src/`: React and TypeScript application source.
- `/frontend/src/assets/`: Frontend image and static assets.
- `/frontend/public/`: Public frontend assets served by Vite.
- `/backend/main.py`: Backend application entry point.
- `/backend/src/`: Supporting backend scripts and modules. Do not move the
  application entry point into this directory.
- `/backend/pyproject.toml`: Backend metadata and Python dependencies.
- `/backend/uv.lock`: Locked Python dependency resolution.
- `/.agents/skills/`: Project-scoped agent skills, including Impeccable and
  Supabase skills.
- `/.vscode/mcp.json`: Ignored workspace MCP override path. The active
  Supabase MCP configuration is global in the user's VS Code profile.
- `/PRD.md`: Product requirements.
- `/SOLUTION-APPROACH.md`: Technical solution approach.

## 4. Architectural Rules & Code Style

- Use TypeScript strict mode and preserve the existing TypeScript compiler
  configuration.
- Prefer functional React components and hooks. Use client-side state only
  when the feature requires it.
- Keep frontend concerns in `frontend/` and backend concerns in `backend/`.
- Keep `backend/main.py` as the backend entry point.
- Use Python type annotations and Pydantic models for API boundaries.
- Keep provider-specific integrations behind typed service or adapter
  boundaries.
- Model campaign work as explicit states and preserve transitions, failures,
  retries, and approvals.
- Keep strategy, audience evidence, brand context, creative assets, and
  execution results linked to the same campaign context.
- Do not silently convert hypotheses, simulated results, or unavailable data
  into facts.
- Do not install new third-party npm packages without asking the user first.
- Python dependencies may be added with `uv add` when required by an approved
  implementation; update and verify `uv.lock`.
- Prefer small, focused modules and repository conventions over speculative
  abstractions.

## 5. Security-First Safety Guardrails

- Never hardcode API keys, access tokens, service-role keys, or credentials.
- Load secrets from secure environment or secret-manager configuration only.
- Never expose Supabase `service_role` or secret keys in frontend code.
- Keep provider credentials server-side; do not place them in prompts, logs,
  generated assets, source control, or browser responses.
- Use least-privilege scopes for Supabase, Qloo, advertising, storage, and
  other provider connections.
- Require explicit user approval before publishing campaigns, spending money,
  changing targeting materially, or changing permissions.
- Distinguish generated, approved, scheduled, published, failed, and simulated
  actions in both API responses and UI.
- Treat Qloo cultural-affinity results as hypotheses, never as proof of
  purchase intent or sensitive individual attributes.
- Do not infer or target sensitive personal traits.
- Validate authentication and authorization on every protected endpoint.
- Enable and correctly scope Row Level Security for exposed Supabase tables.
- Never use user-editable metadata as an authorization source.
- Make retries idempotent where possible and prevent accidental duplicate
  campaign actions.
- Surface provider failures, missing permissions, rate limits, and unavailable
  metrics explicitly. Never return success-shaped fallbacks.
- Do not run destructive database, storage, account, or deployment operations
  without explicit authorization and a reversible plan.

## 6. Development Workflow

1. Read the relevant requirements and existing implementation before editing.
2. Preserve user-provided product facts and existing behavior outside scope.
3. Before changing Supabase schema, SQL, RLS, indexes, or database functions,
   load and follow the applicable Supabase and Postgres best-practices skills.
4. Validate focused behavior first, then run the smallest relevant build,
   lint, or test command.
5. Run frontend lint and build for frontend changes:
   `cd frontend && npm run lint && npm run build`
6. Run backend verification for backend changes:
   `cd backend && uv lock && uv run pytest`
7. If no backend tests exist, at minimum run:
   `cd backend && uv run python main.py`
8. Do not state that a feature is complete until the relevant validation has
   passed.
9. Report simulated integrations and unavailable credentials honestly.

### Commits and Pull Requests

- Use Conventional Commits, for example:
  `feat: add campaign approval workflow`.
- Keep commits focused and explain security-sensitive or behavior-changing
  decisions.
- Include tests or a concrete verification command for behavior changes.
- Never commit secrets, local MCP credentials, `.env` files, or generated
  virtual-environment files.
