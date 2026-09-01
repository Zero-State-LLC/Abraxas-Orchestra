#!/usr/bin/env bash
# Abraxas Orchestra — atomic installer (v0.8.1)
# Default: ~/.hermes/skills/orchestra
# Supports --dry-run, --rollback, --target DIR, --allow-outside-home

set -euo pipefail

VERSION="0.8.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_TARGET="${HOME}/.hermes/skills/orchestra"
BACKUP_ROOT="${HOME}/.hermes/receipts/orchestra-backups"

DRY_RUN=0
ROLLBACK=0
ALLOW_OUTSIDE_HOME=0
TARGET="$DEFAULT_TARGET"

usage() {
  cat <<EOF
Abraxas Orchestra installer v${VERSION}

Usage: ./install.sh [options]

Options:
  --dry-run               Show actions without writing
  --target DIR            Install to DIR (default: ${DEFAULT_TARGET})
  --rollback              Restore most recent backup for this target family
  --allow-outside-home    Permit --target outside \$HOME (dangerous; explicit)
  -h, --help              Show this help

Security:
  Target must resolve under \$HOME unless --allow-outside-home is set.
  Refuses system roots (/, /etc, /usr, /bin, /System, …).
  Always prefer --dry-run before first install.

EOF
}

log()  { printf '==> %s\n' "$*"; }
warn() { printf '!!  %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)              DRY_RUN=1; shift ;;
    --target)
      [[ $# -ge 2 ]] || die "--target requires a directory argument"
      TARGET="$2"; shift 2
      ;;
    --rollback)             ROLLBACK=1; shift ;;
    --allow-outside-home)   ALLOW_OUTSIDE_HOME=1; shift ;;
    -h|--help)              usage; exit 0 ;;
    *)                      die "unknown option: $1" ;;
  esac
done

