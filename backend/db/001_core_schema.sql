begin;

-- Preflight: inspect the current state before creating or changing tables.
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in (
    'tenants',
    'tenant_memberships',
    'tenant_invitations',
    'campaigns',
    'conversations',
    'messages',
    'knowledge_entries',
    'integrations',
    'audience_segments',
    'strategies',
    'creative_assets',
    'launch_actions',
    'approvals',
    'execution_runs',
    'audit_events'
  )
order by table_name;

create table if not exists public.tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null check (length(trim(name)) between 1 and 160),
  slug text not null unique check (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.tenant_memberships (
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'member'
    check (role in ('owner', 'admin', 'member', 'viewer')),
  created_at timestamptz not null default now(),
  primary key (tenant_id, user_id)
);

create table if not exists public.tenant_invitations (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  invited_email text not null,
  role text not null default 'member'
    check (role in ('admin', 'member', 'viewer')),
  token_hash text not null unique,
  expires_at timestamptz not null,
  accepted_at timestamptz,
  invited_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now()
);

create table if not exists public.campaigns (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  name text not null check (length(trim(name)) between 1 and 200),
  status text not null default 'draft'
    check (status in ('draft', 'research', 'strategy', 'creative', 'launch', 'paused', 'complete')),
  description text not null default '',
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  campaign_id uuid references public.campaigns(id) on delete set null,
  created_by uuid not null references auth.users(id) on delete restrict,
  title text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'tool', 'system')),
  content jsonb not null,
  model_id text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.knowledge_entries (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  title text not null,
  content text not null,
  source_uri text,
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.integrations (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  provider text not null,
  display_name text not null,
  status text not null default 'available'
    check (status in ('available', 'connected', 'paused', 'error')),
  scopes text[] not null default '{}',
  connected_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, provider)
);

create table if not exists public.integration_credentials (
  integration_id uuid primary key references public.integrations(id) on delete cascade,
  secret_reference text not null,
  expires_at timestamptz,
  rotated_at timestamptz not null default now()
);

create table if not exists public.audience_segments (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  campaign_id uuid not null references public.campaigns(id) on delete cascade,
  name text not null,
  evidence jsonb not null default '[]'::jsonb,
  confidence numeric(5, 4) check (confidence between 0 and 1),
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now()
);

create table if not exists public.strategies (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  campaign_id uuid not null references public.campaigns(id) on delete cascade,
  version integer not null check (version > 0),
  content jsonb not null,
  approved_at timestamptz,
  approved_by uuid references auth.users(id) on delete set null,
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  unique (campaign_id, version)
);

create table if not exists public.creative_assets (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  campaign_id uuid not null references public.campaigns(id) on delete cascade,
  asset_type text not null,
  storage_path text,
  content jsonb not null default '{}'::jsonb,
  status text not null default 'draft'
    check (status in ('draft', 'review', 'approved', 'rejected')),
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.launch_actions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  campaign_id uuid not null references public.campaigns(id) on delete cascade,
  integration_id uuid references public.integrations(id) on delete set null,
  action_type text not null,
  payload jsonb not null default '{}'::jsonb,
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'running', 'complete', 'failed', 'cancelled')),
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now()
);

create table if not exists public.approvals (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  action_id uuid not null references public.launch_actions(id) on delete cascade,
  decision text not null check (decision in ('approved', 'rejected')),
  decided_by uuid not null references auth.users(id) on delete restrict,
  reason text,
  created_at timestamptz not null default now()
);

create table if not exists public.execution_runs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  action_id uuid not null references public.launch_actions(id) on delete cascade,
  idempotency_key text not null,
  status text not null default 'queued'
    check (status in ('queued', 'running', 'complete', 'failed', 'cancelled')),
  provider_run_id text,
  result jsonb,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  unique (tenant_id, idempotency_key)
);

create table if not exists public.audit_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references public.tenants(id) on delete cascade,
  actor_user_id uuid references auth.users(id) on delete set null,
  event_type text not null,
  resource_type text,
  resource_id uuid,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists tenant_memberships_user_id_idx
  on public.tenant_memberships (user_id);
create index if not exists tenant_invitations_tenant_id_idx
  on public.tenant_invitations (tenant_id);
create index if not exists campaigns_tenant_id_updated_at_idx
  on public.campaigns (tenant_id, updated_at desc);
create index if not exists conversations_tenant_id_updated_at_idx
  on public.conversations (tenant_id, updated_at desc);
create index if not exists messages_tenant_id_conversation_id_created_at_idx
  on public.messages (tenant_id, conversation_id, created_at);
create index if not exists knowledge_entries_tenant_id_idx
  on public.knowledge_entries (tenant_id);
create index if not exists integrations_tenant_id_idx
  on public.integrations (tenant_id);
create index if not exists integration_credentials_integration_id_idx
  on public.integration_credentials (integration_id);
create index if not exists audience_segments_tenant_id_campaign_id_idx
  on public.audience_segments (tenant_id, campaign_id);
create index if not exists strategies_tenant_id_campaign_id_idx
  on public.strategies (tenant_id, campaign_id);
create index if not exists creative_assets_tenant_id_campaign_id_idx
  on public.creative_assets (tenant_id, campaign_id);
create index if not exists launch_actions_tenant_id_campaign_id_idx
  on public.launch_actions (tenant_id, campaign_id);
create index if not exists approvals_tenant_id_action_id_idx
  on public.approvals (tenant_id, action_id);
create index if not exists execution_runs_tenant_id_action_id_idx
  on public.execution_runs (tenant_id, action_id);
create index if not exists audit_events_tenant_id_created_at_idx
  on public.audit_events (tenant_id, created_at desc);

commit;
