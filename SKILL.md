---
name: orchestra
description: Map software onto fail-closed symbolic correspondence maps.
version: 0.8.1
author: "Daniel Meyer (@scrimshawlife-ctrl) / Zero State LLC <scrimshawlife@gmail.com>"
license: Apache-2.0
platforms: [linux, macos]
metadata:
  author: "Daniel Meyer (@scrimshawlife-ctrl) / Zero State LLC <scrimshawlife@gmail.com>"
  openclaw:
    requires:
      bins: [python3]
    os: [darwin, linux]
    emoji: "🎼"
  hermes:
    command_router: true
    groups: [meta, emit, repo]
    tags: [architecture, correspondence, mapping, fail-closed]
    related_skills: []
---

# Abraxas Orchestra

Orchestra maps software onto fail-closed symbolic correspondence maps from `schemas/frameworks.v1.json`. It emits dual-named skeletons and diagrams, and it observes existing trees before any gated rename.

It does not invent loci, apply writes without `--confirm`, or use network I/O on emit or repo paths. Hosts: Hermes and OpenClaw.

## When to Use

Load this skill when the user wants to:

- Scaffold a dual-named layout from a framework listed in `schemas/frameworks.v1.json`
- Emit `architecture.html`, `architecture.json`, and `architecture.mmd` from loci or an observed graph
- Analyze a local tree, map modules fail-closed, and plan or apply mechanical moves
- Collect a guided wizard plan instead of freestyle flags

Do not use this skill to invent symbolic names, write freehand Mermaid for Orchestra-mapped code, or treat FORCED or WEAK maps as success.

## Prerequisites

- Python 3.11 or newer, with `python3` on `PATH`
- Local install: `bash install.sh` writes `${HERMES_HOME:-$HOME/.hermes}/skills/orchestra`. OpenClaw: `bash install.sh --target ~/.openclaw/skills/orchestra`
- Canonical loci only from `schemas/frameworks.v1.json`. Fit notes: `docs/FRAMEWORK_FIT.md`. Agent posture: `references/agent-posture.md`
- No API keys. The CLI is local stdlib Python. Install and smoke scripts are bash, so this skill declares `platforms: [linux, macos]` (OpenClaw `os` stays `darwin` / `linux`)

## How to Run

Call the CLI through the Hermes `terminal` tool. Read `skill_dir` returned by `skill_view(name="orchestra")`. Explicitly set
`HERMES_SKILL_DIR` to that exact reviewed path in each shell invocation (or
substitute the absolute path); Hermes does not promise an exported variable.

```text
terminal(command='python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" <command> ...')
```

Pick one primary CommandRouter group before you choose a command:

- **meta** — `check`, `list`, `wizard` (integrity, discovery, guided path)
- **emit** — `structure`, `project`, `diagram` (greenfield skeleton or graph)
- **repo** — `analyze`, `optimize` (observe, map, plan, gated apply)

When the path or flags are unclear, or you are collecting fields in Desktop chat, use **meta** `wizard`. Do not invent argv.

## Quick Reference

```text
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" check
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" list
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" wizard [--answers FILE] [--preset NAME] [--print-only|--run] [--json]
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" structure -f <framework> [-c concerns] [-o overlay] [--out DIR]
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" project   -f <framework> [-c concerns] [-o overlay] [--out DIR]
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" diagram   -f <framework> [-c concerns] [-o overlay] [--out DIR] [--project]
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" analyze  --path DIR [-f FRAMEWORK] [-o OVERLAY] [--lang python|auto|…] [--out DIR]
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" optimize --from analysis.json [--out DIR] [--min-strength ADEQUATE]
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" optimize --from analysis.json --apply
python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" optimize --from analysis.json --apply --confirm [--backup-dir DIR] [--refresh] [--steps IDS] [--actions NAMES]
```

Shared emit flags: `-f` framework (required), `-c` concerns, `-o` overlay, `--out` directory.

Eleven maps: tree-of-life, alchemical-stages, elder-futhark, planetary-spheres, iching-hexagrams, solomonic, peircean-signs, numogram, sacred-geometry, enochian, chaos-magic.

## Procedure

Hermes routing is required. Prefer one group per turn unless the user clearly needs a sequence (for example emit, then repo). Inside a group, pick the smallest command that satisfies the ask. Never invent symbolic loci outside `schemas/frameworks.v1.json`. Prefer CLI emission over freehand architecture diagrams.

1. **Route.** Need verify or list maps → **meta** `check` or `list`. Unsure or collecting fields → **meta** `wizard`. New dual-named layout or diagram → **emit** (`structure`, `project`, or `diagram`). Existing tree → **repo** (`analyze`, then `optimize`). Done when one group and one command are chosen.

2. **Wizard when unsure.** Collect missing fields in chat, one at a time. Do not use interactive stdin. Write `orchestra-wizard-answers.v1` JSON to a temp file. Run `wizard --answers FILE --print-only` (or `--json`). After approval, `wizard --answers FILE --run` or run the printed argv. Never set `confirm_apply: true` unless the user explicitly approved gated renames. Done when the printed plan matches the ask.

