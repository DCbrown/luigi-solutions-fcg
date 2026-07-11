-- Difficulty per generation (docs/decisions.md D12).
--
-- The user's level (junior/mid/senior) lives in Supabase Auth user_metadata
-- and needs no table. But the List of projects page rebuilds each project
-- from (scenario, seed) — and once difficulty varies, a faithful rebuild
-- needs to know which difficulty the project was generated at. Existing
-- rows default to 'medium', which is what every past generation used.
--
-- Run by hand in the Supabase SQL editor BEFORE deploying code that writes
-- it (a missing column makes generation fail with a visible error).

alter table public.generation_events
  add column difficulty text not null default 'medium';
