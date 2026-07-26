#!/usr/bin/env python3
"""Populate protocol file hashes immediately before the v1.0 trusted timestamp."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER = "TO_BE_FROZEN"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--generated-by", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    manifest_path = root / "16_freeze_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    checklist_path = root / "v1.0_freeze_checklist.csv"
    with checklist_path.open(encoding="utf-8-sig", newline="") as handle:
        checklist = list(csv.DictReader(handle))
    nonpass = [row["check_id"] for row in checklist if row["status"] != "PASS"]

    placeholder_files: list[str] = []
    for entry in manifest["files"]:
        relative = entry["path"]
        target = root / relative
        if not target.is_file():
            raise FileNotFoundError(f"Manifest target missing: {relative}")
        if PLACEHOLDER in target.read_text(encoding="utf-8-sig", errors="ignore"):
            placeholder_files.append(relative)

    if not args.allow_draft and (nonpass or placeholder_files):
        raise RuntimeError(
            "Refusing frozen manifest: "
            f"non-PASS checks={nonpass}; placeholder files={placeholder_files}"
        )

    for entry in manifest["files"]:
        entry["sha256"] = sha256(root / entry["path"])

    for entry in manifest.get("external_artifacts", []):
        if entry.get("path") == PLACEHOLDER:
            continue
        target = (root / entry["path"]).resolve()
        if target.is_file():
            entry["sha256"] = sha256(target)

    manifest["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["generated_by"] = args.generated_by
    manifest["git_commit_or_code_snapshot"] = args.git_commit
    if not args.allow_draft:
        manifest["schema_version"] = "1.0"
        manifest["protocol_id"] = "CROSS_WELL_PROTOCOL_v1.0-frozen"
        manifest["status"] = "FROZEN_PENDING_TRUSTED_TIMESTAMP"

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    sums = [
        f"{entry['sha256']}  {entry['path']}" for entry in manifest["files"]
    ]
    sums.append(f"{sha256(manifest_path)}  16_freeze_manifest.json")
    (root / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "files_hashed": len(manifest["files"]),
                "nonpass_checks": nonpass,
                "placeholder_files": placeholder_files,
                "manifest_sha256": sha256(manifest_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

