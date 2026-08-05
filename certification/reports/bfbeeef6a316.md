# Certification — bfbeeef6a316

**NOT CERTIFIED**  ·  2026-08-05T04:37:25.358590+00:00

## Conditions

- rendering protocol v2
- migration head `0038`
- scenario set `0cf6b2c581e4`
- working tree clean

### Prompt releases in force

- `research_planning@2` on `llama3.1:8b` — `bafc9d282d53`
- `research_synthesis@2` on `llama3.1:8b` — `409a6b2e38a9`

## Gates

- ✅ **import-linter** — 35 kept, 0 broken
- ❌ **mypy** — no summary line
- ✅ **pytest** — 3425 passed
- ✅ **security-invariants** — 383 invariants
- ✅ **smoke** — 24 stages in 138s, slowest 2. Startup 20s
- ✅ **tsc** — clean

## Scenarios

- ✅ **baseline@1 research lifecycle** — 179 assertions

Coverage **95.26%**

## Why this run does not certify

- gate 'mypy' failed: no summary line

*Certification measures a system with zero production traffic. It is evidence of discipline, not of field reliability.*