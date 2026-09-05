"""Same-filesystem staged installation with target-keyed rollback backups."""
import argparse
import fcntl
import os
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
FILES = ("SKILL.md", "orchestra.manifest.yaml", "VERSION", "README.md", "CHANGELOG.md",
         "LICENSE", "NOTICE", "scripts", "references", "schemas", "docs", "examples",
         "assets", "tests", "install.sh")


def check(path):
    for script, args in (("orchestra.py", ["check"]), ("integrity_check.py", [])):
        subprocess.run([sys.executable, str(path / "scripts" / script), *args],
                       check=True, cwd=path)


def activate(stage, target):
    previous = target.parent / (".orchestra-previous-" + uuid.uuid4().hex)
    if target.is_symlink():
        raise ValueError("target changed to a symlink")
    had_previous = target.exists()
    if had_previous:
        target.rename(previous)
    try:
        stage.rename(target)
        check(target)
    except BaseException:
        if target.exists():
            shutil.rmtree(target)
        if had_previous:
            previous.rename(target)
        raise
    if had_previous:
        shutil.rmtree(previous)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--backup-root", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    target = args.target.resolve()
    if target == ROOT or target in ROOT.parents or ROOT in target.parents:
        parser.error("source and target must not overlap")
    if args.target.is_symlink() or (target.exists() and not target.is_dir()):
        parser.error("target must be a directory, not a symlink or file")
    backups = args.backup_root.resolve() / hashlib.sha256(str(target).encode()).hexdigest()
    if target == backups or target in backups.parents or backups in target.parents:
        parser.error("backup and target must not overlap")
    source = ROOT
    if args.rollback:
        candidates = sorted(backups.glob("*/package"), key=lambda p: p.parent.name)
        if not candidates:
            parser.error("no backups for this exact target")
        source = candidates[-1]
        receipt = json.loads((source.parent / "target.json").read_text())
        if receipt["target"] != str(target):
            parser.error("backup target mismatch")
    print(f"{'Rollback' if args.rollback else 'Install'} {source} -> {target}")
    if args.dry_run:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    # Keep the lock inode in place; unlinking it would let waiters lock different files.
    lock_path = target.parent / ("." + target.name + ".install.lock")
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock_fd)
        parser.error("another installer holds this target lock")
    # Descriptor remains held until process exit, including rollback and postcheck.
    with tempfile.TemporaryDirectory(prefix=".orchestra-stage-", dir=target.parent) as tmp:
        stage = Path(tmp) / "package"
        if args.rollback:
            shutil.copytree(source, stage)
        else:
            stage.mkdir()
            for name in FILES:
                item = source / name
                if item.is_dir():
                    shutil.copytree(item, stage / name, ignore=shutil.ignore_patterns("__pycache__"))
                elif item.is_file():
                    shutil.copy2(item, stage / name)
        check(stage)
        if target.exists():
            from datetime import datetime, timezone
            backup = backups / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex)
            backup.mkdir(parents=True)
            shutil.copytree(target, backup / "package")
            (backup / "target.json").write_text(json.dumps({"target": str(target)}))
        activate(stage, target)
    print("Verified activation complete")


if __name__ == "__main__":
    main()
