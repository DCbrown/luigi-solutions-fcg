# Quality

The bar for **our** code — not the user's. Five rules. They were chosen because
each one protects something that would otherwise break quietly.

---

## Q1 — The generator and the scorer are tested. The UI is not.

Pytest covers `src/fcg/generator/` and `src/fcg/scoring/`. That's where the value
and all the real logic live. `app/` is a thin Streamlit shell and testing it costs
more than it returns — if a page breaks, you see it immediately on the screen.

A bug in the *scorer*, by contrast, is silent. It hands out a wrong number and
nobody ever knows. So that's where the tests go.

**Definition of done for any generator/scorer change:** a test that fails without
it and passes with it.

## Q2 — Same seed, same project. Enforced by a test.

This is the load-bearing property of the entire app. If a seed doesn't reproduce,
projects aren't shareable, scores aren't comparable, and no bug in the generator
can ever be reproduced from a report.

**The rule:** every source of randomness in the generator descends from the single
seeded `random.Random(seed)` passed down from `generate_project`. Never
`random.choice` at module level, never `datetime.now()` inside generation, never
an unseeded numpy RNG, never a set-iteration order that leaks into output.

**The test:** generate the same seed twice, assert the two `Project` objects and
the two DataFrames are identical. This test is not optional and not slow.

## Q3 — Type hints throughout `src/fcg`.

Full annotations on every function in the package. The generator and the scorer
communicate entirely through the dataclasses in `models.py`, and they're developed
weeks apart — types are what stop the two halves drifting out of contract without
anyone noticing until a score comes out wrong.

The dataclasses in `models.py` are the contract. If you're passing a dict between
modules, you're doing it wrong; add a dataclass.

## Q4 — A check is honest about its confidence.

Some checks are exact: the file is there or it isn't. Some are heuristic: we are
*guessing* whether a React component is a contact form, and we will sometimes be
wrong (see [decisions.md](decisions.md) D2).

Those are different things and the user must never have to guess which one they
just got.

- An exact check may say **"No README.md found."**
- A heuristic check must say **"No evidence of a contact form found."**

Never assert a build is missing a feature when what we actually know is that we
couldn't find it. A scorer that confidently tells a user they didn't build the
thing they definitely built is worse than no scorer at all — they'll stop trusting
every other number on the card.

## Q5 — Submitted code is read, never run.

Hard rule, no exceptions, no "just for the build step."

FCG clones arbitrary repositories from the internet. It opens them as **text**.
It does not execute them, install their dependencies, run their build, or import
them. Every check is static.

If a future feature seems to need execution, it does not get a quiet exception —
it gets a sandbox, a decision record, and a conversation. Until then: read only.

---

## Conventions (not enforced, but follow them)

- **`app/` calls into `src/fcg/` and holds no logic of its own.** Nothing
  generative or scoreable lives in a Streamlit page. Not tested for, but the
  scaffold is built this way and there's no good reason to break it.
- Run `pytest` before you commit. It takes under a second.
- One check per rubric item. If a check is doing two things, it's two checks.
