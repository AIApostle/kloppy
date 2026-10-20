begin;

-- User-owned brand knowledge and MCP server connections.
create table if not exists public.brand_sources (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (length(trim(title)) between 1 and 200),
  content text not null check (length(content) between 1 and 100000),
  source_type text not null check (source_type in ('brand_text', 'document')),
  file_name text check (file_name is null or length(file_name) <= 255),
  created_at timestamptz not null default now()
);

create index if not exists brand_sources_user_created_idx
  on public.brand_sources (user_id, created_at desc);

alter table public.brand_sources enable row level security;
alter table public.brand_sources force row level security;

drop policy if exists brand_sources_self_select on public.brand_sources;
create policy brand_sources_self_select on public.brand_sources
  for select to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists brand_sources_self_insert on public.brand_sources;
create policy brand_sources_self_insert on public.brand_sources
  for insert to authenticated
  with check (user_id = (select auth.uid()));

drop policy if exists brand_sources_self_delete on public.brand_sources;
create policy brand_sources_self_delete on public.brand_sources
  for delete to authenticated
  using (user_id = (select auth.uid()));

grant select, insert, delete on public.brand_sources to authenticated;

create table if not exists public.user_mcp_servers (
  user_id uuid not null references auth.users(id) on delete cascade,
  provider text not null check (provider ~ '^[a-z0-9_-]{1,64}$'),
  display_name text not null check (length(trim(display_name)) between 1 and 100),
  server_url text not null check (length(server_url) <= 2048),
  encrypted_token text not null default '',
  allowed_tools text[] not null check (cardinality(allowed_tools) between 1 and 40),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, provider)
);

alter table public.user_mcp_servers enable row level security;
alter table public.user_mcp_servers force row level security;

drop policy if exists user_mcp_servers_self_select on public.user_mcp_servers;
create policy user_mcp_servers_self_select on public.user_mcp_servers
  for select to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists user_mcp_servers_self_insert on public.user_mcp_servers;
create policy user_mcp_servers_self_insert on public.user_mcp_servers
  for insert to authenticated
  with check (user_id = (select auth.uid()));

drop policy if exists user_mcp_servers_self_update on public.user_mcp_servers;
create policy user_mcp_servers_self_update on public.user_mcp_servers
  for update to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

drop policy if exists user_mcp_servers_self_delete on public.user_mcp_servers;
create policy user_mcp_servers_self_delete on public.user_mcp_servers
  for delete to authenticated
  using (user_id = (select auth.uid()));

grant select, insert, update, delete on public.user_mcp_servers to authenticated;

-- Public, non-secret provider catalog. Backend code remains the source of
-- provider definitions; these rows make the supported catalog queryable.
create table if not exists public.integration_catalog (
  id text primary key check (id ~ '^[a-z0-9_-]{1,64}$'),
  name text not null check (length(trim(name)) between 1 and 100),
  kind text not null check (kind in ('Application', 'Resource')),
  category text not null check (length(trim(category)) between 1 and 80),
  description text not null check (length(trim(description)) between 1 and 500),
  sort_order smallint not null unique check (sort_order > 0),
  updated_at timestamptz not null default now()
);

alter table public.integration_catalog enable row level security;
alter table public.integration_catalog force row level security;

drop policy if exists integration_catalog_authenticated_read on public.integration_catalog;
create policy integration_catalog_authenticated_read on public.integration_catalog
  for select to authenticated
  using (true);

grant select on public.integration_catalog to authenticated;
revoke insert, update, delete, truncate, references, trigger on public.integration_catalog from anon, authenticated;

insert into public.integration_catalog (id, name, kind, category, description, sort_order)
values
  ('meta-ads', 'Meta Ads', 'Application', 'Paid social', 'Read Meta Ads account and campaign context through an allowlisted MCP server.', 1),
  ('google-ads', 'Google Ads', 'Application', 'Paid search', 'Read Google Ads account and campaign context through an allowlisted MCP server.', 2),
  ('hubspot', 'HubSpot', 'Application', 'CRM', 'Read CRM records and lifecycle context through an allowlisted MCP server.', 3),
  ('mailchimp', 'Mailchimp', 'Application', 'Email', 'Read email campaign and audience context through an allowlisted MCP server.', 4),
  ('canva', 'Canva', 'Application', 'Design', 'Read connected design files and brand assets through an allowlisted MCP server.', 5),
  ('figma', 'Figma', 'Resource', 'Design files', 'Read campaign boards and brand systems through an allowlisted MCP server.', 6),
  ('google-drive', 'Google Drive', 'Resource', 'Knowledge', 'Read briefs, research, and campaign files through an allowlisted MCP server.', 7),
  ('notion', 'Notion', 'Resource', 'Knowledge', 'Read launch notes and brand context through an allowlisted MCP server.', 8),
  ('ga4', 'Google Analytics', 'Resource', 'Performance', 'Read analytics reports through an allowlisted MCP server.', 9),
  ('shopify', 'Shopify', 'Application', 'Commerce', 'Read product and storefront context through an allowlisted MCP server.', 10)
on conflict (id) do update set
  name = excluded.name,
  kind = excluded.kind,
  category = excluded.category,
  description = excluded.description,
  sort_order = excluded.sort_order,
  updated_at = now();

notify pgrst, 'reload schema';

commit;
