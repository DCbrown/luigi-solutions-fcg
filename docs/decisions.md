# Decisions

Each entry: what we chose, what we gave up, and what would make us change our
minds. Newest decisions go at the bottom.

---

## D1 — Everything derives from a seed

**Decided:** 2026-07-11

A project is a pure function of `(seed, difficulty)`. All randomness flows from
one `random.Random(seed)` threaded down through the generator.

**Why:** it makes projects shareable ("try seed 4471"), scores comparable across
people, and generator bugs reproducible from a single integer. It costs almost
nothing to do and is very expensive to retrofit — an unseeded `random.choice`
buried three modules deep is a miserable thing to find later.

**Cost:** mild discipline tax forever. No `datetime.now()` in generation, no
module-level RNG, no leaking set-iteration order into output.

**Revisit if:** never, realistically. This one's load-bearing.

---

## D2 — "Any stack" + static checks: we accept heuristic feature detection

**Decided:** 2026-07-11 · **This is the riskiest decision in the project.**

The user may build in any stack they like (vanilla, React, Vue, Svelte,
whatever). The scorer reads their repo as **text** and never runs it.

These two facts are in real tension, and it's worth being blunt about why. In a
vanilla project, `index.html` *is* the shipped page — searching it for
`<form>` tells you the truth. In a React project, the shipped DOM does not exist
until a build runs. What's in the repo is JSX, split across components, possibly
with the word "form" nowhere in it at all.

**So feature detection cannot be exact, and we are not going to pretend it is.**

**What we're doing instead:** each required feature carries a *bundle of signals* —
HTML elements, JSX component names, attribute patterns, common handler names,
library imports — and the check searches the whole source tree for any of them.
It's grep with domain knowledge, not a DOM query.

**Consequences we accept:**
- False negatives on framework projects. A user who built a contact form as
  `<ContactWidget/>` may not get credit for it.
- Every heuristic check must report as *"no evidence found of X"*, never *"you
  didn't build X"* ([quality.md](quality.md) Q4). The honesty of the wording is
  what keeps a wrong check from poisoning the user's trust in the right ones.
- Feature checks get **lower rubric weight** than the exact checks (files exist,
  seed data used), because we're less sure of them. The score leans on what we
  actually know.

**What we considered and rejected for v1:**
- *Vanilla-only briefs* — would make checks exact, but rules out the frameworks
  most web devs actually want to practise. Wrong trade for the audience.
- *Per-framework AST parsers* — accurate, but that's a parser per stack, forever,
  and it's most of the project. Not v1.
- *Running the build* — the fix that actually works, and the one thing we've ruled
  out on safety ([quality.md](quality.md) Q5).

**Revisit if:** users report unfair scores on framework projects. The real fix is
already scoped — **check the rendered DOM of the deployed site** instead of
guessing from source (roadmap Phase 6). That turns the hardest check into an exact
one and retires this whole compromise. If D2 starts hurting, pull Phase 6 forward.

---

## D3 — Deterministic checks now, LLM judge later

**Decided:** 2026-07-11

v1 scores with code only. No API key, no cost per submission, no network beyond
the clone.

**Why:** the loop (generate → build → submit → score) is the thing that has to
work. It's cheaper to find out the *generator* is boring than to find out the
*judge* is expensive. And deterministic scores are reproducible, which pairs with
D1.

**The hedge:** checks live in a **registry** (`scoring/checks.py`), and the rubric
references them by name. An LLM judge is then just another registered check — it
gets a submission and returns `(fraction, feedback)` like everything else. The
grader never learns it exists.

**Cost:** v1 can't grade the things only a human can see — is the README any good,
is the approach sane, is the code well-organised. Those are real and we're
deferring them.

**Revisit if:** the deterministic score stops discriminating — i.e. everyone gets
80 and the number stops being interesting. That's the signal that the remaining
quality lives in the parts only a judge can read.

---

