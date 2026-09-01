# Changelog

All notable changes to Abraxas Orchestra will be recorded here.

The format follows Keep a Changelog principles. Versions follow Semantic Versioning.

Narrative release notes: [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

## [Unreleased]

## [0.8.1] — 2026-09-01

### Changed
- `SKILL.md` meets Hermes Agent v0.21.0 (tag v2026.8.31) hardline: one-sentence description ≤60 characters, `author`, `platforms`, `metadata.hermes.tags`, and `metadata.hermes.related_skills`
- Skill body uses the Hermes section order (When to Use through Verification). CLI examples use `${HERMES_SKILL_DIR}` and the Hermes `terminal` tool
- Integrity check asserts frontmatter starts at byte 0 and description length ≤60

### Unchanged
- CommandRouter groups remain **meta** / **emit** / **repo**. Prefer wizard when unsure. Loci stay fail-closed to `schemas/frameworks.v1.json`
- Frontmatter `license` stays Apache-2.0. Existing OpenClaw metadata, `command_router`, and `groups` are kept. No blueprint or cron. Never set `confirm_apply: true`

## [0.8.0] — 2026-08-08

### Added
- **`wizard` meta command** — guided plan/resolve from `--answers` and/or `--preset` (`scripts/orchestra_wizard.py`)
- Answers schema `schemas/wizard-answers.v1.schema.json` (`orchestra-wizard-answers.v1`); plan shape `orchestra-wizard-plan.v1`
- Print-only by default; `--json` emits plan JSON; `--run` dispatches resolved argv in-process via `CommandRouter`
- Interactive TTY collect path; non-TTY without `--answers`/`--preset` exits `2` with Desktop guidance
- Hermes Desktop protocol in `SKILL.md` / `references/agent-posture.md`: collect fields in chat → temp answers file → print-only → `--run` on approval
- Presets (e.g. `greenfield`) and strict unknown-key rejection on answers
- Unit + CLI tests (`tests/test_wizard.py`); smoke covers non-interactive wizard print-only

### Changed
- CommandRouter **meta** group: `check` | `list` | `wizard`
- Docs: README, DESIGN, agent-posture, manifest schemas/intents document wizard-first when unsure
- Never set `confirm_apply: true` unless the operator explicitly approved gated renames

## [0.7.0] — 2026-08-07

### Added
- Pure unit tests for `diagram_emit` / `diagram_mermaid` (`tests/test_diagrams.py`)
- Static landing page under `site/` deployed via GitHub Pages (`.github/workflows/pages.yml`)
- 3D brand hero (`assets/hero.jpg`) for README and GitHub Pages
- Hermes agent routing aligned with CLI CommandRouter groups (**meta** / **emit** / **repo**) in `SKILL.md`
- Site: Python best-case before/after (`tree-of-life`) — structure that *optimizes* code, not rename-only
- Example: `examples/python-tree-of-life-pipeline/` (stage contracts + runnable `pipeline.py`)
- **Contract-oriented structure emission:** each stage stub ships `run()` + `contract()` with locus **ALLOWED** / **FORBIDDEN**; multi-stage `--out` also writes a linear `pipeline.py` and documents contracts in `SKELETON.md`
- **Structure benchmark:** `examples/benchmark-tree-of-life/` — paired before/after trees + `harness.py` measuring parity, analyze map quality, import cycles, responsibility mix, and early-exit latency
- **`analyze` structure metrics:** every analysis embeds `metrics` (map quality, import cycles, responsibility mix); `--out` also writes `structure-metrics.json`; stderr prints `# metrics: …`
- `scripts/structure_metrics.py` — shared metrics engine used by analyze

### Changed
- CLI commands registered via `CommandRouter` (`scripts/orchestra_router.py`) — same surface, clearer groups
- Branch protection on `main`: require PR + `ci-ok`, **enforce for admins** (no bypass)
- README + `docs/CI.md` + `docs/FRAMEWORK_FIT.md` document protection and multi-lang limits
- Default hero image is the 3D render; flat `hero.svg` kept as legacy vector
- `references/agent-posture.md`, `docs/DEPLOY.md`, site page, and manifest document Hermes group routing
- Smoke includes optimized Tree-of-Life pipeline + structure benchmark
- Import-from resolution prefers known submodules (`from pkg import sub` → `pkg.sub`) so cycles surface in metrics

## [0.6.0] — 2026-08-07

### Added
- AST-grade multi-language import parsers (tokenizers + structured ImportNode trees for JS/TS, Go, Rust, Ruby)
- Subprocess-aware coverage: in-process CLI exercises under the same tracer as pure unit tests
- Higher hard floors on core modules (orchestra, analyze_*, optimize_*, diagrams, integrity, bump_version)

### Changed
- `analyze_langs.py` no longer relies on regex-only import extraction for non-Python languages

## [0.5.0] — 2026-08-07

### Added
- Multi-language analyze: `javascript`, `typescript`, `go`, `rust`, `ruby`, and `auto`
- `scripts/analyze_langs.py` — stdlib regex import extractors (Python remains AST)
- Hard coverage floors via `python3 scripts/coverage_report.py --gate`
- CI job `coverage-gate` required by `ci-ok` (floors on core in-process modules)
- `tests/test_analyze_langs.py`

### Changed
- `analyze --lang` help and docs; analysis includes `languages` + per-node `language`
- Soft `coverage-soft` remains informational; hard floors are the gate

## [0.4.3] — 2026-08-07

### Added
- `scripts/coverage_report.py` — soft quality report (imports, test linkage, in-process line coverage)
- CI job `coverage-soft` (artifact upload; **not** required by `ci-ok`)
- `tests/test_coverage_report.py`

### Changed
- `docs/CI.md` / `docs/ROADMAP.md` document soft vs hard coverage policy

## [0.4.2] — 2026-08-07

### Added
- Deeper analyze mapping: role synonyms, compound/suffix stripping, docstring/`def` signals, secondary `match_score`
- Token-aware `candidate_frameworks` ranking when analyze runs without `-f`
- `tests/test_mapping.py` for mapping heuristics

### Changed
- `docs/FRAMEWORK_FIT.md` documents the scoring signals

## [0.4.1] — 2026-08-07

### Added
- `scripts/integrity_check.py` — critical-file line floors + markers (anti-truncation)
- CI job `integrity` required by `ci-ok`
- `docs/FRAMEWORK_FIT.md` — which map to use and strength labels
- Optimize apply split: `optimize_enrich.py` + `optimize_rewrite.py` (public API still `optimize_apply`)

### Changed
- Mapping: normalize hyphen/underscore identifiers for STRONG/ADEQUATE locus match
- Smoke runs integrity check before unit tests

## [0.4.0] — 2026-08-05

### Added
- `suggest_boundary` safe apply: promote `module.py` → `module/__init__.py` when stem matches mechanical name
- `suggest_flatten` plan + safe apply: collapse single-file packages `leaf/__init__.py` → `leaf.py`
- `optimize --steps` — apply only listed step ids (still must be `safe_apply`)
- `optimize --actions` — filter by action name (`suggest_rename`, `suggest_boundary`, `suggest_flatten`)
- Schema `schemas/optimize-apply.v1.schema.json`

### Changed
- Apply path runs renames → promotes → flattens; collision demotion covers all three move kinds
- Docs / COMPLETION / ROADMAP aligned to broader `safe_apply` surface

## [0.3.2] — 2026-08-04

### Added
- Semantic versioning policy (`docs/SEMVER.md`)
- `scripts/bump_version.py` — show / check / patch / minor / major / set
- CI `version-parity` runs `bump_version.py check`
- `tests/test_semver.py`

### Changed
- `release_preflight.sh` uses semver parity check
- CONTRIBUTING documents bump classes (framework=PATCH, capability=MINOR, break=MAJOR)

## [0.3.1] — 2026-08-04

### Fixed
- Packaging drift: `install.sh` VERSION aligned to 0.3.1; README quick-start flat CLI; COMPLETION checklist refreshed

### Added
- `optimize --apply --confirm --refresh` re-analyzes the tree and writes refreshed `analysis.json` beside the backup
- Vacate-first ordering when a rename destination is another rename’s source
- Destination-collision demotion in plan enrichment
- Analyze skips `.orchestra-backups/`; smoke analyzes `scripts/` + optimize dry-run

## [0.3.0] — 2026-08-04

### Added
- `optimize --apply` dry-run; `--apply --confirm` performs gated mechanical renames with backup
- Import lines rewritten with `as <old>` aliases so call sites stay valid
- `RESTORE.md` + `apply-report.json` written under `--backup-dir`
- Fixture `tests/fixtures/rename_pkg/` for apply tests

### Security
- Apply path jail under analyzed root; refuse FORCED analysis; system backup-dir denied

## [0.2.0] — 2026-08-04

### Added
- `analyze` — read-only Python repo import graph + optional fail-closed framework map
- `optimize` — plan-only refactor suggestions from `analysis.json` (no tree writes)
- Schemas: `analysis.v1`, `optimize-plan.v1`
- Fixture `tests/fixtures/mini_pkg/`

## [0.1.6] — 2026-08-04

### Added
- Automatic diagram emission on `structure`/`project --out`: HTML + JSON + Mermaid (`.mmd`)
- Skill contract: agents must use Orchestra diagram output instead of ad-hoc Mermaid when mapping structure

## [0.1.5] — 2026-08-04

### Added
- `diagram` / `diagrammit` — interactive HTML + agent JSON (`nodes`, `edges`, `flows`)

## [0.1.4] — 2026-08-04

### Changed
- CLI simplified: top-level `check` | `list` | `structure` | `project`

## [0.1.3] — 2026-08-04

### Security
- Path jail; Apache-2.0; audit docs

## [0.1.0] — 2026-08-04

First design surface.
