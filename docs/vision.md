# Vision

## The problem

Practising web development alone has a missing ingredient: **a client.**

Tutorials hand you the requirements *and* the answer. Personal projects let you
quietly redefine the goal whenever it gets hard — you wanted a checkout flow,
you shipped a nav bar, and nobody says otherwise. Neither one rehearses the part
of the job that's actually hard: being handed someone else's messy, opinionated,
half-reasonable requirements and being judged on whether you met them.

You can't practise that without a client. And you can't get a client without a job.

## The idea

FCG invents the client.

It generates a fictional company with a name, an industry, a personality, and a
problem. It writes you a brief — real background, a real ask, specific
deliverables, a couple of arbitrary constraints, the way real ones come. It
hands you a CSV of the company's content: their actual products, their actual
listings, their actual data, that your build has to display.

Then it gets out of the way. You go build it, in whatever stack you like, in
your own editor, on your own time. Roughly two hours of work.

When you're done, you push it to GitHub and paste the link back into FCG. It
reads your repo and scores it against the brief it wrote — not against taste, but
against the requirements it gave you, which it has been holding the whole time.
You get a number and a line of feedback per criterion, so you know exactly which
requirement you dropped.

Then you generate another one, and the client is different.

## What makes this work

**The rubric is written before you are.** FCG derives the scorecard from the
brief at generation time. It cannot move the goalposts after seeing your code,
because it decided how to grade you before you'd written a line. That's the whole
trick — it's why the score means something.

**The client's data is not your data.** The seed CSV forces you to build against
content you didn't choose, with the names and edge cases and awkward lengths
already baked in. You can't design around your data when it isn't yours.

**Same seed, same project.** Every project is reproducible from its seed, so you
can hand a friend a number and you'll both get the identical client, brief, and
data — and your scores will be comparable.

## What success looks like

A developer opens FCG on a Saturday morning, gets a brief from a fictional bakery
that needs an order page, builds it in two hours, submits, scores 78, reads
*"the brief asked for a contact form; none found"*, mutters something, and
generates another one.

That's it. That's the product.

## Non-goals

- **Not a course.** It teaches nothing. It only gives you something to do and
  tells you how you did.
- **Not a judge of taste.** It does not have opinions about your CSS. It checks
  whether you did what the client asked.
- **Not a portfolio host.** Your work lives in your repo. FCG reads it and forgets it.
- **Not multiplayer — though no longer account-less.** Signup/login exists as
  of [decisions.md](decisions.md) D9 (Supabase Auth). Identity is the only
  thing that left the machine: projects, submissions, and scores are still
  files on one disk, and nothing is shared or per-user yet.
