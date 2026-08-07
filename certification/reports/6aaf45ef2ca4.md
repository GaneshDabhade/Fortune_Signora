# Certification — 6aaf45ef2ca4

**NOT CERTIFIED**  ·  2026-08-07T03:04:00.153188+00:00

## Conditions

- rendering protocol v2
- migration head `0040`
- scenario set `0cf6b2c581e4`
- working tree clean

### Prompt releases in force

- `research_planning@2` on `llama3.1:8b` — `bafc9d282d53`
- `research_synthesis@2` on `llama3.1:8b` — `409a6b2e38a9`

## Gates

- ✅ **import-linter** — 37 kept, 0 broken
- ✅ **mypy** — strict, clean over 814 files
- ❌ **pytest** — 3928 passed
- ✅ **security-invariants** — 392 invariants
- ✅ **smoke** — 24 stages in 158s, slowest 14k. Researched account 20s
- ✅ **tsc** — clean

## Scenarios

- ✅ **baseline@1 research lifecycle** — 190 assertions

Coverage **95.33%**

## Why this run does not certify

- gate 'pytest' failed: 3928 passed

*Certification measures a system with zero production traffic. It is evidence of discipline, not of field reliability.*