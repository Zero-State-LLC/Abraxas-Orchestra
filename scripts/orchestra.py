#!/usr/bin/env python3
"""
Abraxas Orchestra — CLI entrypoint

Minimal, fail-closed, dual-naming skeleton emitter + repo analyze/optimize plan.
Stdlib only. No external dependencies.

Commands are registered on a CommandRouter (see orchestra_router.py):
  meta:  check | list | wizard
  emit:  structure | project | diagram
  repo:  analyze | optimize
Legacy: do <command> still accepted.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from orchestra_router import CommandRouter, CommandSpec
from orchestra_wizard import (
    WizardError,
    format_plan_human,
    format_plan_json,
    interactive_collect,
    load_answers,
    merge_preset,
    resolve_plan,
    validate_answers,
)

VERSION = "0.8.1"
SKILL_ROOT = Path(__file__).resolve().parent.parent

def _load_frameworks() -> dict[str, dict[str, Any]]:
    path = SKILL_ROOT / "schemas" / "frameworks.v1.json"
    if not path.exists():
        raise SystemExit(f"MISSING frameworks schema: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    frameworks: dict[str, dict[str, Any]] = {}
    for key, meta in raw.get("frameworks", {}).items():
        loci = []
        for row in meta.get("default_loci", []):
            loci.append((row["mechanical"], row["symbolic"], row.get("note") or ""))
        frameworks[key] = {
            "title": meta["title"],
            "reference": meta["reference"],
            "default_loci": loci,
            "core_collapse": list(meta.get("core_collapse") or []),
        }
    return frameworks


FRAMEWORKS: dict[str, dict[str, Any]] = _load_frameworks()


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_list_frameworks(_: argparse.Namespace) -> int:
    print(f"Abraxas Orchestra {VERSION} — available frameworks\n")
    for key, meta in FRAMEWORKS.items():
        ref = meta["reference"]
        exists = (SKILL_ROOT / ref).exists()
        status = "OK" if exists else "MISSING_REF"
        print(f"  {key:22}  {meta['title']:28}  [{status}]")
    print()
    return 0


def _validate_table_against_schema(table: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed_fw = {
        "tree-of-life", "alchemical-stages", "elder-futhark", "planetary-spheres",
        "iching-hexagrams", "solomonic", "peircean-signs", "numogram",
        "sacred-geometry", "enochian", "chaos-magic", "composite",
    }
    allowed_status = {"CLEAN", "WEAK_MAPPINGS", "FORCED_CORRESPONDENCE", "NOT_COMPUTABLE"}
    allowed_strength = {"STRONG", "ADEQUATE", "WEAK", "FORCED"}
    allowed_map_keys = {
        "functional_concern", "mechanical_name", "symbolic_name", "symbolic_locus",
        "strength", "notes", "overlay_note",
    }
    allowed_top = {
        "framework", "secondary_overlay", "status", "mappings",
        "pragmatic_projection", "provenance",
    }
    for k in table:
        if k not in allowed_top:
            errors.append(f"unknown top-level key: {k}")
    if "framework" not in table:
        errors.append("missing required: framework")
    elif table["framework"] not in allowed_fw:
        errors.append(f"framework not in schema enum: {table['framework']}")
    if "status" not in table:
        errors.append("missing required: status")
    elif table["status"] not in allowed_status:
        errors.append(f"status not in schema enum: {table['status']}")
    if "mappings" not in table:
        errors.append("missing required: mappings")
    elif not isinstance(table["mappings"], list):
        errors.append("mappings must be an array")
    else:
        for i, m in enumerate(table["mappings"]):
            if not isinstance(m, dict):
                errors.append(f"mappings[{i}] not an object")
                continue
            for k in m:
                if k not in allowed_map_keys:
                    errors.append(f"mappings[{i}] unknown key: {k}")
            for req in ("functional_concern", "symbolic_locus", "strength"):
                if req not in m:
                    errors.append(f"mappings[{i}] missing required: {req}")
            if "strength" in m and m["strength"] not in allowed_strength:
                errors.append(f"mappings[{i}] bad strength: {m['strength']}")
    return errors


def cmd_check(_: argparse.Namespace) -> int:
    errors: list[str] = []
    required = [
        "SKILL.md", "orchestra.manifest.yaml", "VERSION",
        "schemas/correspondence-table.v1.schema.json",
        "schemas/frameworks.v1.json",
        "schemas/analysis.v1.schema.json",
        "schemas/optimize-plan.v1.schema.json",
        "schemas/optimize-apply.v1.schema.json",
        "schemas/wizard-answers.v1.schema.json",
    ]
    for rel in required:
        if not (SKILL_ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")
    for key, meta in FRAMEWORKS.items():
        ref = SKILL_ROOT / meta["reference"]
        if not ref.exists():
            errors.append(f"missing reference for {key}: {meta['reference']}")
    for key in FRAMEWORKS:
        loci = _select_loci(key, None)[:3]
        table = _build_table(key, None, loci, [], None)
        for e in _validate_table_against_schema(table):
            errors.append(f"{key}: {e}")
    if "tree-of-life" in FRAMEWORKS and "chaos-magic" in FRAMEWORKS:
        loci = _select_loci("tree-of-life", ["intent", "output"])
        ov_notes = _overlay_annotation(loci, "chaos-magic")
        table = _build_table("tree-of-life", "chaos-magic", loci, ov_notes, None)
        for e in _validate_table_against_schema(table):
            errors.append(f"overlay-sample: {e}")
    if errors:
        print("CHECK FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"CHECK OK — Orchestra {VERSION}")
    print(f"  skill root : {SKILL_ROOT}")
    print(f"  frameworks : {len(FRAMEWORKS)}")
    print(f"  schema     : correspondence-table.v1 validated for all frameworks")
    return 0


def _select_loci(framework: str, concerns: list[str] | None) -> list[tuple[str, str, str]]:
    meta = FRAMEWORKS[framework]
    defaults = meta["default_loci"]
    if not concerns:
        return list(defaults)
    selected: list[tuple[str, str, str]] = []
    for concern in concerns:
        c = concern.strip().lower()
        matched = False
        for mech, sym, note in defaults:
            if c in mech.lower() or c in sym.lower() or c in note.lower():
                selected.append((mech, sym, note))
                matched = True
        if not matched:
            selected.append((concern, f"unmapped_{concern}", "FORCED — no clean locus"))
    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for item in selected:
        if item[0] not in seen:
            seen.add(item[0])
            out.append(item)
    return out


def _apply_pragmatic_projection(
    framework: str, loci: list[tuple[str, str, str]]
) -> tuple[list[tuple[str, str, str]], str | None]:
    forced = [x for x in loci if x[2].startswith("FORCED")]
    clean = [x for x in loci if not x[2].startswith("FORCED")]
    meta = FRAMEWORKS[framework]
    core_names = set(meta.get("core_collapse") or [])
    projection_note: str | None = None
    if forced:
        loci = clean
        projection_note = f"Dropped {len(forced)} FORCED locus/loci; retained clean mappings only."
    if len(loci) > 6 and core_names:
        collapsed = [x for x in loci if x[0] in core_names]
        if not collapsed:
            collapsed = [loci[0], loci[len(loci) // 2], loci[-1]]
        dropped = len(loci) - len(collapsed)
        loci = collapsed
        extra = f" Collapsed {dropped} non-core loci to framework core set."
        projection_note = (projection_note or "") + extra
    return loci, projection_note


def _overlay_annotation(primary_loci: list[tuple[str, str, str]], overlay: str) -> list[str]:
    if overlay not in FRAMEWORKS:
        return []
    o_loci = FRAMEWORKS[overlay]["default_loci"]
    notes: list[str] = []
    for i, _ in enumerate(primary_loci):
        if i < len(o_loci):
            _, o_sym, o_note = o_loci[i]
            notes.append(f"overlay:{overlay}/{o_sym} ({o_note})")
        else:
            notes.append(f"overlay:{overlay}/—")
    return notes


# Locus contracts used when emitting Python stubs — structure optimizes work,
# not just folder names. Keys match mechanical locus stems (and common aliases).
_STAGE_CONTRACTS: dict[str, tuple[str, str]] = {
    "intent": (
        "Validate goals, limits, and entry contract for one run",
        "I/O, scoring, persistence, external side-effects",
    ),
    "intake": (
        "Pull/load raw records bounded by intent",
        "Scoring, filtering policy, durable store, final emission",
    ),
    "analyze": (
        "Score, filter, and decompose intake into structured results",
        "File/network I/O, persistence, operator-facing emission",
    ),
    "analysis": (
        "Score, filter, and decompose intake into structured results",
        "File/network I/O, persistence, operator-facing emission",
    ),
    "store": (
        "Persist foundation/substrate state",
        "New scoring rules, raw intake, final packaging for operators",
    ),
    "persist": (
        "Persist foundation/substrate state",
        "New scoring rules, raw intake, final packaging for operators",
    ),
    "output": (
        "Shape the concrete manifestation for operators/agents",
        "Intake, analysis rules, low-level store protocols",
    ),
    "emit": (
        "Shape the concrete manifestation for operators/agents",
        "Intake, analysis rules, low-level store protocols",
    ),
    "synthesis": (
        "Combine prior stage results into a coherent intermediate whole",
        "Raw intake, unrelated side-channels, silent policy changes",
    ),
    "constraint": (
        "Enforce schema/form limits on data or actions",
        "Bypassing validation, inventing new external sinks",
    ),
    "adversarial": (
        "Critique, challenge, or stress prior stage outputs",
        "Becoming the primary happy-path producer without review",
    ),
}


def _contract_for(mech: str, note: str) -> tuple[str, str]:
    """Return (allowed, forbidden) for a mechanical locus."""
    key = mech.lower().strip()
    if key in _STAGE_CONTRACTS:
        return _STAGE_CONTRACTS[key]
    # stem match: user_intake → intake
    for stem, pair in _STAGE_CONTRACTS.items():
        if key.endswith(stem) or key.startswith(stem):
            return pair
    # Fall back to locus note as "allowed" guidance
    allowed = note.strip() if note and not note.startswith("FORCED") else (
        f"Work that honestly belongs to locus '{mech}'"
    )
    forbidden = "Work belonging to other stages; invented symbolic loci; silent cross-cutting I/O"
    return allowed, forbidden


def _module_stub_py(mech: str, sym: str, note: str, overlay_line: str | None) -> str:
    """Emit a contract-oriented stub: map optimizes responsibilities, not names only."""
    overlay_doc = f"\nOverlay:    {overlay_line}" if overlay_line else ""
    allowed, forbidden = _contract_for(mech, note)
    # Safe string literals for generated Python
    mech_j, sym_j, note_j = json.dumps(mech), json.dumps(sym), json.dumps(note)
    allowed_j, forbidden_j = json.dumps(allowed), json.dumps(forbidden)
    return f'''"""
{mech} — dual-named stage (optimized by map)

