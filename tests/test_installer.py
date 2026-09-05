"""Installer integration checks use only disposable homes and checkouts."""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

import pytest

@pytest.mark.parametrize("component", ["skills", "profile", "leaf", "dotdot"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_symlink_redirect_is_refused(tmp_path, component, dry_run):
    profile = tmp_path / "home/profile"
    other = tmp_path / "home/other"
    other.mkdir(parents=True)
    (other / "sentinel").write_text("keep")
    if component == "profile":
        profile.symlink_to(other, target_is_directory=True)
    else:
        profile.mkdir()
        if component == "skills":
            (profile / "skills").symlink_to(other, target_is_directory=True)
        else:
            (profile / "skills").mkdir()
            (profile / "skills" / 'orchestra').symlink_to(other, target_is_directory=True)
    env = dict(os.environ, HOME=str(tmp_path / "home"), HERMES_HOME=str(profile))
    command = ["bash", str(ROOT / "install.sh")]
    if component == "dotdot":
        command += ["--target", str(profile / "skills" / 'orchestra' / ".." / "redirected")]
    result = subprocess.run(command + (["--dry-run"] if dry_run else []),
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode != 0, result.stdout
    assert "symlink" in result.stderr.lower(), result.stderr
    assert (other / "sentinel").read_text() == "keep"
    assert sorted(p.name for p in other.iterdir()) == ["sentinel"]



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




def test_target_is_rechecked_after_lock(tmp_path, monkeypatch):
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install_package.py")
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    parent = tmp_path / "skills"
    parent.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    target = parent / "orchestra"
    monkeypatch.setattr(sys, "argv", ["installer", "--target", str(target),
                                      "--backup-root", str(tmp_path / "backups")])
    real_flock = installer.fcntl.flock
    def redirect_after_lock(fd, flags):
        real_flock(fd, flags)
        parent.rename(tmp_path / "old-skills")
        parent.symlink_to(other, target_is_directory=True)
    monkeypatch.setattr(installer.fcntl, "flock", redirect_after_lock)
    with pytest.raises(ValueError, match="symlink"):
        installer.main()
    assert list(other.iterdir()) == []


def test_rollback_selection_is_locked(tmp_path, monkeypatch):
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install_package.py")
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    monkeypatch.setattr(sys, "argv", ["installer", "--target", str(tmp_path / "skills/orchestra"),
                                      "--backup-root", str(tmp_path / "backups"), "--rollback"])
    locked = False
    real_flock = installer.fcntl.flock
    def lock(fd, flags):
        nonlocal locked
        real_flock(fd, flags)
        locked = True
    def candidates(path, pattern):
        assert locked, "rollback candidates selected before transaction lock"
        return iter(())
    monkeypatch.setattr(installer.fcntl, "flock", lock)
    monkeypatch.setattr(Path, "glob", candidates)
    with pytest.raises(SystemExit):
        installer.main()




def test_failed_activation_keeps_competing_installer_out(tmp_path):
    import sys
    target = tmp_path / "skills/orchestra"
    target.mkdir(parents=True)
    (target / "sentinel").write_text("original")
    # Pause logically at A's postcheck by invoking B there, then fail A.
    # Real subprocesses and flock; no sleeps or scheduler assumptions.
    code = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import install_package as installer
import subprocess
target = Path(sys.argv[2])
backups = sys.argv[3]
def check(path):
    if path == target:
        result = subprocess.run([sys.executable, str(installer.ROOT / 'scripts/install_package.py'),
            '--target', str(target), '--backup-root', backups], capture_output=True, text=True)
        assert result.returncode != 0 and 'target lock' in result.stderr, result
        raise RuntimeError('injected postcheck failure')
installer.check = check
sys.argv = ['installer', '--target', str(target), '--backup-root', backups]
try:
    installer.main()
except RuntimeError as exc:
    assert str(exc) == 'injected postcheck failure'
else:
    raise AssertionError('postcheck must fail')
"""
    result = subprocess.run([sys.executable, "-c", code, str(ROOT / "scripts"), str(target),
                             str(tmp_path / "backups")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (target / "sentinel").read_text() == "original"
    assert sorted(p.name for p in target.iterdir()) == ["sentinel"]


def test_concurrent_target_lock_is_refused(tmp_path):
    import fcntl
    parent = tmp_path / "home/profile/skills"
    parent.mkdir(parents=True)
    with (parent / ".orchestra.install.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = invoke(tmp_path)
    assert result.returncode != 0
    assert not (parent / "orchestra").exists()
