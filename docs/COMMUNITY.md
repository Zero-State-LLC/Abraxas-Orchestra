# Community skills compliance

Checklist for listing **orchestra** in agent skill hubs (OpenClaw, Hermes Skills Hub, agentskills.io-style registries, Claude/Codex skill directories).

## Spec alignment (Agent Skills open format)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Folder contains `SKILL.md` | Pass | Root entry |
| YAML frontmatter `name` | Pass | `orchestra` (lowercase, hyphens) |
| YAML frontmatter `description` | Pass | One sentence, ≤60 chars (Hermes v0.21 hardline) |
| `name` matches install directory | Pass | `…/skills/orchestra` |
| Optional `scripts/`, `references/` | Pass | Progressive disclosure |
| Description ≤ 60 chars | Pass | Hermes v0.21 index; validator ceiling remains 1024 |
| SKILL body not a full manual | Pass | Deep tables stay in `references/` |

## OpenClaw / Hermes packaging

| Requirement | Status | Notes |
|-------------|--------|-------|
| Install path documented | Pass | `~/.hermes/skills/orchestra`, `~/.openclaw/skills/orchestra` |
| Atomic install + dry-run | Pass | `install.sh` |
| Path jail | Pass | Outside-`$HOME` requires `--allow-outside-home` |
| `metadata` for runtime gates | Partial | Prefer declaring `requires.bins: [python3]` in frontmatter |
| No undeclared network/env secrets | Pass | CLI is local stdlib |
| Mutable state outside package | Pass | Documented invariant |

## Security review expectations

Registries often reject or quarantine skills that:

- Download and execute remote code at install time
- Require undeclared API keys
- Write outside the skill/project tree without disclosure
- Obfuscate scripts

**Orchestra posture:** local copy install, no network in CLI structure path, disclosed path jail, Apache-2.0, audit at `docs/SECURITY_AUDIT.md`.

## License

Current `LICENSE` is **Apache-2.0**. Eligible for most community registries that require OSI-approved licenses.

| Option | Implication |
|--------|-------------|
| Apache-2.0 (current) | Eligible for public skill hubs |

## Suggested submission packet

1. Repo URL + tag `v0.1.3` (or later)
2. One-paragraph description (from `SKILL.md` frontmatter)
3. Install commands from `docs/DEPLOY.md`
4. Security one-liner from `docs/PUBLIC_RELEASE.md`
5. License: Apache-2.0

## Pre-submit checklist

- [x] LICENSE is Apache-2.0 (OSI-approved)
- [ ] `bash scripts/smoke.sh` green on clean clone
- [ ] Path-refusal check: `--target /etc/orchestra` fails
- [ ] SKILL frontmatter validates on target host
- [ ] README states is / is-not clearly
- [ ] Contact path for security reports (`.github/SECURITY.md`)
