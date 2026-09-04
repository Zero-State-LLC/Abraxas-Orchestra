# Contributing

Private skill package. External PRs are not solicited by default.

Coding agents: follow [`AGENTS.md`](AGENTS.md). Other adapters (`CLAUDE.md`)
point there and add no extra authority. Non-trivial product changes start from
[`intent/README.md`](intent/README.md).

## Versioning

See [`docs/SEMVER.md`](docs/SEMVER.md). Single source of truth: `VERSION`.

```bash
python3 scripts/bump_version.py show
python3 scripts/bump_version.py patch|minor|major   # updates parity files
python3 scripts/bump_version.py check
```

Additive frameworks → **PATCH**. New CLI capability → **MINOR**. Breaking CLI/schema/install or unsafe apply defaults → **MAJOR**.

## Local checks before any change

```bash
bash scripts/smoke.sh
```

Must exit 0.

## Adding a framework

Update **together** (single commit preferred):

1. `references/<key>.md` — dual-naming table + architectural intent  
2. `schemas/frameworks.v1.json` — canonical loci + core_collapse  
3. `scripts/orchestra.py` — only if loader/CLI behavior changes  
4. `schemas/correspondence-table.v1.schema.json` — framework enum  
5. `orchestra.manifest.yaml` — frameworks list  
6. `install.sh` — required refs list  
7. `SKILL.md` — supported frameworks section  
8. `CHANGELOG.md`

Then: `python3 scripts/orchestra.py check` and `bash scripts/smoke.sh`.

The CLI loads `schemas/frameworks.v1.json` at startup. Do not re-embed framework tables in Python.

## Agent posture

When filling skeletons, follow `references/agent-posture.md`.

## Binary assets

GitHub connector text pushes cannot carry JPEG/WebP. Commit `assets/hero.jpg` from a local git client. Specs: `assets/README.md`.

## License

Apache-2.0 (`LICENSE` + `NOTICE`). Preserve copyright and license headers.


## Licensing and contributions

This repository uses the Zero State Proprietary License v1.0 (ZSPL-1.0) for original Zero State materials. See [`LICENSE`](LICENSE) and [`LICENSE_POLICY.md`](LICENSE_POLICY.md).

Contributions are limited to authorized Zero State contributors and agents unless a separate written agreement is approved. Zero State may require a contributor license agreement, intellectual-property assignment, work-for-hire agreement, or other written agreement before accepting an external contribution. Do not add third-party code or assets without documenting their license and preserving required notices.
