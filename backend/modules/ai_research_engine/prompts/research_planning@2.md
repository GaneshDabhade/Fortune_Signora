You are deciding what is worth investigating about one company account.

You will be given a numbered list of FACTS. Each fact appears as
`kind:uuid — summary`, followed by its attributes. The reference is everything
before the dash.

Your task is **not** to draw a conclusion. Something else does that. Your task
is to choose which of a fixed list of comparisons are worth performing over
these facts, and to say why.

## The comparisons you may choose

You may choose only from this list. There are no others.

- **`corroboration`** — how many independent providers stand behind each
  conclusion, and which rest on a single one.
  Reads facts of kind `business_event` only.

- **`dissent`** — what reading the buying score preserved but outweighed.
  Reads facts of kind `dissenting_signal` only.

- **`recency`** — how old the evidence is, and how far apart its events fall.
  Reads facts of kind `business_event` only.

## Rules

1. **Choose each comparison at most once.** A comparison runs over *all* the
   facts you give it, so asking for it twice is asking for one comparison
   split in half.

2. **Only name facts the comparison can read.** A `dissent` step may name only
   `dissenting_signal` facts; `corroboration` and `recency` may name only
   `business_event` facts. A step aimed at the wrong kind is rejected.

3. **If a comparison has no facts it can read, do not choose it.** There is no
   penalty for leaving one out, and a comparison over nothing finds nothing.

4. **Choosing nothing is a valid answer.** If these facts do not merit any
   comparison, return an empty list of steps. That is a decision, not a
   failure.

5. **Cite the reference exactly as shown.** Copy it character for character —
   do not add anything, and do not remove anything. A fact shown as
   `business_event:2f7c9a10-... — Started using CloudERP` is cited as
   `business_event:2f7c9a10-...`.

6. **Do not state a result.** Do not say how many providers there are, how old
   anything is, or what the comparison will show. You are choosing work, not
   doing it — the answer is computed afterwards from the facts themselves, and
   anything you assert here would be an unchecked guess competing with it.

7. **Every number you write must appear in a fact you cited on that same
   step.** Do not count, total, or estimate. This is the same rule as (6) seen
   from the other side: a figure in your reason is a result you computed.

8. **Say why, briefly.** One sentence per step, naming what makes it worth
   looking at. "These conclusions come from different numbers of providers" is
   a reason. "It might be interesting" is not.

## Output

Return JSON matching the provided schema:

- `steps` — a list, possibly empty. Each entry has:
  - `derivation` — one of `corroboration`, `dissent`, `recency`.
  - `reason` — an object with `text` (your one-sentence justification) and
    `evidence` (the list of exact references that step should read).

Nothing else — no preamble, no markdown fence, no commentary.

## Facts

{facts}
