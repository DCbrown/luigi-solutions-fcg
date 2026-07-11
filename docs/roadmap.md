# Phases and Roadmap

**Goal: a working v1 today.** Generate a brief → build against it → submit a repo
→ get a score.

> **Status, 2026-07-11: v1 is done.** All four steps ship. The loop runs
> end-to-end — a generated bakery brief, a real repo cloned from GitHub, a score
> out of 100 with feedback per criterion, surviving an app restart. 37 tests pass.
> Everything below is kept as the record of what was cut and what comes next.

The ordering rule for a one-day build is different from the ordering rule for a
careful one. It isn't "de-risk the hardest thing first" — it's **close the loop
first, then make it good.** One scenario that scores end-to-end beats five
scenarios that can't be submitted. Breadth is what gets cut; the loop is what
gets finished.

So: build a **thin vertical slice** through all four stages, on a single
hardcoded scenario, and only widen once a real repo has gotten a real score.

---

## Phase 0 — Scaffold ✅

Done. Structure, models, package layout, Streamlit shell, tests pass, app boots.

---

## Step 1 — Generator, one scenario ✅

**Ships:** `generate_project(seed)` returns a real `Project` and saves it.

Pick **one** scenario and do it properly: *a small bakery needs a single-page
order site.* Not two scenarios. One.

- `data/seeds/` — enough pools for that one scenario: bakery-ish company names,
  owner names, 15–20 product names with prices and descriptions
- `client.py` — company, contact, background paragraph (Faker, seeded)
- `brief.py` — background, the ask, **4 fixed required features** (item grid,
  contact form, nav, opening hours), 2 constraints, required files
- `dataset.py` — the product CSV, with one awkward row baked in
- `generate_rubric` — derive the scorecard from those features
- `storage.py` — `save_project` / `load_project`
- **One test that matters:** same seed → identical project (quality Q2)

**Checkpoint — do not skip.** Print the brief. Read it as a human. *Would you
build this?* If it reads like filler, fix it now — a dull brief makes everything
downstream pointless, and it is the one thing you cannot fix later by adding code.

## Step 2 — Generate + Brief pages ✅

**Ships:** the practice half, usable.

- Generate page: a button → project, stored in `st.session_state`
- Brief page: client, background, ask, features, constraints
- Download the seed CSV

**This is the first shippable thing.** If the day fell apart right here, you could
still generate a project and go build it. Bank this.

## Step 3 — Ingest ✅

**Ships:** repo URL → dict of `{path: text}`.

- Validate the URL, `git clone --depth 1` to a temp dir, read text files, discard
- Caps: timeout, file count, file size
- **Never execute anything** (quality Q5)
- Errors that say what went wrong: bad URL, private, 404, network

Plumbing, and the only step that ships nothing on its own. Keep it short — resist
every temptation to make it clever.

## Step 4 — Scorer ✅ — **the loop closed here**

**Ships:** v1.

- The check registry plus the four families:
  - `required_files` *(exact)* — index.html and README present?
  - `seed_data_used` *(exact)* — do the product names appear in the source?
  - `feature_present` *(heuristic)* — any signal for this feature in the tree?
  - `quality_signals` *(heuristic)* — viewport meta, `alt` on images, real README
- `grader.py` — walk the rubric, dispatch by name, weight into 0–100
- Submit page: URL box → scorecard with feedback per criterion
- Heuristic failures read **"no evidence found of X"**, never "you didn't build X"
  (quality Q4 — this wording is not a nicety, it's what keeps a wrong check from
  poisoning trust in the right ones)

**Test it for real:** throw a repo at it that you *know* is good and one you know
is bad. If the good one doesn't outscore the bad one, the scorer is decoration.

---

## Cut from today — and why it's safe to cut

Each of these is *additive*. None of them requires reshaping what you build today,
which is exactly why they're the ones to drop.

| Cut | Why it can wait |
| --- | --- |
| **Difficulty levels** | Hardcode `medium`. Keep the parameter in the signature; just ignore it. |
| **More than one scenario** | The generator's shape doesn't change when you add the second one — only its seed pools do. |
| **Project history / list** | `st.session_state` holds the current project. `list_projects()` is already written if you want it cheap. |
| **Brief → Markdown export** | Nice, not load-bearing. Ten minutes, any day. |
| **Zip upload** | Repo URL is the decided path (D4). One submission route is enough. |
| **LLM judge** | Already deferred by D3, and the registry means it plugs in without a rewrite. |
| **Rendered-DOM checking** | The real fix for D2 — but it only matters once people are getting *unfair* scores, which requires people getting scores at all. |

## After today

In the order the pain will actually arrive:

1. **More scenarios.** Repetition is what kills this app, and you'll feel it on
   your fifth project. This is the first thing to fix once the loop works.
2. **Difficulty that actually scales** — feature count, constraint count, data messiness.
3. **Tune the weights** against real submissions. Exact checks should outweigh
   heuristic ones.
4. **Rendered-DOM checking** (old Phase 6) — retires the D2 compromise. Pull this
   forward the moment framework projects start scoring unfairly.
5. **The LLM judge** (old Phase 7) — do it when the deterministic score stops
   discriminating. If everything comes back an 80, the remaining quality is in the
   parts only a reader can judge.