## D4 — Submit a GitHub repo URL, not a zip

**Decided:** 2026-07-11

Shallow clone (`--depth 1`) into a temp dir, read, discard.

**Why:** pushing your work to a repo is what actually happens on the job, and the
habit is worth rehearsing. It also gives us a whole file tree rather than whatever
the user remembered to zip.

**Cost:** requires network and `git` on the machine, and the repo must be public.
Failure modes multiply (bad URL, private repo, 404, timeout, giant repo) and each
one needs its own legible error — see requirements R3.5.

**Guardrails:** shallow clone only, size cap, clone timeout, file-count cap, and
**never execute** anything in the tree (Q5).

**Revisit if:** the friction of "you must push to GitHub first" turns out to stop
people submitting. Zip upload is a small addition and can coexist.

---

## D5 — Files on disk, no database

**Decided:** 2026-07-11

```
data/generated/<project_id>/project.json     the Project, serialised
data/generated/<project_id>/seed_data.csv    what the user downloads
data/generated/<project_id>/rubric.json      hidden until submission
data/submissions/<project_id>/               clone artefacts and scorecards
```

**Why:** single user, single machine, small data. A database would be pure
ceremony. JSON is diffable and inspectable, which matters a lot while the
generator is still being tuned — you can just *look* at what it made.

**Cost:** no querying, no concurrency, no history across machines.

**Revisit if:** this ever goes multi-user. Then `storage.py` is the seam that
absorbs it — that's why the file layout is behind functions instead of scattered
`open()` calls.

---

## D6 — The rubric is written at generation time, and hidden

**Decided:** 2026-07-11

The rubric is derived from the brief when the project is generated, stored with
it, and not shown to the user until they've submitted.

**Why:** two reasons, and both matter.

*Integrity:* the app decides how it will grade you before it has seen your code.
It cannot rationalise a score after the fact, because the goalposts were planted
first.

*Realism:* clients don't hand you their scoring matrix. Reading the brief closely
enough to work out what actually counts **is the skill being practised.** Showing
the rubric up front would turn the exercise into filling in a checklist, which is
precisely the tutorial-shaped thing this app exists to escape.

**Cost:** a user who scores badly may feel ambushed. Mitigated by the feedback
line on every criterion — after submission, exactly what was looked for is
visible, and the brief always did say so.

**Revisit if:** users find it punishing rather than instructive. A "reveal rubric"
escape hatch after a first submission would be a reasonable compromise.

---

## D7 — v1 is a thin vertical slice, built in a day

**Decided:** 2026-07-11

Ship the whole loop — generate → build → submit → score — on **one hardcoded
scenario**, today. Cut breadth: one scenario, no difficulty scaling, no history,
no export.

**Why:** an app that generates five kinds of beautiful brief and can't score
anything is not 60% of this product — it's 0% of it, because the thing being
tested is *the loop*. Until a real repo gets a real number back, every assumption
in this project is still unverified, including the ones that would be expensive to
be wrong about (are the checks even discriminating? is a two-hour brief the right
size?). A slice answers those on day one.

**Why it's safe:** every cut is *additive*. Adding a second scenario changes the
seed pools, not the generator's shape. Difficulty stays in the function signature
and is simply ignored. History is a listing over a directory that's already being
written. None of it forces a rewrite of what gets built today — which is the whole
test of whether a cut is safe to make.

**Cost:** the app will feel repetitive immediately — there is exactly one client
and one kind of brief. That's fine on day one and intolerable by day three, so
"more scenarios" is the first thing after the loop closes.

**The risk this doesn't cover:** a thin slice proves the machinery works. It does
*not* prove the briefs are interesting, and a boring generator kills this product
no matter how well the scorer runs. That's why Step 1 has a human checkpoint —
read the brief, ask whether you'd actually build it — before any scoring code gets
written.

**Revisit if:** the slice closes early. Then spend the remaining time on scenarios,
not on difficulty levels.
