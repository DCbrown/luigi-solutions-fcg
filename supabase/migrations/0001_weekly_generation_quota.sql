-- Weekly generation quota (docs/decisions.md D10).
--
-- One row per project generation. The app counts a user's rows in the
-- current calendar week (Monday 00:00 UTC) and refuses to generate past 3.
--
-- Not applied automatically: the assistant's Supabase access is read-only,
-- so run this in the Supabase dashboard (SQL Editor) against the "fcg"
-- project before deploying code that reads it.

create table public.generation_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  project_id text not null,
  created_at timestamptz not null default now()
);

alter table public.generation_events enable row level security;

-- Users see and record only their own events. No update/delete policies on
-- purpose: quota rows are append-only from the client's point of view.
create policy "users read own generation events"
  on public.generation_events for select
  to authenticated
  using ((select auth.uid()) = user_id);

create policy "users record own generation events"
  on public.generation_events for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

create index generation_events_user_created
  on public.generation_events (user_id, created_at);
