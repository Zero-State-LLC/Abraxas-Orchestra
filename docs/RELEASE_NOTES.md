# Release notes

Narrative notes for operators and agents. Machine changelog: [`CHANGELOG.md`](../CHANGELOG.md).

## 0.8.1 — 2026-09-01

Hermes Agent v0.21.0 (Pantheon, tag v2026.8.31) skill-index contract.

- Description is one sentence, 59 characters: map software onto fail-closed symbolic correspondence maps.
- Required frontmatter: `author`, `platforms: [linux, macos]`, `metadata.hermes.tags`, `metadata.hermes.related_skills: []`
- Routing groups are unchanged: **meta** / **emit** / **repo**. Wizard when unsure. No invented loci. Gated apply stays gated.
- Integrity check now fails a description over 60 characters

## 0.7.0 — 2026-08-07

Structure as optimization — contracts, metrics, and a measurable proof path.

- **Emit:** stage stubs carry locus ALLOWED/FORBIDDEN contracts (`run` + `contract`); multi-stage `--out` writes `pipeline.py`
- **Repo analyze:** always embeds structure metrics (map quality, cycles, mix); `structure-metrics.json` on `--out`
- **Proof:** `examples/benchmark-tree-of-life/` + harness (parity, map, cycles, mix, early-exit)
- **Hermes:** route via **meta** / **emit** / **repo** (same as CLI CommandRouter)
- Site documents Python best-case optimized by the map, not rename-only

## 0.6.0 — 2026-08-07

AST-grade multi-language import parsers + higher, subprocess-aware coverage floors.

## 0.4.0 — 2026-08-05

Broader gated `safe_apply` beyond mechanical rename.

- **Promote:** `suggest_boundary` may move `module.py` → `module/__init__.py` when the stem matches the mechanical name
- **Flatten:** `suggest_flatten` collapses single-file packages (`leaf/__init__.py` → `leaf.py`) when there are no siblings
- **Selective apply:** `--steps step-1,step-3` and `--actions suggest_rename,suggest_boundary,suggest_flatten`
- Schema: `schemas/optimize-apply.v1.schema.json`
- `suggest_extract` remains advisory (no content invention)

## 0.3.2 — 2026-08-04

Semantic versioning as an operable contract.

- Policy: [`SEMVER.md`](SEMVER.md)
- Tool: `python3 scripts/bump_version.py {show,check,patch,minor,major,set}`
- CI parity job fails on drift or non-core semver in `VERSION`
- Release flow: bump → CHANGELOG → `release_preflight.sh` → tag `v` + VERSION

## 0.3.1 — 2026-08-04

Apply hardening + import-graph refresh.

- `--refresh` with `--apply --confirm` re-runs `analyze` and writes beside the backup
- Destination collisions demoted; vacate-first rename ordering
- Smoke covers `scripts/` analyze + optimize dry-run

## 0.3.0 — 2026-08-04

**Optimize apply (Phase C)** — gated mutation.

- `optimize --apply` = dry-run of `safe_apply` mechanical renames
- `optimize --apply --confirm` writes after backup (`--backup-dir`, default under analyzed root)
- FORCED mappings refuse apply; boundary/extract steps stay advisory
- Restore notes: `RESTORE.md` in the backup directory

## 0.2.0 — 2026-08-04

Repo **analyze → map → optimize (plan)**.

- `analyze --path DIR` observes a local Python import graph (stdlib `ast`), optional `-f` mapping onto `frameworks.v1.json`, diagram bundle on `--out`.
- `optimize --from analysis.json` emits `optimize-plan.json` + `OPTIMIZE.md` without modifying the analyzed tree.

Plan: [`ANALYZE_OPTIMIZE_PLAN.md`](ANALYZE_OPTIMIZE_PLAN.md).

## 0.1.6 — 2026-08-04

Automatic diagrammatic emission.

`structure` / `project --out DIR` always writes:

- `architecture.html`
- `architecture.json`
- `architecture.mmd` (Mermaid)

Agents: when Mermaid or a code diagram is needed for Orchestra-mapped work, emit via CLI — do not invent separate graphs.

## 0.1.5 — 2026-08-04

Diagrammatic emission via `diagram` / `diagrammit`.

## 0.1.4 — 2026-08-04

Simplified command structure.

## 0.1.3 — 2026-08-04

Public debut packaging + security hardening.

## 0.1.0 — 2026-08-04

First design surface.
