# Home — where the implementation stands

**Written 2026-08-19 by Lane A**, updated at `2d43e87b`, **22 commits above
`origin/main` (`7f883ea5`).** This is a resumption note, not a status record —
`PROJECT_STATUS.md` is QE's and is measured from the promoted commit.

---

## What is done

**All four compositions render, and all four have now been seen in a browser.**
Seller and activation routinely; **Executive** at `bd5519fc` and **RevOps** at
`b7ad4ed3`, each of which had only ever had component tests. Both perturbations
of the Playground were reverted — `onboarding_run` is empty, as seeded.

**Thirteen of the fourteen states are implemented and browser-verified.** The
fourteenth is `C-1533` below.

**Contract 5 landed at `60db0cbd`** — the activation registry is served by two
endpoints rather than frozen in the browser bundle, which is what made **state 12
and `AC-H09` reachable at all**. Before it, `home.tsx` carried a state-12 branch
keyed on a client constant that could never be empty.

| | |
|---|---|
| **`GET /workspaces/{id}/integrations/activation-steps`** | `crm_activity` 100 · `meetings` 200, both blocking |
| **`GET /workspaces/{id}/membership/activation-steps`** | `invite_members` 300, not blocking |

**Two endpoints because two modules own the steps**, and `workspace_tenancy` is
the root of the dependency graph — a single composed endpoint would need an edge
the graph does not have. Home composes them by the integer each declares.

---

## What is genuinely outstanding, and whose it is

### The product owner's — filed, indexed, and not blocking anything else

| | |
|---|---|
| **[C-1533](LANE_COORDINATION.md)** | **State 14's entry condition and its copy describe different cards.** The corpus was searched and does not resolve it. ⛔ **State 14 alone is stopped.** `HM_COPY_12` stays in the copy table, unrendered |
| **[C-1534](LANE_COORDINATION.md)** | **Six cards name a dependency no approved document assigns a producer** — `card.forecast`, `card.requests`, `card.dataquality`, `card.briefing`, `card.execsummary`, `card.meetings`. ✅ **Home renders completely without them** |

### This lane's, and open

| | |
|---|---|
| **[B-286](BUGS.md)** | The design's own **light warn tag is 4.078:1** against the 4.5:1 the design states. ⛔ **Not an implementation defect** — the token is `#a5691f` exactly. §20c makes the palette the design's authority. Encoded as `it.fails` in `frontend/tests/unit/home-contrast.test.ts`, so it **reddens the day somebody fixes the palette** |
| **Contract 16** | The stale-figure stamp **has an empty subject**. Measured: no module imports `modules.integrations`, so a disconnected CRM feeds no Home figure. ⛔ **Stamping would be a false claim.** Shares `C-1534`'s root and is recorded there rather than as its own row |

---

## Where to pick up

1. **Rebase onto `main`** (QE promoted `19317ea3` in cycle 249 and did not touch
   this branch). Two things arrive: `attention-route-absence.spec.ts` and
   `refuse_if_head_moved()` in the certification runner.
2. **Push the 15 commits.** QE snapshots whatever tip exists when the next cycle
   opens, and has said it will check `0065` and `0066` for reversibility on a
   **used** database as well as a clean one ([B-1016](BUGS.md)).
3. **Then the remaining implementation**, in the order below.

### ✅ The 22 contract items have now each been checked, one at a time

⚡ **This was a claim before and is a measurement now.** ⛔ **The audit found two
things**, and neither was visible from the outside:

| | |
|---|---|
| **Contract 6** | *"Completed activation cards collapse in place… none is removed from the DOM"* — **true of the implementation and asserted nowhere.** ⚠️ **Home's activation cards had no component test of their own at all.** ✅ Two tests at `2d43e87b` |
| **Contract 12** | *"Each card skeleton uses the card's declared height… **so nothing reflows when data lands**"* — ⛔ **the stated purpose is violated**, and it is [B-283](BUGS.md). ✅ **Partly diagnosed and the Home half fixed** at `859b1bbf` |

**Every other item is implemented and has a check behind it**, except the two the
product owner holds and the one the design holds.

### Remaining work, and none of it is a lane's to decide

| | |
|---|---|
| **[C-1533](LANE_COORDINATION.md)** · **[C-1534](LANE_COORDINATION.md)** | ⛔ **Product owner.** State 14's contradiction, and six cards with no producer |
| **[B-286](BUGS.md)** | ⛔ **The design's palette.** The token is byte-faithful; `it.fails` reddens when the palette is fixed |
| **[B-283](BUGS.md)**, the rest of it | ⚠️ **Its own slice, not a Home one.** What remains is likely in `components/shell/` — 📁 the frozen foundation, where a change affects every screen and needs its own verification |

> ⚡ **Home is at its design-defined completion boundary for everything
> resolvable.** ⛔ **Not "done"** — three of the above are open — **but nothing
> outstanding is waiting on this lane.**

---

## Two things worth not re-learning

**The backend integration suite truncates every table** ([B-282](BUGS.md)). Run
it against a disposable database — create, `alembic upgrade head`, run, drop —
never against the seeded Playground.

**The lane API does not auto-reload.** New backend routes 404 until
`uv run uvicorn apps.api.main:create_app --factory --port 8300` is restarted, and
the symptom looks exactly like a frontend bug.
