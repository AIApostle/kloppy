# Kloppy

Kloppy is an AI Marketing Officer for founders, small businesses, and lean
marketing teams. It helps turn a business or product brief into audience
research, a coherent campaign strategy, and reviewable marketing deliverables
in one workspace.

Instead of treating research, strategy, and creative as disconnected tasks,
Kloppy keeps work tied to its campaign context so that insights can inform the
strategy and the strategy can guide the content.

## What it does

- **Campaign workspace:** Create and manage campaigns, keep campaign context
  together, and continue campaign-specific conversations.
- **AI marketing chat:** Work through campaign goals, briefs, audience
  hypotheses, strategy, and creative direction with focused follow-up
  questions.
- **Audience research:** Use Qloo, when configured, to explore cultural
  affinities and related entities. These signals are directional evidence, not
  proof of purchase intent or attributes of individual people.
- **Web research:** Search for current or specialized public information with
  Tavily when it would materially help. Search results include source links.
- **Visual examples:** Ask Kloppy for web image examples and receive a small
  gallery of linked, third-party images in the conversation. Image previews
  are examples, not original Kloppy assets or cleared usage rights.
- **Campaign documents:** Create campaign plans and other substantial
  deliverables as downloadable Word documents. Campaign plans include
  Overview, Audience, Strategy, and Launch & Learn sections.
- **Interactive chat controls:** Answer blocking popup questions, stop a
  running response, edit a previous message and regenerate from it, and copy
  Kloppy's replies.
- **Workspace knowledge and integrations:** Add brand knowledge and configure
  allowlisted, read-only tools from compatible MCP servers.
- **Project-scoped memory:** When Walrus Memory is configured, retain selected
  durable user-provided facts in isolated workspace or campaign namespaces.

Publishing, spending, and other consequential external actions require
explicit authorization. The current MCP connector exposes only tools marked
read-only; the integration catalog should not be interpreted as a promise that
every listed provider has a built-in OAuth connection or write capability.

## Technology

- **Frontend:** React, TypeScript, and Vite.
- **Backend:** Python 3.11+, FastAPI, and Strands Agents.
- **Authentication and data:** Supabase Auth and Postgres with row-level
  security policies.
- **Agent model access:** OpenRouter.
- **Optional capabilities:** Qloo audience research, Tavily web and image
  search, Walrus Memory, and configured MCP servers.

## Repository layout

```text
backend/
  db/                 Supabase SQL migrations and database notes
  src/app/            FastAPI application, routes, services, and prompts
  tests/              Backend unit tests
frontend/
  src/                React application and styles
PRODUCT.md             Product context and principles
PRD.md                 Product requirements
SOLUTION-APPROACH.md   Product and technical approach
```

## Run locally

### Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- A Supabase project for authentication and data

### Configure the backend

Create a local environment file from the example:

```bash
cp backend/.env.example backend/.env
```

Set the required backend values in `backend/.env`, including the Supabase
project URL, Supabase publishable/anonymous key, and OpenRouter API key. Optional
provider keys enable their corresponding capabilities:

- `QLOO_API_KEY` for audience research
- `TAVILY_API_KEY` for web and image search
- `MEMWAL_PRIVATE_KEY` and `MEMWAL_ACCOUNT_ID` for Walrus Memory

Keep credentials in backend environment variables. Do not commit `.env` files
or place server-side provider keys in frontend configuration.

Install backend dependencies and start the API:

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000
```

The API health endpoint is available at `http://localhost:8000/health`.

### Configure the database

Apply the SQL migrations in [`backend/db/`](/home/ai-apostle/Projects/kloppy/backend/db)
to the Supabase project in numeric order. Review the database notes in
[`backend/db/README.md`](/home/ai-apostle/Projects/kloppy/backend/db/README.md)
before applying migrations.

### Configure and start the frontend

In another terminal, create the frontend environment file:

```bash
cp frontend/.env.example frontend/.env
```

To connect the local frontend to the local API, set this in `frontend/.env`:

```dotenv
VITE_API_URL=http://localhost:8000/api
```

Then install frontend dependencies and start Vite:

```bash
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite. The application also supports the hosted
API; the frontend API URL can be changed with `VITE_API_URL`.

## Database and security

The application uses Supabase Auth for user sessions and Postgres row-level
security to scope user data. The backend verifies authenticated sessions and
keeps provider credentials server-side. User-configured MCP credentials are
encrypted before storage; configure a stable `INTEGRATION_ENCRYPTION_KEY` as
described in the backend environment example and database README.

For a fuller description of provider setup, logs, memory, and integration
constraints, see [`backend/README.md`](backend/README.md).

## Development checks

Run the backend tests:

```bash
cd backend
uv run python -m unittest discover -s tests
```

Build and lint the frontend:

```bash
cd frontend
npm run build
npm run lint
```

## Product documentation

- [Product context](PRODUCT.md)
- [Product requirements](PRD.md)
- [Solution approach](SOLUTION-APPROACH.md)
