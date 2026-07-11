# Handoff — 2026-07-11

Written for whoever picks this up next, on a fresh session with no memory of how
it got here.

**Read [vision.md](vision.md) first — it's short, and nothing else makes sense
without it.** Then [decisions.md](decisions.md), especially **D2**, which is the
live risk in this codebase. This file covers only what a `git clone` *doesn't*
tell you.

---

## Where things stand

**v1 is done and the loop closes.** Generate a brief → build the page yourself →
paste a GitHub repo URL → get a score out of 100 with feedback per criterion.
Verified end-to-end against a real cloned repo, including across an app restart.
50 tests pass.

The four steps in [roadmap.md](roadmap.md) are all ✅. What's left is under
"After today", in the order the pain will actually arrive.

## Machine state (none of this is in git)

- Repo: `/Users/donovanbrown/Desktop/dev/project1`, pushed to
  **github.com/DCbrown/luigi-solutions-fcg** (public, `main`).
- **`.streamlit/secrets.toml` is gitignored** and holds the Supabase project
  URL + publishable key for auth (decisions.md D9). On a fresh clone, copy
  `.streamlit/secrets.toml.example` and fill it from the Supabase dashboard
  (project "fcg"). Without it the app won't open — the core library and tests
  don't need it.
- **`venv/` is at the repo root and is gitignored.** Python 3.14, pandas 3.0,
  streamlit 1.59. Use `venv/bin/python`, not the system one.
- The package is **installed editable** (`pip install -e .`). That's why `app/`
  can `import fcg` with no `sys.path` hacks. If imports break on a fresh clone,
  that install is the missing step.
- Run it: `venv/bin/streamlit run app/main.py`. Tests: `venv/bin/python -m pytest`.
- Git identity is set **repo-locally** (Donovan Brown / dess5000@gmail.com), and
  auth is via an ed25519 SSH key added on 2026-07-11. Pushes just work.

## Auth (2026-07-11, decisions.md D9)

The UI now sits behind email/password signup + login, backed by **Supabase
Auth** on the "fcg" project. Read D9 before touching it — it is a deliberate,
*bounded* amendment of D5: identity lives in Supabase, everything else is
still files on disk, and accounts do **not** yet isolate `data/generated/`.

Mechanics: `app/main.py` is now an `st.navigation` router — signed out you get
only `app_pages/login.py`; signed in, the full page set. Pages moved from
`app/pages/` to `app/app_pages/` (the old `pages/` name collides with
Streamlit's legacy auto-discovery, which would have shown every page without
login). `app/auth.py` wraps the Supabase client — created **per browser
session, not `st.cache_resource`**, because the client carries the user's
tokens; don't "optimise" that. Logout calls `st.session_state.clear()` on
purpose, so the next user in the tab doesn't inherit a project or score.

Verified: the publishable key round-trips against the live Auth endpoint
(wrong creds → `Invalid login credentials`), and both auth states render via
`AppTest`. **Not yet done: one real signup with a real inbox** — email
confirmation is on (Supabase default), and nobody has clicked the
confirmation link end-to-end yet.