mechanical: {mech}
symbolic:   {sym}
locus:      {note}{overlay_doc}

ALLOWED:    {allowed}
FORBIDDEN:  {forbidden}

Generated by Abraxas Orchestra {VERSION}.
Implement domain logic *inside* this contract — do not re-tangle other stages here.
"""

from __future__ import annotations

from typing import Any


def run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stage entrypoint. Keep side-effects within ALLOWED; refuse FORBIDDEN work."""
    data = dict(payload or {{}})
    # TODO: replace with real locus logic for `{mech}` / {sym}
    return {{
        "mechanical": {mech_j},
        "symbolic": {sym_j},
        "locus": {note_j},
        "status": "STAGE_OK",
        "input_keys": sorted(data.keys()),
    }}


def contract() -> dict[str, str]:
    """Machine-readable stage contract for agents and tests."""
    return {{
        "mechanical": {mech_j},
        "symbolic": {sym_j},
        "allowed": {allowed_j},
        "forbidden": {forbidden_j},
    }}
'''


def _write_skeleton(
    out_dir: Path,
    framework: str,
    meta: dict[str, Any],
    loci: list[tuple[str, str, str]],
    table: dict[str, Any],
    overlay_notes: list[str],
    *,
    python_stubs: bool = True,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "correspondence-table.json").write_text(
        json.dumps(table, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        f"# Skeleton — {framework} ({meta['title']})",
        "",
        f"Status: {table['status']}",
        f"Generated: {table['provenance']['timestamp']}",
        f"Skill: Orchestra {VERSION}",
    ]
    if table.get("pragmatic_projection"):
        lines.append(f"Projection: {table['pragmatic_projection']}")
    lines += [
        "",
        "## Dual-named modules (structure optimizes work)",
        "",
        "Each package is a **locus contract**: implement only ALLOWED work;",
        "keep FORBIDDEN work out. See also `examples/python-tree-of-life-pipeline/`.",
        "",
    ]
    for i, (mech, sym, note) in enumerate(loci):
        allowed, forbidden = _contract_for(mech, note)
        lines.append(f"### `{mech}/`")
        lines.append(f"- mechanical: `{mech}`")
        lines.append(f"- symbolic: `{sym}`")
        lines.append(f"- locus: {note}")
        lines.append(f"- **allowed:** {allowed}")
        lines.append(f"- **forbidden:** {forbidden}")
        ov = overlay_notes[i] if overlay_notes and i < len(overlay_notes) else None
        if ov:
            lines.append(f"- {ov}")
        lines.append("")
        mod_dir = out_dir / mech
        mod_dir.mkdir(parents=True, exist_ok=True)
        if python_stubs:
            (mod_dir / "__init__.py").write_text(
                _module_stub_py(mech, sym, note, ov), encoding="utf-8"
            )
        else:
            stub_body = [
                f"# {mech}",
                "",
                f"mechanical: `{mech}`",
                f"symbolic: `{sym}`",
                f"locus: {note}",
                f"allowed: {allowed}",
                f"forbidden: {forbidden}",
                "",
            ]
            if ov:
                stub_body.append(ov)
            (mod_dir / "README.md").write_text("\n".join(stub_body), encoding="utf-8")

    # Optional linear pipeline runner when multiple stages emit (Python)
    if python_stubs and len(loci) >= 2:
        mechs = [m for m, _, _ in loci]
        imports = "\n".join(
            f"from {m} import run as run_{m}" for m in mechs
        )
        body_lines = ["payload: dict[str, Any] = {}"]
        for m in mechs:
            body_lines.append(f"payload = run_{m}(payload)")
        body_lines.append("return payload")
        # Indent every body line so multi-stage chain stays inside run()
        chain_indented = "\n".join(f"    {line}" for line in body_lines)
        (out_dir / "pipeline.py").write_text(
            f'''#!/usr/bin/env python3
