# Certification — b7cdb9c863fa

**CERTIFIED**  ·  2026-08-29T06:48:28.322860+00:00

## Conditions

- rendering protocol v2
- migration head `0066`
- scenario set `e5b92f4872fc`
- working tree clean

### Prompt releases in force

- `research_planning@2` on `llama3.1:8b` — `bafc9d282d53`
- `research_synthesis@2` on `llama3.1:8b` — `409a6b2e38a9`

## Gates

- ✅ **eslint** — clean
- ✅ **frontend-suite** — 4511 passed in 265 files
- ✅ **import-linter** — 37 kept, 0 broken
- ✅ **mypy** — strict, clean over 959 files
- ✅ **pytest** — 5468 passed
- ✅ **security-invariants** — 680 invariants
- ✅ **smoke** — 24 stages in 150s, slowest 2. Startup 19s
- ✅ **tsc** — clean

### Planned and NOT recorded

The Validation Planner required these for this run's `platform` diff and this record does not contain them. **They did not run inside certification** — whether they ran by hand is not something this record can know (B-131).

- ⚠️ **accessibility**
- ⚠️ **doc-drift**
- ⚠️ **dr**
- ⚠️ **event-catalog**
- ⚠️ **migration-reversibility**
- ⚠️ **prompt-evaluation**
- ⚠️ **reachability**
- ⚠️ **runtime-composition**
- ⚠️ **state-check**

## Scenarios

- ✅ **baseline@1 research lifecycle** — 208 assertions

Coverage **95.05%**

*Certification measures a system with zero production traffic. It is evidence of discipline, not of field reliability.*