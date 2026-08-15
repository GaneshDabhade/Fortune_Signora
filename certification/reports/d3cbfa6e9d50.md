# Certification — d3cbfa6e9d50

**NOT CERTIFIED**  ·  2026-08-15T20:06:04.531852+00:00

## Conditions

- rendering protocol v2
- migration head `0057`
- scenario set `e5b92f4872fc`
- working tree clean

### Prompt releases in force

- `research_planning@2` on `llama3.1:8b` — `bafc9d282d53`
- `research_synthesis@2` on `llama3.1:8b` — `409a6b2e38a9`

## Gates

- ✅ **eslint** — clean
- ❌ **frontend-suite** — 1 failed
- ✅ **import-linter** — 37 kept, 0 broken
- ✅ **mypy** — strict, clean over 911 files
- ✅ **pytest** — 4950 passed
- ✅ **security-invariants** — 458 invariants
- ✅ **smoke** — 24 stages in 221s, slowest 2. Startup 23s
- ✅ **tsc** — clean

## Scenarios

- ✅ **baseline@1 research lifecycle** — 190 assertions

Coverage **95.03%**

## Why this run does not certify

- gate 'frontend-suite' failed: 1 failed

*Certification measures a system with zero production traffic. It is evidence of discipline, not of field reliability.*