# Certification — eaecf496e3c4

**CERTIFIED**  ·  2026-08-26T13:13:12.557992+00:00

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
- ✅ **frontend-suite** — 4167 passed in 228 files
- ✅ **import-linter** — 37 kept, 0 broken
- ✅ **mypy** — strict, clean over 957 files
- ✅ **pytest** — 5459 passed
- ✅ **security-invariants** — 679 invariants
- ✅ **smoke** — 24 stages in 215s, slowest 1. Build 67s
- ✅ **tsc** — clean

### Planned and NOT recorded

The Validation Planner required these for this run's `documentation+frontend` diff and this record does not contain them. **They did not run inside certification** — whether they ran by hand is not something this record can know (B-131).

- ⚠️ **accessibility**
- ⚠️ **doc-drift**
- ⚠️ **reachability**
- ⚠️ **state-check**

## Scenarios

- ✅ **baseline@1 research lifecycle** — 208 assertions

Coverage **95.03%**

*Certification measures a system with zero production traffic. It is evidence of discipline, not of field reliability.*