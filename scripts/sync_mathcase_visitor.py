#!/usr/bin/env python3
"""Copy the public MathCase visitor workbench from one verified public-main commit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile


EXPECTED_ORIGIN = {
    "https://github.com/DarthCeltic/MathCase",
    "https://github.com/DarthCeltic/MathCase.git",
    "git@github.com:DarthCeltic/MathCase",
    "git@github.com:DarthCeltic/MathCase.git",
    "ssh://git@github.com/DarthCeltic/MathCase",
    "ssh://git@github.com/DarthCeltic/MathCase.git",
}
MAX_FILES = 100
MAX_TOTAL_BYTES = 2_000_000
REQUIRED_FILES = {"visitor/index.html", "visitor/workbench.css", "visitor/workbench.js"}


class SyncError(RuntimeError):
    pass


def run_git(repo: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise SyncError(f"git {' '.join(args)} failed ({result.returncode}): {message}")
    return result.stdout


def normalized_origin(repo: Path) -> str:
    raw = run_git(repo, "remote", "get-url", "origin").decode("utf-8").strip()
    if raw not in EXPECTED_ORIGIN:
        raise SyncError(f"origin is not the public MathCase repository: {raw!r}")
    return raw


def verify_commit(repo: Path, source_commit: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise SyncError("--source-commit must be a full 40-character lowercase commit hash")
    resolved = run_git(repo, "rev-parse", "--verify", f"{source_commit}^{{commit}}").decode("ascii").strip()
    if resolved != source_commit:
        raise SyncError("Git resolved the supplied commit to a different object")
    main_ref = subprocess.run(
        ["git", "-C", str(repo), "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if main_ref.returncode != 0:
        raise SyncError("origin/main is unavailable; fetch the public main branch before syncing")
    ancestor = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", source_commit, "refs/remotes/origin/main"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if ancestor.returncode != 0:
        raise SyncError("source commit is not contained in the local origin/main history")
    return resolved


def source_entries(repo: Path, source_commit: str) -> list[tuple[str, str]]:
    raw = run_git(repo, "ls-tree", "-r", "-z", "--full-tree", source_commit, "--", "visitor/")
    entries: list[tuple[str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        path = path_bytes.decode("utf-8")
        pure = PurePosixPath(path)
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise SyncError(f"refusing non-regular visitor entry: {path}")
        if pure.is_absolute() or pure.parts[0] != "visitor" or ".." in pure.parts:
            raise SyncError(f"unsafe source path: {path}")
        entries.append((path, object_id))
    if not entries:
        raise SyncError("the selected public commit contains no tracked visitor/ files")
    if len(entries) > MAX_FILES:
        raise SyncError(f"visitor/ has {len(entries)} files; limit is {MAX_FILES}")
    missing = REQUIRED_FILES - {path for path, _ in entries}
    if missing:
        raise SyncError("visitor workbench is incomplete; missing " + ", ".join(sorted(missing)))
    return entries


def copy_snapshot(repo: Path, source_commit: str, entries: list[tuple[str, str]], stage: Path) -> list[dict[str, object]]:
    manifest_files: list[dict[str, object]] = []
    total = 0
    for path, object_id in entries:
        content = run_git(repo, "cat-file", "blob", object_id)
        total += len(content)
        if total > MAX_TOTAL_BYTES:
            raise SyncError(f"visitor/ exceeds the {MAX_TOTAL_BYTES}-byte safety limit")
        relative = PurePosixPath(path).relative_to("visitor")
        destination = stage.joinpath(*relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        manifest_files.append({
            "path": path,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    return manifest_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mathcase-repo", type=Path, required=True, help="local public MathCase clone")
    parser.add_argument("--source-commit", required=True, help="full commit SHA containing the approved visitor/ tree")
    parser.add_argument(
        "--backup-existing-to",
        type=Path,
        help="move an existing site visitor/ directory and manifest into this new backup folder before replacing; folder must be outside this repo",
    )
    args = parser.parse_args()

    site_root = Path(__file__).resolve().parents[1]
    destination = site_root / "visitor"
    manifest_path = site_root / "evidence" / "visitor-workbench" / "source-manifest.json"
    stage: Path | None = None
    backup_root: Path | None = None

    try:
        repo = args.mathcase_repo.resolve(strict=True)
        normalized_origin(repo)
        source_commit = verify_commit(repo, args.source_commit)
        entries = source_entries(repo, source_commit)

        if destination.exists() or manifest_path.exists():
            if args.backup_existing_to is None:
                raise SyncError("site visitor/ or its source manifest already exists; provide --backup-existing-to for a preserved replacement")
            backup_root = args.backup_existing_to.resolve()
            if site_root == backup_root or site_root in backup_root.parents:
                raise SyncError("the backup must be outside the Pages repository")
            if backup_root.drive.lower() != site_root.drive.lower():
                raise SyncError("the backup must be on the same drive as the Pages repository for a safe directory swap")
            if backup_root.exists():
                raise SyncError(f"backup destination already exists: {backup_root}")

        stage_parent = site_root
        with tempfile.TemporaryDirectory(prefix=".visitor-sync-", dir=stage_parent) as temporary:
            stage = Path(temporary) / "visitor"
            stage.mkdir()
            files = copy_snapshot(repo, source_commit, entries, stage)
            tree_bytes = sum(int(item["bytes"]) for item in files)
            manifest = {
                "schema": "mathcase-visitor-workbench-source-v1",
                "source_repository": "https://github.com/DarthCeltic/MathCase",
                "source_branch": "main",
                "source_commit": source_commit,
                "source_path": "visitor/",
                "files": files,
                "total_bytes": tree_bytes,
            }
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_temp = manifest_path.with_suffix(".json.tmp")
            manifest_temp.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="ascii", newline="\n")

            if backup_root is not None:
                backup_root.mkdir(parents=True)
                if destination.exists():
                    destination.replace(backup_root / "visitor")
                if manifest_path.exists():
                    manifest_path.replace(backup_root / "source-manifest.json")
            try:
                stage.replace(destination)
                manifest_temp.replace(manifest_path)
            except Exception:
                if destination.exists() and backup_root is not None:
                    destination.replace(backup_root / "visitor-new")
                if backup_root is not None:
                    saved_visitor = backup_root / "visitor"
                    saved_manifest = backup_root / "source-manifest.json"
                    if saved_visitor.exists() and not destination.exists():
                        saved_visitor.replace(destination)
                    if saved_manifest.exists() and not manifest_path.exists():
                        saved_manifest.replace(manifest_path)
                manifest_temp.unlink(missing_ok=True)
                raise

        print(f"Copied {len(files)} files ({tree_bytes} bytes) from MathCase {source_commit} to visitor/.")
        print(f"Source manifest: {manifest_path.relative_to(site_root).as_posix()}")
        return 0
    except (OSError, UnicodeError, SyncError, subprocess.SubprocessError) as exc:
        print(f"sync refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
