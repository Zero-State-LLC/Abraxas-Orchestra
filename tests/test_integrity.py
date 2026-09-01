#!/usr/bin/env python3
"""Tests for critical-file integrity floors — stdlib only."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPT = ROOT / "scripts" / "integrity_check.py"


def _load_integrity():
    sys.path.insert(0, str(ROOT / "scripts"))
    import integrity_check  # type: ignore

    return integrity_check


def _skill_text(
    *,
    description: str = "Map software onto fail-closed symbolic correspondence maps.",
    extra_keys: bool = True,
    leading: str = "",
) -> str:
    body = (
        f"{leading}---\n"
        "name: orchestra\n"
        f"description: {description}\n"
        "version: 0.8.1\n"
        "author: Daniel Meyer (scrimshawlife-ctrl), Hermes Agent\n"
        "license: Apache-2.0\n"
        "platforms: [linux, macos]\n"
    )
    if extra_keys:
        body += (
            "metadata:\n"
            "  hermes:\n"
            "    tags: [architecture]\n"
            "    related_skills: []\n"
        )
    body += "---\n\n# Orchestra\nanalyze\noptimize\nwizard\n"
    return body


class TestIntegrityCheck(unittest.TestCase):
    def test_real_repo_passes(self) -> None:
        r = subprocess.run(
            [PYTHON, str(SCRIPT)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("INTEGRITY OK", r.stdout)

    def test_truncated_orchestra_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)
            # Minimal skill tree with truncated CLI
            (dest / "scripts").mkdir()
            (dest / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (dest / "SKILL.md").write_text(
                "---\nname: orchestra\nversion: 0.4.0\n---\n"
                "name: orchestra\nanalyze\noptimize\nwizard\nHERMES_SKILL_DIR\n"
                + ("x\n" * 50),
                encoding="utf-8",
            )
            (dest / "install.sh").write_text(
                "#!/bin/bash\nvalidate_target\nallow-outside-home\ndry-run\n"
                + ("# pad\n" * 160),
                encoding="utf-8",
            )
            # Copy real modules that must exist for floors, then truncate orchestra
            for rel in (
                "scripts/optimize_apply.py",
                "scripts/optimize_enrich.py",
                "scripts/optimize_rewrite.py",
                "scripts/orchestra_router.py",
                "scripts/analyze_repo.py",
                "scripts/analyze_langs.py",
                "scripts/optimize_plan.py",
                "scripts/coverage_report.py",
            ):
                shutil.copy2(ROOT / rel, dest / rel)
            (dest / "scripts" / "orchestra.py").write_text(
                "# truncated\nVERSION = '0.4.0'\n",
                encoding="utf-8",
            )
            r = subprocess.run(
                [PYTHON, str(SCRIPT), "--root", str(dest)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("INTEGRITY FAIL", r.stderr)
            self.assertIn("orchestra.py", r.stderr)


class TestSkillFrontmatter(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ic = _load_integrity()

    def test_real_skill_md_passes(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(self.ic.check_skill_frontmatter(text), [])
        desc_m = None
        for line in text.splitlines():
            if line.startswith("description:"):
                desc_m = self.ic._yaml_scalar(line.split(":", 1)[1])
                break
        self.assertIsNotNone(desc_m)
        assert desc_m is not None
        self.assertLessEqual(len(desc_m), self.ic.SKILL_DESC_MAX)
        self.assertTrue(desc_m.endswith("."))
        self.assertTrue(text.startswith("---"))

    def test_description_over_60_fails(self) -> None:
        long_desc = "A" * 61 + "."
        errs = self.ic.check_skill_frontmatter(_skill_text(description=long_desc))
        self.assertTrue(any("description is 62 chars" in e for e in errs), errs)

    def test_description_missing_period_fails(self) -> None:
        errs = self.ic.check_skill_frontmatter(
            _skill_text(description="Map software onto fail-closed maps")
        )
        self.assertTrue(any("period" in e for e in errs), errs)

    def test_quoted_description_excludes_quotes(self) -> None:
        desc = "Map software onto fail-closed symbolic correspondence maps."
        self.assertEqual(len(desc), 59)
        errs = self.ic.check_skill_frontmatter(
            _skill_text(description=f'"{desc}"')
        )
        self.assertEqual(errs, [])

    def test_leading_whitespace_fails(self) -> None:
        errs = self.ic.check_skill_frontmatter(_skill_text(leading="\n"))
        self.assertTrue(any("byte 0" in e for e in errs), errs)

    def test_missing_required_keys_fail(self) -> None:
        errs = self.ic.check_skill_frontmatter(_skill_text(extra_keys=False))
        joined = " ".join(errs)
        self.assertIn("metadata", joined)
        text = _skill_text()
        text = text.replace("author: Daniel Meyer (scrimshawlife-ctrl), Hermes Agent\n", "")
        errs = self.ic.check_skill_frontmatter(text)
        self.assertTrue(any("author" in e for e in errs), errs)

    def test_check_integrity_includes_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)
            (dest / "scripts").mkdir()
            (dest / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (dest / "SKILL.md").write_text(
                "---\nname: orchestra\nversion: 0.4.0\n---\n"
                "name: orchestra\nanalyze\noptimize\nwizard\nHERMES_SKILL_DIR\n"
                + ("x\n" * 50),
                encoding="utf-8",
            )
            (dest / "install.sh").write_text(
                "#!/bin/bash\nvalidate_target\nallow-outside-home\ndry-run\n"
                + ("# pad\n" * 160),
                encoding="utf-8",
            )
            for rel in (
                "scripts/optimize_apply.py",
                "scripts/optimize_enrich.py",
                "scripts/optimize_rewrite.py",
                "scripts/orchestra_router.py",
                "scripts/analyze_repo.py",
                "scripts/analyze_langs.py",
                "scripts/optimize_plan.py",
                "scripts/coverage_report.py",
                "scripts/orchestra.py",
            ):
                shutil.copy2(ROOT / rel, dest / rel)
            errs = self.ic.check_integrity(dest)
            self.assertTrue(any("description" in e for e in errs), errs)


class TestMappingNormalize(unittest.TestCase):
    def test_hyphen_underscore_adequate(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from analyze_repo import _map_node_to_locus  # type: ignore

        node = {"id": "pkg.edge_intake", "path": "edge_intake.py", "kind": "module"}
        loci = [("edge-intake", "Edge", "edge intake")]
        m = _map_node_to_locus(node, loci, source_text="")
        self.assertIsNotNone(m)
        assert m is not None
        self.assertIn(m["strength"], {"STRONG", "ADEQUATE"})
        self.assertEqual(m["mechanical_name"], "edge-intake")


if __name__ == "__main__":
    unittest.main()
