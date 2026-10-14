begin;

-- Preflight: verify RLS state before applying tenant isolation policies.
select
  c.relname as table_name,
  c.relrowsecurity as rls_enabled,
  c.relforcerowsecurity as rls_forced,
  count(p.policyname) as policy_count
from pg_class c
left join pg_policies p
  on p.schemaname = 'public'
 and p.tablename = c.relname
where c.relnamespace = 'public'::regnamespace
  and c.relname in (
    'tenants',
    'tenant_memberships',
    'tenant_invitations',
    'campaigns',
    'conversations',
    'messages',
    'knowledge_entries',
    'integrations',
    'integration_credentials',
    'audience_segments',
    'strategies',
    'creative_assets',
    'launch_actions',
    'approvals',
    'execution_runs',
    'audit_events'
  )
group by c.relname, c.relrowsecurity, c.relforcerowsecurity
order by c.relname;

alter table public.tenants enable row level security;
alter table public.tenant_memberships enable row level security;
alter table public.tenant_invitations enable row level security;
alter table public.campaigns enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.knowledge_entries enable row level security;
alter table public.integrations enable row level security;
alter table public.integration_credentials enable row level security;
alter table public.audience_segments enable row level security;
alter table public.strategies enable row level security;
alter table public.creative_assets enable row level security;
alter table public.launch_actions enable row level security;
alter table public.approvals enable row level security;
alter table public.execution_runs enable row level security;
alter table public.audit_events enable row level security;

alter table public.tenants force row level security;
alter table public.tenant_memberships force row level security;
alter table public.tenant_invitations force row level security;
alter table public.campaigns force row level security;
alter table public.conversations force row level security;
alter table public.messages force row level security;
alter table public.knowledge_entries force row level security;
alter table public.integrations force row level security;
alter table public.integration_credentials force row level security;
alter table public.audience_segments force row level security;
alter table public.strategies force row level security;
alter table public.creative_assets force row level security;
alter table public.launch_actions force row level security;
alter table public.approvals force row level security;
alter table public.execution_runs force row level security;
alter table public.audit_events force row level security;

drop policy if exists tenants_member_select on public.tenants;
create policy tenants_member_select on public.tenants
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = tenants.id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_memberships_self_select on public.tenant_memberships;
create policy tenant_memberships_self_select on public.tenant_memberships
  for select to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists tenant_invitations_admin_select on public.tenant_invitations;
create policy tenant_invitations_admin_select on public.tenant_invitations
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = tenant_invitations.tenant_id
      and m.user_id = (select auth.uid())
      and m.role in ('owner', 'admin')
  ));

drop policy if exists tenant_rows_select on public.campaigns;
create policy tenant_rows_select on public.campaigns
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = campaigns.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.conversations;
create policy tenant_rows_select on public.conversations
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = conversations.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.messages;
create policy tenant_rows_select on public.messages
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = messages.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.knowledge_entries;
create policy tenant_rows_select on public.knowledge_entries
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = knowledge_entries.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.integrations;
create policy tenant_rows_select on public.integrations
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = integrations.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists integration_credentials_member_select on public.integration_credentials;
create policy integration_credentials_member_select on public.integration_credentials
  for select to authenticated
  using (exists (
    select 1
    from public.integrations i
    join public.tenant_memberships m on m.tenant_id = i.tenant_id
    where i.id = integration_credentials.integration_id
      and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.audience_segments;
create policy tenant_rows_select on public.audience_segments
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = audience_segments.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.strategies;
create policy tenant_rows_select on public.strategies
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = strategies.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.creative_assets;
create policy tenant_rows_select on public.creative_assets
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = creative_assets.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.launch_actions;
create policy tenant_rows_select on public.launch_actions
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = launch_actions.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.approvals;
create policy tenant_rows_select on public.approvals
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = approvals.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists tenant_rows_select on public.execution_runs;
create policy tenant_rows_select on public.execution_runs
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = execution_runs.tenant_id and m.user_id = (select auth.uid())
  ));

drop policy if exists audit_events_member_select on public.audit_events;
create policy audit_events_member_select on public.audit_events
  for select to authenticated
  using (exists (
    select 1 from public.tenant_memberships m
    where m.tenant_id = audit_events.tenant_id and m.user_id = (select auth.uid())
  ));

commit;
