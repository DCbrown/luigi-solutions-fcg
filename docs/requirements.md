# Requirements

Status: **v1 scope, agreed 2026-07-11.** Anything marked *Later* is explicitly
out of v1 and lives in [roadmap.md](roadmap.md).

> **Day-one cut.** v1 ships in a single day as a thin vertical slice: **one
> scenario** (bakery order page), difficulty hardcoded to `medium`, no project
> history, no Markdown export. The requirements below are unchanged in *shape* —
> the cuts are all breadth, not structure, so nothing here has to be rewritten to
> add them back. Deferred items are marked **[day-2]**. See
> [decisions.md](decisions.md) D7.

## The loop

1. **Generate** — user picks a difficulty; app creates a fictional client, a build
   brief, a seed-content CSV, and a hidden rubric.
2. **Build** — user leaves the app and builds the web app in any stack, in their
   own editor. Target scope: ~2 hours, single page.
3. **Submit** — user pushes to GitHub and pastes the repo URL into the app.
4. **Score** — app clones the repo, runs static checks against the rubric, and
   returns 0–100 with written feedback per criterion.

---

## R1 — Generation

**R1.1** A project is generated from an integer **seed**. The same seed and
difficulty must always produce a byte-identical project. No unseeded randomness
anywhere in the generator.

**R1.2** The generator produces a **Client**: company name, industry, size,
contact person with a name and role, and a paragraph of background. It should
read like a company, not a placeholder.

**R1.3** The generator produces a **Brief** containing:
- background paragraph (why they need this)
- the ask, in the client's words
- **required features** — a list of 3–6 concrete things the page must have
  (search box, contact form, item grid, filter, nav, footer with hours…)
- **required files** — at minimum an entry HTML/app file and a `README.md`
- **constraints** — 1–3 arbitrary-but-plausible rules ("must work on mobile",
  "our brand colour is #2E5C3E", "no carousels, our CEO hates them")

**R1.4** The generator produces a **seed-content CSV** via pandas — the client's
real content that the build must display. Shape depends on scenario (products,
menu items, staff, listings, events). It must contain at least one awkward row
(a very long name, an empty optional field, a special character) so the user has
to handle real content, not tidy content.

**R1.5** The generator derives the **rubric** from the brief at generation time.
Every rubric item points at something the brief actually asked for. The rubric is
stored with the project and **is not shown to the user before submission**.

**R1.6 Difficulty** (`easy` | `medium` | `hard`) scales: number of required
features, number of constraints, rows and messiness of the seed CSV. **[day-2]** —
v1 keeps the parameter in the signature and hardcodes `medium`, so adding this is
additive rather than a refactor.

**R1.7** Projects are saved to `data/generated/<project_id>/` and are listable
and re-openable. See [decisions.md](decisions.md) D5 for the on-disk layout.
*(Saving and loading are v1; browsing past projects in the UI is **[day-2]**.)*

## R2 — Practice

**R2.1** The brief is readable in the app: client, background, ask, required
features, constraints.

**R2.2** The seed CSV is downloadable as a file.

**R2.3** The brief is exportable as Markdown, so the user can keep it open beside
their editor while they work. **[day-2]**

## R3 — Submission

**R3.1** The user submits a **public GitHub repository URL**.

**R3.2** The app performs a **shallow clone** (`--depth 1`) into a temp directory.

**R3.3** The app **never executes** any submitted code. Not a build, not a script,
not a package install. It reads files as text. This is a hard rule, not a
preference — see [quality.md](quality.md) Q5.

**R3.4** Clones are bounded: repo size cap, clone timeout, and a cap on files
read. A submission that exceeds them fails cleanly with a message, rather than
hanging the app.

**R3.5** Failure modes must be legible to the user: bad URL, private repo, repo
not found, network down, repo too large. Each gets its own message.

## R4 — Scoring

Scoring walks the rubric and runs one **check** per item. Four families of check,
all static:

**R4.1 Required files exist** — the brief demanded an entry file and a README;
are they in the tree? Exact, high confidence.

**R4.2 Seed data is used** — do the item names / SKUs / prices from the generated
CSV appear anywhere in the repo's source? Proves the user consumed the client's
content instead of inventing their own. Exact, high confidence — this works
regardless of stack, because the strings have to be *somewhere*.

**R4.3 Required features present** — did they build the search box, the contact
form, the grid? **This check is heuristic and known to be imperfect** (see
[decisions.md](decisions.md) D2). Each feature carries a set of signals — HTML
elements, JSX component names, attribute patterns, handler names — and the check
looks for any of them across the source tree. It will produce false negatives on
some framework projects. The feedback line must therefore say *"no evidence found
of X"*, never *"you did not build X"*.

**R4.4 Code quality signals** — cheap static heuristics that map to real review
comments: semantic elements over div soup, `alt` on images, a responsive viewport
meta tag, a stylesheet rather than inline styles, a README with actual content.

**R4.5 Scorecard** — a weighted score out of 100, plus one line of written
feedback per rubric item saying what was looked for and what was found. Partial
credit is allowed where a check can express it.

**R4.6** Every check is registered by name in a **check registry**, and the rubric
references checks by that name. Adding a check must not require touching the
grader. This is what lets an LLM judge drop in later as just another check.

## R5 — Non-functional

**R5.1** Runs locally, single user, via `streamlit run app/main.py`.

**R5.2** No network calls except the git clone in R3.2. No API keys in v1.

**R5.3** Generation completes in under 2 seconds. Scoring completes in under 30
seconds for a typical repo, clone included.

**R5.4** Stack is Python + pandas + Streamlit, per the project's stated stack.

---

## Later (not v1)

- **LLM judge** for README quality and approach — plugs into the R4.6 registry.
- **Rendered-DOM checking** — fetch the deployed GitHub Pages site and check the
  real DOM instead of guessing from source. This is the actual fix for R4.3's
  weakness (see roadmap Phase 6).
- Zip upload as an alternative to a repo URL.
- Project history, score-over-time, streaks.
- Multi-page and full-CRUD briefs.
- Hosting for multiple users.
