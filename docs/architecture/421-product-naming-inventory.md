# 421 — Product naming: the migration inventory

> **Lane C — Product Office, 2026-08-04**, on the product owner's product identity decision. **Brand: Fortune. Product: Signora.** The rule is recorded in [`CLAUDE.md`](../../CLAUDE.md) §4; **this is the inventory only, and it changes nothing.**
>
> Measured against `origin/integration` and against the approved Design Project.

## 1 · The result

> **`git grep "Fortune Signora"` on `origin/integration` returns zero matches. There is nothing in the repository to migrate.**

**The repository already speaks the way the decision requires.** `Signora` appears **315 times in the frontend alone**; the browser title is `Signora`; the package is `signora-frontend`; `README.md` opens `# Signora`.

**So the classification the directive asks for — Branding `KEEP` versus Product Naming `MIGRATE` — has nothing to classify.** The rule is adopted prospectively, and **it is already satisfied by everything that exists.**

## 2 · The one divergence, and it runs the other way

**The directive anticipated a repository over-using the combined brand. The measurement found the opposite: it under-uses it.**

| Surface | Today | The rule says | |
|---|---|---|---|
| **Browser / application title** — `frontend/app/layout.tsx` | `title: 'Signora'` | **Branding surface** — application title and browser title are named explicitly | ⚠️ **The only candidate for change in the whole repository** |
| Everything else — 315 frontend strings, README, package names, module names | `Signora` | `Signora` | ✅ |

> **This is a genuine finding and it is not a bug.** A one-word browser title is a defensible product choice; the new rule says branding surfaces carry the combined brand. **Lane C reports the divergence and does not resolve it** — it is a branding judgement, and the directive explicitly forbids a standalone cosmetic commit.

**Recommendation: leave it.** It converges naturally the next time `layout.tsx` is touched — **which the App Shell convergence will do**, since the approved shell is a 22-section specification and `layout.tsx` is classified `REPLACE` in [413](413-migration-inventory.md).

## 3 · The approved Design Project

**Six occurrences of `Fortune Signora` across the 26 files. Five are the document describing the product; one is the product speaking.**

| Occurrence | | |
|---|---|---|
| *"The **Fortune Signora** application shell"* · *"**Fortune Signora** treats them as a designed system"* · *"A calmer, more confident **Fortune Signora**"* · *"**Fortune Signora** · v2 tokens"* ×2 | **Branding / document prose** | ✅ **KEEP** |
| **App Shell §8** — *"The top-bar field, labelled **'Search Fortune Signora'**"* | **The product speaking to the user.** A placeholder is UI copy | ⚠️ **MIGRATE → `Search Signora`** |

> **One string in the entire approved design set diverges from the new rule**, and it is the search placeholder. **The design project is the product owner's**, so this is reported rather than edited — and it is a one-word change that costs nothing whenever the shell is next touched.

**Everything else in the designs already complies**, including every AI surface: *"Ask Signora"*, *"Signora: deals that slip a third time close 41% of the time"*, *"Signora can explain the setup as you go"*, *"Signora reads your CRM, calls and email"*, *"Signora never sees or stores a password"*. **The assistant is already `Signora` throughout.**

## 4 · What is explicitly not renamed

**The rule lands where [ADR-0034](adr/0034-ubiquitous-language.md) already put the boundary: at the frontend edge, travelling no further inward.**

**`signora_platform` · `signora-frontend` · `signora_app` · `signora_auth` · `signora_relay` · every module, table, column, API path, JWT claim and architecture document — all correct, all unchanged.** These are engineering identifiers, not product identity, and renaming one would be the sweep the directive forbids.

## 5 · Enforcement — the guard already exists

**`frontend/tests/components/vocabulary.test.tsx` enforces ADR-0034 today**, and its own reasoning covers this case exactly:

> *"Every string this would have caught was written deliberately, by an engineer who had read the architecture… They were not carelessness — they are what happens when **the only vocabulary written down is the internal one**, and an engineer reaching for the right word finds `Workspace` because it is the only word the repository has."*
>
> *"A guard that cannot fail is documentation pretending to be code, and **a glossary nobody can violate is the same thing.**"*

> **So the cheapest way to make this rule stick is one more assertion in a test that already runs: no user-facing string contains `Fortune Signora` outside the branding surfaces.** **Lane C recommends it and does not write it** — the frontend is not this lane's, and the test belongs to whoever next touches that file.

**Deliberately not recommended:** a repository-wide lint, a pre-commit hook, or a `state-check` rule. **The repository already complies; a guard against a violation that has never occurred is process spent on nothing.**
