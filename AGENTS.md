# AGENTS.md

Canonical multi-agent contract for this repository. Other adapters (`CLAUDE.md`)
point here — do not duplicate rules.

**Abraxas Orchestra** is a local Hermes / OpenClaw skill (`name: orchestra`).
It maps software onto fail-closed correspondence maps, emits dual-named
skeletons and diagrams, and observes existing trees before any gated rename.

It is not a network service, a magic runtime, or a hosted Worker. Do not copy
Noema deploy, pin, or ACK procedures into this skill repo.

## Authority

| Surface | Role |
|---|---|
| [`SKILL.md`](SKILL.md) | Hermes / OpenClaw skill contract. Do not rewrite unless a CLI contract change is authorized. |
| [`references/agent-posture.md`](references/agent-posture.md) | How agents fill emitted skeletons |
| [`schemas/frameworks.v1.json`](schemas/frameworks.v1.json) | Canonical loci — do not invent names |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Live write-surface / threat model |
| [`docs/CI.md`](docs/CI.md) | `main` requires a PR and green `ci-ok` |

## Route first

Same groups as `SKILL.md` and `scripts/orchestra_router.py`: **meta** · **emit** · **repo**.

| User wants… | Group | Commands |
|---|---|---|
| Health / which maps exist | **meta** | `check`, `list` |
| Unsure of flags / Desktop chat collect | **meta** | `wizard` |
| New dual-named skeleton or diagram | **emit** | `structure`, `project`, `diagram` |
| Observe / map / refactor an existing tree | **repo** | `analyze`, then `optimize` |

Prefer CLI emission over freehand Mermaid. Prefer **wizard** when unsure.
Do not invent argv or loci.

## Critical invariants

- Do not invent loci outside `schemas/frameworks.v1.json`.
- `WEAK` / `FORCED` / `NOT_COMPUTABLE` fail closed. Do not paper over them.
- `optimize` is plan-only unless the operator explicitly approved `--apply --confirm`.
- Emit and repo CLI paths are local stdlib Python. No network I/O.
- Keep mutable agent state outside the skill install root.
- Do not force-push `main` or bypass required checks.

## Escalation

If CI or tests look wrong, open a labeled defect (`bug`). Do not edit tests or
fixtures to force green. Do not reward-hack.

## SDLC

Non-trivial product changes start here:

1. `intent.md` — copy [`intent/_TEMPLATE.md`](intent/_TEMPLATE.md); see [`intent/README.md`](intent/README.md).
2. spec / design note under `docs/` (or `docs/superpowers/specs/` when using that workflow)
3. plan
4. implement

Clarifications, adapters, and docs-only hygiene that do not change the CLI,
schemas, or install contract may skip this sequence. Do not invent intent
records for already-shipped work.

## Verify

```bash
bash scripts/smoke.sh
python3 scripts/orchestra.py check
python3 scripts/integrity_check.py
```

Install / host wiring: [`docs/DEPLOY.md`](docs/DEPLOY.md). Semver: [`docs/SEMVER.md`](docs/SEMVER.md).