3. **Identify concerns or observe.** For greenfield, name functional concerns. For an existing tree, run **repo** `analyze --path DIR`. Optional `-f FRAMEWORK` maps fail-closed (`STRONG` / `ADEQUATE` / `WEAK` / `FORCED`). Exit `1` if WEAK or FORCED; `2` on `NOT_COMPUTABLE`. `--lang python` (default) is full AST; `javascript`, `typescript`, `go`, `rust`, `ruby`, and `auto` cover import-surface graphs. Analyze always embeds `metrics`; stderr prints `# metrics:`. `--out` writes `analysis.json`, `structure-metrics.json`, and the diagram trio. Done when you have concerns or an `analysis.json`.

4. **Choose a framework.** Use **meta** `list` if unsure. Optional overlay with `-o`. Done when the framework key exists in `schemas/frameworks.v1.json`.

5. **Emit or plan.** Prefer **emit** `structure` or `project` with `--out DIR` so diagrams write automatically (`architecture.html`, `architecture.json`, `architecture.mmd`). `project` collapses oversized or forced maps with an explicit projection. Use **emit** `diagram` for graph-only. Stage stubs from `structure` carry ALLOWED / FORBIDDEN locus contracts (`run()` + `contract()`); multi-stage `--out` also writes `pipeline.py`. For an existing tree, **repo** `optimize --from analysis.json` is plan-only by default. `--apply` is a dry-run of `safe_apply` (rename / promote / flatten). `--apply --confirm` writes after backup. FORCED blocks apply. `--steps` / `--actions` select moves; `--refresh` re-analyzes after confirmed apply. Done when artifacts exist under `--out` or the plan is printed.

6. **Implement inside locus contracts.** After `structure` / `project`, implement domain logic in each stage. Do not stop at empty scaffolds. See `examples/python-tree-of-life-pipeline/`. Done when each stage only does its locus work and call direction follows the map.

7. **Stop on fail-closed outcomes.** `NOT_COMPUTABLE` or `FORCED` means stop. Do not invent loci. Do not silently “improve” FORCED or WEAK maps. Done when the label is reported and no invented names were added.

## Pitfalls

- Inventing a locus that is not in `schemas/frameworks.v1.json` breaks the fail-closed contract.
- Setting `confirm_apply: true` without explicit operator approval can write renames. Leave it unset or false.
- Freehand Mermaid for Orchestra-mapped code drifts from the map. Run emission and use `architecture.mmd`.
- Desktop chat cannot use interactive stdin. Collect wizard fields in chat and pass `--answers`.
- `--apply` without `--confirm` does not write. That is the dry-run. Do not treat it as a failed apply.
- WEAK or FORCED analyze exits `1`. That is a mapping failure, not a CLI crash.
- Analyze language limits: Python is AST; javascript, typescript, go, rust, and ruby are import-surface parsers.
- Windows is not a declared platform. Install and smoke are bash; the Python CLI is stdlib but untested on Windows.

## Verification

Prove the skill loaded and the chosen command worked:

1. `terminal(command='python3 "${HERMES_SKILL_DIR}/scripts/orchestra.py" check')` prints `CHECK OK`.
2. `terminal(command='python3 "${HERMES_SKILL_DIR}/scripts/integrity_check.py"')` prints `INTEGRITY OK`.
3. After **emit** `structure`, stdout includes `"status": "CLEAN"` and `--out` contains the diagram trio when `--out` was set.
4. After **repo** `analyze --out`, `analysis.json` exists and stderr includes `# metrics:`.
5. After **repo** `optimize` without `--confirm`, the tree is unchanged and a plan is printed or written.

Operator install (not the agent loop):

```text
terminal(command='bash install.sh --dry-run') # workdir = reviewed source checkout
```

Then `bash install.sh` to `${HERMES_HOME:-$HOME/.hermes}/skills/orchestra`.

After an approved `optimize --apply --confirm`, inspect the changed paths and
run the target project's import/build checks and existing tests from its root,
plus a fresh analyze on the renamed tree. Record exit statuses and compare
behavior before/after; a plan, tree listing, or refreshed diagram is not proof
imports still work. Use `python3 -m unittest discover -s tests` for Orchestra's
own fixture tests, not as a substitute for the target project's test suite.

Installer upgrades stage and check on the target filesystem, retain unique
backups keyed to the exact resolved target, then rename and check the final path.
`bash install.sh --target DIR --rollback` restores only that target's verified
backup. Concurrent installers fail on a per-target advisory lock. There is a
brief absent-target window between renames: this is not crash-atomic or an
uninterrupted replacement. On process death, preserve `.orchestra-previous-*`
and backups for operator recovery; never blindly delete them. Run only in
trusted user-owned directories (advisory locks do not stop hostile filesystem
writers). Do not run this installer from inside the destination package.

Skill source selection, migration and safe checks: [SKILL_PROVENANCE.md](SKILL_PROVENANCE.md).