resolve_path() {
  local p="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath -m "$p" 2>/dev/null && return 0
  fi
  p="${p/#\~/$HOME}"
  if [[ "$p" != /* ]]; then
    p="$(pwd)/$p"
  fi
  python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$p"
}

is_forbidden_prefix() {
  local t="$1"
  local bad=( "/" "/etc" "/usr" "/bin" "/sbin" "/boot" "/dev" "/proc" "/sys" "/lib" "/lib64" "/var/run" "/var/lib" "/System" "/Windows" "/root" )
  local b
  for b in "${bad[@]}"; do
    if [[ "$t" == "$b" || "$t" == "$b"/* ]]; then
      return 0
    fi
  done
  return 1
}

validate_target() {
  local resolved home_resolved
  resolved="$(resolve_path "$TARGET")"
  TARGET="$resolved"

  if [[ "$TARGET" == "$SCRIPT_DIR" || "$TARGET" == "$SCRIPT_DIR"/* ]]; then
    warn "target is inside source tree: ${TARGET}"
  fi

  if [[ "$TARGET" == "/" ]]; then
    die "refusing to install to filesystem root"
  fi

  if [[ "$TARGET" == "$HOME" ]]; then
    die "refusing to install to \$HOME itself (choose a skills subdirectory)"
  fi

  home_resolved="$(resolve_path "$HOME")"
  if [[ "$TARGET" == "$home_resolved" || "$TARGET" == "$home_resolved"/* ]]; then
    :
  else
    if is_forbidden_prefix "$TARGET"; then
      die "refusing system path target: ${TARGET}"
    fi
    if [[ $ALLOW_OUTSIDE_HOME -ne 1 ]]; then
      die "target is outside \$HOME (${TARGET}). Re-run with --allow-outside-home if intentional."
    fi
    warn "installing outside \$HOME: ${TARGET}"
  fi

  [[ -n "$TARGET" ]] || die "empty target"
}

run_cmd() {
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[dry-run]'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

validate_source() {
  log "Validating source at ${SCRIPT_DIR}"
  local required=(
    "SKILL.md"
    "orchestra.manifest.yaml"
    "VERSION"
    "scripts/orchestra.py"
    "schemas/correspondence-table.v1.schema.json"
    "schemas/frameworks.v1.json"
  )
  local f
  for f in "${required[@]}"; do
    [[ -f "${SCRIPT_DIR}/${f}" ]] || die "missing required file: ${f}"
  done

  local refs=(
    "references/tree-of-life-mappings.md"
    "references/alchemical-stages.md"
    "references/elder-futhark.md"
    "references/planetary-spheres.md"
    "references/iching-hexagrams.md"
    "references/solomonic.md"
    "references/peircean-signs.md"
    "references/numogram.md"
    "references/sacred-geometry.md"
    "references/enochian.md"
    "references/enochian-cli-loci.md"
    "references/chaos-magic.md"
  )
  for f in "${refs[@]}"; do
    [[ -f "${SCRIPT_DIR}/${f}" ]] || die "missing framework reference: ${f}"
  done

  if ! python3 "${SCRIPT_DIR}/scripts/orchestra.py" check >/dev/null 2>&1; then
    python3 -c "import ast, pathlib; ast.parse(pathlib.Path('${SCRIPT_DIR}/scripts/orchestra.py').read_text())" \
      || die "scripts/orchestra.py failed syntax check"
  fi
  log "Source validation OK"
}

do_rollback() {
  validate_target
  local latest
  latest="$(ls -1dt "${BACKUP_ROOT}"/*/ 2>/dev/null | head -1 || true)"
  [[ -n "$latest" ]] || die "no backups found under ${BACKUP_ROOT}"
  log "Rolling back from ${latest}"
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[dry-run] rm -rf %q && mkdir -p %q && cp -a %q %q\n' \
      "$TARGET" "$(dirname "$TARGET")" "$latest" "$TARGET"
  else
    rm -rf "$TARGET"
    mkdir -p "$(dirname "$TARGET")"
    cp -a "$latest" "$TARGET"
  fi
  log "Rollback complete"
}

backup_existing() {
  if [[ ! -d "$TARGET" ]]; then
    return 0
  fi
  local stamp dest
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  dest="${BACKUP_ROOT}/${stamp}"
  log "Backing up existing install to ${dest}"
  run_cmd mkdir -p "${BACKUP_ROOT}"
  run_cmd cp -a "${TARGET}" "${dest}"
}

atomic_install() {
  local staging
  staging="$(mktemp -d "${TMPDIR:-/tmp}/orchestra-install.XXXXXX")"
  trap 'rm -rf "$staging"' EXIT

  log "Staging into ${staging}"

  run_cmd cp -a "${SCRIPT_DIR}/SKILL.md" "${staging}/"
  run_cmd cp -a "${SCRIPT_DIR}/orchestra.manifest.yaml" "${staging}/"
  run_cmd cp -a "${SCRIPT_DIR}/VERSION" "${staging}/"
  run_cmd cp -a "${SCRIPT_DIR}/README.md" "${staging}/" 2>/dev/null || true
  run_cmd cp -a "${SCRIPT_DIR}/CHANGELOG.md" "${staging}/" 2>/dev/null || true
  run_cmd cp -a "${SCRIPT_DIR}/LICENSE" "${staging}/" 2>/dev/null || true
  run_cmd cp -a "${SCRIPT_DIR}/NOTICE" "${staging}/" 2>/dev/null || true
  run_cmd cp -a "${SCRIPT_DIR}/scripts" "${staging}/"
  run_cmd cp -a "${SCRIPT_DIR}/references" "${staging}/"
  run_cmd cp -a "${SCRIPT_DIR}/schemas" "${staging}/"
  run_cmd cp -a "${SCRIPT_DIR}/docs" "${staging}/" 2>/dev/null || true
  run_cmd cp -a "${SCRIPT_DIR}/examples" "${staging}/" 2>/dev/null || true
  run_cmd cp -a "${SCRIPT_DIR}/assets" "${staging}/" 2>/dev/null || true
  run_cmd cp -a "${SCRIPT_DIR}/tests" "${staging}/" 2>/dev/null || true
  run_cmd cp -a "${SCRIPT_DIR}/install.sh" "${staging}/" 2>/dev/null || true

  run_cmd chmod +x "${staging}/scripts/orchestra.py"
  run_cmd chmod +x "${staging}/scripts/smoke.sh" 2>/dev/null || true
  run_cmd chmod +x "${staging}/install.sh" 2>/dev/null || true

  log "Activating at ${TARGET}"
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '[dry-run] mkdir -p %q && rm -rf %q && mv %q %q\n' \
      "$(dirname "$TARGET")" "$TARGET" "$staging" "$TARGET"
    rm -rf "$staging"
    trap - EXIT
  else
    mkdir -p "$(dirname "$TARGET")"
    rm -rf "$TARGET"
    mv "$staging" "$TARGET"
    trap - EXIT
  fi
}

if [[ $ROLLBACK -eq 1 ]]; then
  do_rollback
  exit 0
fi

validate_target
validate_source
backup_existing
atomic_install

log "Installed Abraxas Orchestra ${VERSION} → ${TARGET}"
log "Try: python3 ${TARGET}/scripts/orchestra.py check"
log "     python3 ${TARGET}/scripts/orchestra.py list"
log "     python3 ${TARGET}/scripts/orchestra.py analyze --path . --out /tmp/orch-an"
log "     bash ${TARGET}/scripts/smoke.sh"
