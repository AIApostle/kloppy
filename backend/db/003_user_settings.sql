begin;

-- Preflight: confirm whether authenticated users already have a settings row.
select count(*) as settings_table_exists
from information_schema.tables
where table_schema = 'public' and table_name = 'user_settings';

create table if not exists public.user_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  name text not null default '' check (length(name) <= 80),
  workspace text not null default '' check (length(workspace) <= 120),
  digest_enabled boolean not null default true,
  permission_policy text not null default 'ask'
    check (permission_policy in ('ask', 'auto')),
  updated_at timestamptz not null default now()
);

alter table public.user_settings enable row level security;
alter table public.user_settings force row level security;

drop policy if exists user_settings_select_self on public.user_settings;
create policy user_settings_select_self on public.user_settings
  for select to authenticated
  using (user_id = (select auth.uid()));

drop policy if exists user_settings_insert_self on public.user_settings;
create policy user_settings_insert_self on public.user_settings
  for insert to authenticated
  with check (user_id = (select auth.uid()));

drop policy if exists user_settings_update_self on public.user_settings;
create policy user_settings_update_self on public.user_settings
  for update to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

grant select, insert, update on public.user_settings to authenticated;

commit;
