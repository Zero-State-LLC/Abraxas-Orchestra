# Framework fit guide

When to pick which map for `structure` / `project` / `analyze -f`, and how to read strength scores.

Live threat model: `docs/SECURITY.md` · CLI surface: `docs/DESIGN.md`

## Strength labels (fail-closed)

| Strength | Meaning | Optimize apply |
|----------|---------|----------------|
| `STRONG` | Leaf or module id equals mechanical or symbolic locus | Eligible if other gates pass |
| `ADEQUATE` | Path segment / normalized name / token overlap with locus | Eligible |
| `WEAK` | Loose token overlap only | Plan may list; apply blocked for that step |
| `FORCED` | Required concern with no honest locus | Blocks apply entirely |

Analyze exit codes: `0` CLEAN / OBSERVED_ONLY · `1` WEAK_MAPPINGS present · `2` NOT_COMPUTABLE.

**Agent rule:** Do not invent loci. Prefer `analyze` without `-f` first when the tree is unfamiliar, then pick a framework from suggestions or this guide.

## Which framework for which shape

| Shape of the code | Prefer | Why |
|-------------------|--------|-----|
| Linear pipeline / stages (intake → process → out) | `tree-of-life` (**Python best case**), `alchemical-stages` | Ordered stages map cleanly to modules when names match loci |
| Layered agent / multi-domain system | `enochian`, `chaos-magic` (overlay) | Domains + seals + intent layers |
| Ranked authority / command hierarchy | `solomonic`, `planetary-spheres` | Clear rank order |
| Token / sign / interface taxonomy | `peircean-signs` | Types of signs ↔ API roles |
| Cyclic zones / zones of recursion | `numogram` | Zone graph, not a single pipeline |
| Discrete rune-like capabilities | `elder-futhark` | Many peer modules with distinct roles |
| Decision / oracle branching | `iching-hexagrams` | Branching states |
| Geometry / layout / structure-first | `sacred-geometry` | Spatial / structural metaphors |

## Practical workflow

```bash
# 1. Observe only
python3 scripts/orchestra.py analyze --path ./pkg --out /tmp/orch-an

# 2. If suggestions look right, re-run with -f
python3 scripts/orchestra.py analyze --path ./pkg -f alchemical-stages --out /tmp/orch-an

# 3. Plan only — never apply on WEAK/FORCED without human review
python3 scripts/orchestra.py optimize --from /tmp/orch-an/analysis.json --out /tmp/orch-plan

# 4. Dry-run apply, then confirm
python3 scripts/orchestra.py optimize --from /tmp/orch-an/analysis.json --apply
python3 scripts/orchestra.py optimize --from /tmp/orch-an/analysis.json --apply --confirm
```

## Python best case (tree-of-life)

When building a staged Python package, choose concerns that **are** framework mechanical names:

```bash
python3 scripts/orchestra.py structure \
  -f tree-of-life \
  -c "intent,intake,analyze,store,output" \
  --out ./myapp-skel
```

| Mechanical | Symbolic | Role |
|------------|----------|------|
| `intent` | kether | Entry contract |
| `intake` | chokmah | Load / pull |
| `analyze` | hod | Score / transform |
| `store` | yesod | Persist |
| `output` | malkuth | Emit |

Hermes: route **emit** → `structure`, then implement logic **optimized by** each locus
(not rename-only). Full working example: `examples/python-tree-of-life-pipeline/`.  
Site demo: [before & after](https://scrimshawlife-ctrl.github.io/Abraxas-Orchestra/#before-after).

## Naming tips that improve fit

- Name modules after **mechanical locus** strings in `schemas/frameworks.v1.json` when you own the tree.
- Underscores / hyphens normalize for matching (`edge_intake` ≈ `edge-intake` style loci).
- Put role words in the **module leaf** or package segment, not only deep in comments.
- For greenfield work, prefer `structure` / `project` emit over force-fitting a messy tree.

## How mapping scores (0.4.2+)

Analyzer heuristics (still **fail-closed** — loci only from `frameworks.v1.json`):

| Signal | Typical strength |
|--------|------------------|
| Leaf / path equals mechanical or symbolic (incl. hyphen-normalize) | `STRONG` |
| Strip boilerplate suffix (`_handler`, `_service`, `_module`, …) then match | `STRONG` / `ADEQUATE` |
| Compound name contains full locus (`user_intake` → `intake`) | `ADEQUATE` |
| Role synonyms (`repository`→store family, `emit`→output, `cli`→entry/intent, …) | `ADEQUATE` / `WEAK` |
| Module docstring + `def`/`class` names token overlap with locus notes | boosts score |
| Single loose token only | `WEAK` |

`match_score` on each mapping is a secondary tie-break (higher is better) within the same strength.

## When not to map

- Generated / vendor trees — exclude or narrow `--path`
- Pure libraries with no architectural stages — use OBSERVED graph + diagrams only
- Polyglot monorepos where non-Python edges are critical to correctness — import-surface parsers are **not** full language compilers (see below)

## Multi-language analyze (limits)

| Language | Fidelity |
|----------|----------|
| Python | Full AST import graph |
| JavaScript / TypeScript | Token + structured import/export/require nodes |
| Go | Token + structured `import` declarations |
| Rust | Token + structured `use` / `mod` |
| Ruby | Token + structured `require` / `require_relative` |
| `auto` | Union of the above extensions |

Non-Python resolution is best-effort (relative paths when possible; packages stay external). Optimize apply remains Python-oriented. Details: `scripts/analyze_langs.py`, `docs/DESIGN.md`.

Canonical loci: `schemas/frameworks.v1.json` · Human tables: `references/`
