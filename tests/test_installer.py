"""Installer integration checks use only disposable homes and checkouts."""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def invoke(tmp_path, *args, source=ROOT):
    home = tmp_path / 'home'
    home.mkdir(exist_ok=True)
    env = dict(os.environ, HOME=str(home), HERMES_HOME=str(home / 'profile'))
    return subprocess.run(['bash', str(source / 'install.sh'), *args], cwd=tmp_path,
                          env=env, text=True, capture_output=True)


def test_profile_install_and_dry_run(tmp_path):
    result = invoke(tmp_path, '--dry-run')
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / 'home/profile').exists()
    result = invoke(tmp_path)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'home/profile/skills/orchestra/SKILL.md').is_file()
    assert not (tmp_path / 'home/.hermes').exists()


def test_runtime_failure_preserves_install(tmp_path):
    source = tmp_path / 'source'
    shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', 'graft', '__pycache__'))
    (source / 'scripts/orchestra.py').write_text('raise SystemExit(42)\n')
    target = tmp_path / 'home/profile/skills/orchestra'
    target.mkdir(parents=True)
    (target / 'sentinel').write_text('previous')
    result = invoke(tmp_path, source=source)
    assert result.returncode != 0
    assert (target / 'sentinel').read_text() == 'previous'


def test_rollback_is_target_scoped(tmp_path):
    for name in ('a', 'b'):
        target = tmp_path / 'home' / name
        target.mkdir(parents=True, exist_ok=True)
        # A valid old package plus a target-specific sentinel.
        shutil.copytree(ROOT, target, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git', 'graft', '__pycache__'))
        (target / 'sentinel').write_text(name)
        result = invoke(tmp_path, '--target', str(target))
        assert result.returncode == 0, result.stderr
    target = tmp_path / 'home/a'
    result = invoke(tmp_path, '--target', str(target), '--rollback')
    assert result.returncode == 0, result.stderr
    assert (target / 'sentinel').read_text() == 'a'


def test_refuse_source_ancestry(tmp_path):
    result = invoke(tmp_path, '--target', str(ROOT), '--allow-outside-home', '--dry-run')
    assert result.returncode != 0


def test_final_symlink_is_refused(tmp_path):
    actual = tmp_path / "home/actual"
    actual.mkdir(parents=True)
    (actual / "sentinel").write_text("keep")
    alias = tmp_path / "home/alias"
    alias.symlink_to(actual, target_is_directory=True)
    result = invoke(tmp_path, "--target", str(alias), "--dry-run")
    assert result.returncode != 0
    assert (actual / "sentinel").read_text() == "keep"


def test_concurrent_target_lock_is_refused(tmp_path):
    import fcntl
    parent = tmp_path / "home/profile/skills"
    parent.mkdir(parents=True)
    with (parent / ".orchestra.install.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = invoke(tmp_path)
    assert result.returncode != 0
    assert not (parent / "orchestra").exists()