"""Linear stage runner generated by Orchestra {VERSION}.

Calls each dual-named stage in map order. Replace stage bodies with real logic
while keeping each stage inside its ALLOWED / FORBIDDEN contract.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

{imports}


def run() -> dict[str, Any]:
    """Execute stages in framework order (one-way along the map)."""
{chain_indented}


def main() -> int:
    print(json.dumps(run(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
            encoding="utf-8",
        )
        lines += [
            "## Generated `pipeline.py`",
            "",
            "Calls stages in map order. Implement each stage's `run()` under its contract.",
            "",
        ]
    (out_dir / "SKELETON.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_table(
    framework: str,
    overlay: str | None,
    loci: list[tuple[str, str, str]],
    overlay_notes: list[str],
    projection: str | None,
) -> dict[str, Any]:
    mappings = []
    forced = 0
    for i, (mech, sym, note) in enumerate(loci):
        strength = "FORCED" if note.startswith("FORCED") else "ADEQUATE"
        if strength == "FORCED":
            forced += 1
        entry: dict[str, Any] = {
            "functional_concern": note if not note.startswith("FORCED") else mech,
            "mechanical_name": mech,
            "symbolic_name": sym,
            "symbolic_locus": sym,
            "strength": strength,
            "notes": note,
        }
        if overlay_notes and i < len(overlay_notes):
            entry["overlay_note"] = overlay_notes[i]
        mappings.append(entry)
    status = "FORCED_CORRESPONDENCE" if forced else "CLEAN"
    return {
        "framework": framework,
        "secondary_overlay": overlay,
        "status": status,
        "mappings": mappings,
        "pragmatic_projection": projection,
        "provenance": {
            "operator": "orchestra-cli",
            "timestamp": _utc_now(),
            "skill_version": VERSION,
        },
    }


def _emit_structure(
    framework: str,
    overlay: str | None,
    concerns: list[str] | None,
    out: str | None,
    *,
    project: bool = False,
) -> int:
    if framework not in FRAMEWORKS:
        print(f"NOT_COMPUTABLE — unknown framework: {framework}", file=sys.stderr)
        print(f"Known: {', '.join(FRAMEWORKS)}", file=sys.stderr)
        return 2
    if overlay and overlay not in FRAMEWORKS:
        print(f"NOT_COMPUTABLE — unknown overlay: {overlay}", file=sys.stderr)
        return 2
    if overlay and overlay == framework:
        print("NOT_COMPUTABLE — overlay must differ from primary framework", file=sys.stderr)
        return 2
    loci = _select_loci(framework, concerns)
    projection: str | None = None
    if project:
        loci, projection = _apply_pragmatic_projection(framework, loci)
        if not loci:
            print("NOT_COMPUTABLE — pragmatic projection removed all loci", file=sys.stderr)
            return 2
    meta = FRAMEWORKS[framework]
    overlay_notes = _overlay_annotation(loci, overlay) if overlay else []
    table = _build_table(framework, overlay, loci, overlay_notes, projection)
    print("# Abraxas Orchestra — structure skeleton")
    print(f"# framework : {framework} ({meta['title']})")
    if overlay:
        print(f"# overlay   : {overlay} ({FRAMEWORKS[overlay]['title']})")
    if project:
        print("# mode      : project (pragmatic projection applied)")
    print(f"# status    : {table['status']}")
    if projection:
        print(f"# projection: {projection.strip()}")
    print(f"# generated : {table['provenance']['timestamp']}")
    print()
    print("## Dual-named skeleton")
    print()
    for i, (mech, sym, note) in enumerate(loci):
        print(f"{mech}/")
        print(f"  # mechanical : {mech}")
        print(f"  # symbolic   : {sym}")
        print(f"  # locus note : {note}")
        if overlay_notes and i < len(overlay_notes):
            print(f"  # {overlay_notes[i]}")
        print()
    print("## Correspondence table (JSON)")
    print()
    print(json.dumps(table, indent=2))
    print()
    if out:
        out_dir = Path(out).expanduser().resolve()
        _write_skeleton(out_dir, framework, meta, loci, table, overlay_notes, python_stubs=True)
        print(f"# wrote skeleton → {out_dir}")
        print("#   SKELETON.md")
        print("#   correspondence-table.json")
        for mech, _, _ in loci:
            print(f"#   {mech}/__init__.py")
        scripts_dir = str(Path(__file__).resolve().parent)
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from diagram_emit import emit_diagram_bundle
        emit_diagram_bundle(
            version=VERSION,
            frameworks=FRAMEWORKS,
            framework=framework,
            overlay=overlay,
            loci=loci,
            overlay_notes=overlay_notes,
            out_dir=out_dir,
            quiet=False,
        )
        print()
    if table["status"] == "FORCED_CORRESPONDENCE":
        print(
            "# WARNING: one or more concerns had no clean locus. "
            "Review FORCED mappings before accepting.",
            file=sys.stderr,
        )
        return 1
    return 0


def cmd_structure(args: argparse.Namespace) -> int:
    concerns = None
    if args.concerns:
        concerns = [c.strip() for c in args.concerns.split(",") if c.strip()]
    return _emit_structure(args.framework, args.overlay, concerns, args.out, project=False)


def cmd_project(args: argparse.Namespace) -> int:
    concerns = None
    if args.concerns:
        concerns = [c.strip() for c in args.concerns.split(",") if c.strip()]
    return _emit_structure(args.framework, args.overlay, concerns, args.out, project=True)


def cmd_diagram(args: argparse.Namespace) -> int:
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from diagram_emit import run_diagram, set_context
    set_context(VERSION, FRAMEWORKS)
    framework = args.framework
    overlay = args.overlay
    if framework not in FRAMEWORKS:
        print(f"NOT_COMPUTABLE — unknown framework: {framework}", file=sys.stderr)
        return 2
    if overlay and overlay not in FRAMEWORKS:
        print(f"NOT_COMPUTABLE — unknown overlay: {overlay}", file=sys.stderr)
        return 2
    if overlay and overlay == framework:
        print("NOT_COMPUTABLE — overlay must differ from primary framework", file=sys.stderr)
        return 2
    concerns = None
    if args.concerns:
        concerns = [c.strip() for c in args.concerns.split(",") if c.strip()]
    loci = _select_loci(framework, concerns)
    if getattr(args, "project", False):
        loci, _proj = _apply_pragmatic_projection(framework, loci)
        if not loci:
            print("NOT_COMPUTABLE — pragmatic projection removed all loci", file=sys.stderr)
            return 2
    overlay_notes = _overlay_annotation(loci, overlay) if overlay else []
    run_diagram(
        framework=framework,
        overlay=overlay,
        loci=loci,
        overlay_notes=overlay_notes,
        out=args.out,
    )
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from analyze_repo import analyze_path, write_analysis_artifacts

    analysis, code = analyze_path(
        args.path,
        frameworks=FRAMEWORKS,
        version=VERSION,
        framework=args.framework,
        overlay=args.overlay,
        lang=args.lang,
        max_depth=args.max_depth,
        max_files=args.max_files,
        allow_system=bool(getattr(args, "allow_system", False)),
    )
    if args.out:
        out_dir = Path(args.out).expanduser().resolve()
        write_analysis_artifacts(analysis, out_dir, version=VERSION)
        print(f"# wrote analysis → {out_dir}")
        print("#   analysis.json")
        if (out_dir / "structure-metrics.json").exists():
            print("#   structure-metrics.json")
        if (out_dir / "correspondence-table.json").exists():
            print("#   correspondence-table.json")
        print("#   architecture.json")
        print("#   architecture.html")
        print("#   architecture.mmd")
    else:
        print(json.dumps(analysis, indent=2))

    status = analysis.get("status")
    print(f"# status: {status}", file=sys.stderr)
    metrics = analysis.get("metrics")
    if metrics and not metrics.get("error"):
        from structure_metrics import format_metrics_summary

        print(format_metrics_summary(metrics), file=sys.stderr)
    if status == "NOT_COMPUTABLE":
        err = (analysis.get("provenance") or {}).get("error")
        if err:
            print(f"NOT_COMPUTABLE — {err}", file=sys.stderr)
    elif status in {"WEAK_MAPPINGS", "FORCED_CORRESPONDENCE"}:
        print(
            f"# WARNING: analysis status {status} — review before optimize.",
            file=sys.stderr,
        )
    return code


def cmd_optimize(args: argparse.Namespace) -> int:
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from optimize_apply import apply_optimize_plan
    from optimize_plan import build_optimize_plan, load_analysis, write_plan_artifacts

    try:
        analysis = load_analysis(args.from_analysis)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"NOT_COMPUTABLE — {exc}", file=sys.stderr)
        return 2

    if analysis.get("status") == "NOT_COMPUTABLE":
        print("NOT_COMPUTABLE — source analysis is NOT_COMPUTABLE", file=sys.stderr)
        return 2

    plan = build_optimize_plan(
        analysis,
        from_analysis=str(Path(args.from_analysis).expanduser().resolve()),
        min_strength=args.min_strength,
        version=VERSION,
    )

    if args.out:
        out_dir = Path(args.out).expanduser().resolve()
        write_plan_artifacts(plan, out_dir)
        print(f"# wrote optimize plan → {out_dir}")
        print("#   optimize-plan.json")
        print("#   OPTIMIZE.md")
    elif not getattr(args, "apply", False):
        print(json.dumps(plan, indent=2))

    if not plan.get("steps") and not getattr(args, "apply", False):
        print("# empty plan — nothing met strength threshold", file=sys.stderr)

    if getattr(args, "apply", False):
        confirm = bool(getattr(args, "confirm", False))
        refresh = bool(getattr(args, "refresh", False))
        step_ids = None
        raw_steps = getattr(args, "steps", None)
        if raw_steps:
            step_ids = [s.strip() for s in raw_steps.split(",") if s.strip()]
        actions_filter = None
        raw_actions = getattr(args, "actions", None)
        if raw_actions:
            actions_filter = [s.strip() for s in raw_actions.split(",") if s.strip()]
        report, code = apply_optimize_plan(
            analysis,
            plan,
            confirm=confirm,
            backup_dir=getattr(args, "backup_dir", None),
            version=VERSION,
            refresh=refresh,
            frameworks=FRAMEWORKS,
            step_ids=step_ids,
            actions_filter=actions_filter,
        )
        print(json.dumps(report, indent=2))
        if report.get("status") == "NOT_COMPUTABLE":
            print(f"NOT_COMPUTABLE — {report.get('error')}", file=sys.stderr)
        elif report.get("dry_run"):
            print(
                "# dry-run only — re-run with --apply --confirm to write "
                "(safe_apply rename/promote/flatten + backup)",
                file=sys.stderr,
            )
        else:
            print(
                f"# applied → backup {report.get('backup_dir')}",
                file=sys.stderr,
            )
            if report.get("refresh") and report["refresh"].get("out"):
                print(
                    f"# refreshed analysis → {report['refresh']['out']}",
                    file=sys.stderr,
                )
        return code
    return 0


# ---------------------------------------------------------------------------
# Arg builders (shared option shapes)
# ---------------------------------------------------------------------------


def _add_emit_args(sp: argparse.ArgumentParser) -> None:
    """Args shared by structure / project / diagram."""
    sp.add_argument("--framework", "-f", required=True, help="Primary framework key")
    sp.add_argument("--overlay", "-o", default=None, help="Secondary overlay framework")
    sp.add_argument("--concerns", "-c", default=None, help="Comma-separated concerns")
    sp.add_argument("--out", default=None, help="Write outputs to DIR")


def _add_diagram_args(sp: argparse.ArgumentParser) -> None:
    _add_emit_args(sp)
    sp.add_argument(
        "--project",
        action="store_true",
        help="Apply pragmatic projection before graphing",
    )


def _add_analyze_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--path", required=True, help="Local directory to analyze")
    sp.add_argument("--framework", "-f", default=None, help="Optional framework key for mapping")
    sp.add_argument("--overlay", "-o", default=None, help="Secondary overlay framework")
    sp.add_argument(
        "--lang",
        default="python",
        help=(
            "Language: python (default), javascript, typescript, go, rust, ruby, "
            "or auto (all supported extensions)"
        ),
    )
    sp.add_argument("--max-depth", type=int, default=None, help="Max directory depth")
    sp.add_argument("--max-files", type=int, default=2000, help="Cap files processed")
    sp.add_argument("--out", default=None, help="Write analysis + diagrams to DIR")
    sp.add_argument(
        "--allow-system",
        action="store_true",
        help="Permit analyzing system prefixes (dangerous; explicit)",
    )


def _add_optimize_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--from",
        dest="from_analysis",
        required=True,
        help="Path to analysis.json from analyze",
    )
    sp.add_argument("--out", default=None, help="Write optimize-plan.json + OPTIMIZE.md")
    sp.add_argument(
        "--min-strength",
        default="ADEQUATE",
        choices=["STRONG", "ADEQUATE", "WEAK", "FORCED"],
        help="Minimum mapping strength for plan steps (default ADEQUATE)",
    )
    sp.add_argument(
        "--apply",
        action="store_true",
        help="Apply safe_apply steps (dry-run unless --confirm)",
    )
    sp.add_argument(
        "--confirm",
        action="store_true",
        help="Required with --apply to perform writes (backup first)",
    )
    sp.add_argument(
        "--backup-dir",
        default=None,
        help="Backup directory for --apply --confirm (default under analyzed root)",
    )
    sp.add_argument(
        "--refresh",
        action="store_true",
        help="After --apply --confirm, re-analyze the tree and write analysis.json beside the backup",
    )
    sp.add_argument(
        "--steps",
        default=None,
        help="Comma-separated step ids to apply (default: all safe_apply steps)",
    )
    sp.add_argument(
        "--actions",
        default=None,
        help=(
            "Comma-separated action names to apply "
            "(suggest_rename,suggest_boundary,suggest_flatten)"
        ),
    )


def cmd_wizard(args: argparse.Namespace) -> int:
    """Guided plan (default) or execute resolved Orchestra command."""
    try:
        answers_in: dict | None = None
        if getattr(args, "answers", None):
            answers_in = load_answers(args.answers)
        preset = getattr(args, "preset", None)
        if preset or answers_in is not None:
            raw = merge_preset(preset, answers_in)
        else:
            if not sys.stdin.isatty():
                print(
                    "wizard: non-interactive use requires --answers and/or --preset "
                    "(Hermes Desktop: collect fields in chat, then pass --answers)",
                    file=sys.stderr,
                )
                return 2
            raw = interactive_collect(FRAMEWORKS)
        answers = validate_answers(raw, FRAMEWORKS)
        run = bool(getattr(args, "run", False))
        # Absence of --run means print-only; --print-only is a no-op for agents
        if getattr(args, "print_only", False) and run:
            print("wizard: both --print-only and --run set; using --run", file=sys.stderr)
        plan = resolve_plan(answers, FRAMEWORKS, run=run)
        if getattr(args, "json", False):
            sys.stdout.write(format_plan_json(plan))
        else:
            sys.stdout.write(format_plan_human(plan, skill_root_hint=str(Path(sys.argv[0]))))
        if not run:
            return 0
        return _wizard_run(plan)
    except WizardError as e:
        print(f"wizard error: {e.message}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"wizard error: invalid JSON: {e}", file=sys.stderr)
        return 2


def _wizard_run(plan: dict) -> int:
    """Dispatch resolved argv in-process; refuse re-entering wizard."""
    argv = list(plan["argv"])
    if not argv or argv[0] == "wizard":
        print("wizard error: refusing to dispatch wizard", file=sys.stderr)
        return 2
    return build_router().dispatch(argv)


def _add_wizard_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--answers",
        default=None,
        help="Path to answers JSON, or '-' for stdin",
    )
    sp.add_argument(
        "--preset",
        choices=["greenfield", "observe", "map", "optimize-plan"],
        default=None,
        help="Seed answers from a named preset",
    )
    sp.add_argument(
        "--print-only",
        action="store_true",
        help="Print plan only (default if --run omitted)",
    )
    sp.add_argument(
        "--run",
        action="store_true",
        help="Execute resolved command after printing plan",
    )
    sp.add_argument(
        "--json",
        action="store_true",
        help="Emit orchestra-wizard-plan.v1 JSON",
    )


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------


def build_router() -> CommandRouter:
    """Register all CLI commands on a single router."""
    router = CommandRouter(
        prog="orchestra",
        description="Abraxas Orchestra — symbolic code architecture CLI",
        version=VERSION,
    )
    router.add(CommandSpec(
        name="check",
        handler=cmd_check,
        help="Validate skill integrity",
        group="meta",
    ))
    router.add(CommandSpec(
        name="list",
        handler=cmd_list_frameworks,
        help="List available frameworks",
        aliases=("list-frameworks",),
        group="meta",
    ))
    router.add(CommandSpec(
        name="wizard",
        handler=cmd_wizard,
        help="Guided plan/execute for Hermes (answers JSON or interactive TTY)",
        group="meta",
        configure=_add_wizard_args,
    ))
    router.add(CommandSpec(
        name="structure",
        handler=cmd_structure,
        help="Emit dual-named skeleton + correspondence table",
        group="emit",
        configure=_add_emit_args,
    ))
    router.add(CommandSpec(
        name="project",
        handler=cmd_project,
        help="Emit skeleton with pragmatic projection (collapse oversized / forced maps)",
        group="emit",
        configure=_add_emit_args,
    ))
    router.add(CommandSpec(
        name="diagram",
        handler=cmd_diagram,
        help="Emit interactive HTML + agent JSON + Mermaid architecture graph",
        aliases=("diagrammit",),
        group="emit",
        configure=_add_diagram_args,
    ))
    router.add(CommandSpec(
        name="analyze",
        handler=cmd_analyze,
        help="Observe a local repo import graph; optionally map onto a framework",
        group="repo",
        configure=_add_analyze_args,
    ))
    router.add(CommandSpec(
        name="optimize",
        handler=cmd_optimize,
        help="Emit refactor plan from analysis.json (plan-only unless --apply --confirm)",
        group="repo",
        configure=_add_optimize_args,
    ))
    return router



def build_parser() -> argparse.ArgumentParser:
    """Back-compat: build the full CLI parser via the router."""
    return build_router().build_parser()


def main(argv: list[str] | None = None) -> int:
    return build_router().dispatch(argv)


if __name__ == "__main__":
    sys.exit(main())
