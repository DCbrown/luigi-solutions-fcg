-- Completion credits (docs/decisions.md D11).
--
-- A scored submission marks its project complete, and each completion adds
-- one generation request to the current week's allowance. One credit per
-- project, ever: the unique constraint makes resubmitting the same project
-- a no-op, at the database level rather than by app politeness.
--
-- Run by hand in the Supabase SQL editor (assistant access is read-only),
-- BEFORE deploying code that reads it — the quota check fails closed.

create table public.completion_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  project_id text not null,
  score numeric not null,
  created_at timestamptz not null default now(),
  unique (user_id, project_id)
);

alter table public.completion_events enable row level security;

create policy "users read own completions"
  on public.completion_events for select
  to authenticated using ((select auth.uid()) = user_id);

create policy "users record own completions"
  on public.completion_events for insert
  to authenticated with check ((select auth.uid()) = user_id);

create index completion_events_user_created
  on public.completion_events (user_id, created_at);
