begin;

-- Preflight: verify whether the legacy chat-mode column exists before removal.
select table_name, column_name, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name = 'messages'
  and column_name = 'mode';

alter table public.messages drop column if exists mode;

commit;
