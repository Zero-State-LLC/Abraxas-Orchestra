# intent/ — SDLC intent records

**Kind:** process. Not a specification. Not implementation authority. Does not
authorize a CLI change, schema change, skill rewrite, or any production publish.

Non-trivial product changes start here. Copy [`_TEMPLATE.md`](_TEMPLATE.md) to a
dated file (`YYYY-MM-DD-short-slug.md`). Fill every section. Label claims
`OBSERVED`, `INFERRED`, `SPECULATIVE`, or `NOT_COMPUTABLE`.

## Sequence

`intent.md` → spec / design note under `docs/` → plan → implement.

The next stage after a filled intent is a design note or spec (existing
`docs/DESIGN.md` surface, or `docs/superpowers/specs/` when using that
workflow). Plan and implement stay in this repository. Do not treat an intent
as acceptance or a release.

Clarifications, adapters, and docs-only hygiene that do not change the CLI,
schemas, or install contract may skip this sequence.

## Holds

- An intent is not a spec, not a plan, and not a release. It does not authorize
  implementation or production.
- Do not invent intent records for already-shipped work.
- Do not invent symbolic loci, CLI flags, or schema fields here.
- Do not rewrite [`SKILL.md`](../SKILL.md) from an intent alone.
- This directory is a template surface only until a non-trivial change is
  authorized.