The "List of projects" page (which replaced the Brief page in the nav) lists
the user's `generation_events` rows and **rebuilds each project from its id**
— `bakery-4471` encodes scenario and seed, and D1 guarantees regeneration is
byte-identical, so no project payload is stored anywhere. The caveat pinned
in `app/history.py`: difficulty is not in the id (it's always "medium", D7);
if difficulty ever becomes real, the table needs a difficulty column.

Generation is capped at 3 per user per calendar week (decisions.md **D10**),
plus one extra request per project *completed* — submitted and scored — that
week (**D11**, one credit per project ever, enforced by a DB unique
constraint). The counters live in Supabase `generation_events` and
`completion_events` tables. The check **fails closed**: if either table is
missing or unreachable, the Generate page blocks with an error rather than
generating uncapped. So both migrations in `supabase/migrations/` must be
run by hand in the Supabase SQL editor **before** deploying code that reads
them — the assistant's MCP access is read-only and cannot apply them.

## The thing that actually needs doing next

**Nobody has ever built a real page and submitted it.**

The whole app has only been exercised against fixtures and against repos that
weren't trying to pass (`octocat/Spoon-Knife` scores ~29/100, correctly). The
"good submission" path is unit-tested with an in-memory fixture, never a real
clone.

So the single most valuable thing is not a feature. It is: **generate a project,
actually build the bakery page in ~2 hours, submit it, and see whether the score
is fair.** Specifically, whether the heuristic feature checks miss things on a
real framework build. That is the D2 risk, and it is currently unmeasured.

If a feature the user definitely built comes back "no evidence found," D2 is
biting, and the fix is already scoped: check the **rendered DOM of the deployed
page** rather than guessing from source. Pull that forward over anything else.

After that: **more scenarios.** There is exactly one (a bakery). It will feel
repetitive on the third project. The generator's *shape* doesn't change when you
add a second scenario — only the seed pools in `data/seeds/` — so this is additive.

## Why the code looks the way it does

Four bugs were found by *running* the thing, not by writing tests first. Each is
now pinned by a test, and each will look like an over-cautious quirk until you
know why it's there:

1. **`MANDATORY_FEATURES` in `generator/brief.py`.** Features used to be sampled
   freely, and a seed produced a brief that never asked for a product listing —
   while 35 points rode on the client's products appearing. It graded something it
   never requested. The product listing is now always required.

2. **`seed_data_used` only requires *available* products.** The seed data
   deliberately marks one item sold out. A dev who thoughtfully hides it was
   losing points — the scorer was punishing good judgment. Don't "fix" this back.

3. **`_normalise()` unescapes HTML entities.** `&amp;` is how a *correct* build
   writes "&", so "Cheese & Onion Pasty" was failing to match on a page that
   escaped it properly — a false negative in a check the user is told is exact.

4. **`_signal_matches()` uses word boundaries; signals are deduped case-insensitively.**
   The signal `Mon` was firing inside "money", awarding an opening-hours section
   nobody wrote. And `"closed"` + `"Closed"` were being counted as *two independent*
   pieces of evidence, faking a confident match out of one hit.

There's a fifth, in `storage.load_seed_data`: pandas may hand `available` back as
real bools *or* as the strings "True"/"False" depending on version. Mapping a
column that's already bool matches nothing, yields `NaN` — and **`NaN` is truthy**,
so every product silently becomes available. The dtype check guarding that is not
paranoia; the bug was introduced by the fix for itself and caught by
`test_storage.py`.

And a sixth, at the top of `app/main.py`: `ARROW_DEFAULT_MEMORY_POOL=system`.
On 2026-07-11 the running app segfaulted (exit 139) in **pyarrow 25.0's bundled
mimalloc** while Arrow-serialising a DataFrame on a Streamlit script thread —
crash report `Python-2026-07-11-153102.ips`, stack through `NdarrayToArrow →
mi_thread_init`. Not reproducible in isolation (250 threaded conversions pass),
so the env var routes Arrow to the system allocator instead of mimalloc. It is
read once, at pyarrow import — which is why it's set before any other import in
main.py. Moving it below an import that pulls in pyarrow silently disables it.

## The rule that holds all of it together

`docs/quality.md` **Q4** — a check must be honest about its confidence.

- **Exact** checks (files present, client's products used) state facts:
  *"No README.md found."*
- **Heuristic** checks (feature detection, quality signals) state evidence:
  *"No evidence of a contact form found."*

Never assert that someone didn't build a thing when all you know is that you
couldn't find it. A scorer that confidently tells a user they didn't build the
feature they definitely built is worse than no scorer at all — they stop trusting
every other number on the card. There is a test enforcing this
(`test_heuristic_failures_never_assert_the_user_didnt_build_it`), and the same
logic is why false *positives* were fixed too: unearned credit discredits a
scorecard exactly as much as unfair blame.

The other hard rule is **Q5: submitted code is never executed.** It's cloned,
read as text, and thrown away. No build, no install, no import. If a feature seems
to need execution, it doesn't get a quiet exception — it gets a sandbox and a
decision record.

## Working preferences observed

- Wants working software fast — v1 was explicitly compressed into a single day,
  and breadth was cut to close the loop ([decisions.md](decisions.md) D7).
- Prefers being told when something is wrong over being agreed with. Two of the
  best decisions here came from pushing back: the "web dev vs data analyst"
  contradiction in the original requirements, and stopping a push to a repo that
  was public when private had been asked for.
