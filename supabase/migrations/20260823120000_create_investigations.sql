create table public.investigations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  status text not null default 'running',
  current_step text,
  steps jsonb not null default '[]'::jsonb,
  namespace text,
  root_cause text,
  explanation text,
  fix text,
  kubectl_command text,
  confidence integer,
  message text
);

create index investigations_user_created_idx
  on public.investigations (user_id, created_at desc);

alter table public.investigations enable row level security;

create policy "users_select_own_investigations"
  on public.investigations
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

create policy "users_insert_own_investigations"
  on public.investigations
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

create policy "users_update_own_investigations"
  on public.investigations
  for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

grant select, insert, update on table public.investigations to authenticated;
revoke all on table public.investigations from anon;

alter table public.investigations replica identity full;

do $$
begin
  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'investigations'
  ) then
    execute 'alter publication supabase_realtime add table public.investigations';
  end if;
end
$$;
