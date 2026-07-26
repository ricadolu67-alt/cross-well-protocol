#!/usr/bin/env python3
"""Populate protocol file hashes immediately before the v1.0 trusted timestamp."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER = "TO_" + "BE_FROZEN"


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
    environment_lock = root / "registration" / "0726_execution_environment_lock_v1.json"
    manifest["environment_lock_path"] = "registration/0726_execution_environment_lock_v1.json"
    manifest["environment_sha256"] = sha256(environment_lock)
    manifest["trusted_timestamp_service"] = (
        "OSF Registration (primary); GitHub signed immutable release (secondary); "
        "Zenodo DOI after execution"
    )
    manifest["trusted_timestamp_receipt_path"] = (
        "registration_external/0726_external_unlock_gate_completed_v1.json"
    )
    manifest["trusted_timestamp_receipt_sha256"] = "EXTERNAL_GATE_PENDING"
    manifest["outcome_access_status_at_manifest"] = "INACCESSIBLE_CONFIRMED_PRE_PAYLOAD"
    manifest["external_artifacts"] = [
        {
            "path": "../0725_CROSS_WELL_preunlock_integration_v4/0725_combined_acquisition_inventory_v5.csv",
            "sha256": "20917e0bfd144dc2d9ef10b3aa7c2eba592a012c2cb7498720cf7ca6ebb0310b",
            "role": "immutable_102_file_candidate_inventory",
        }
    ]
    manifest["signatures"] = [
        {
            "role": "protocol_owner_and_outcome_custodian",
            "name": "Lu Yuhan",
            "signed_at_utc": "EXTERNAL_GATE_PENDING",
            "signature_or_receipt": "OSF_AND_GITHUB_EVIDENCE_RECORDED_IN_EXTERNAL_GATE",
        }
    ]

    checklist_path = root / "v1.0_freeze_checklist.csv"
    with checklist_path.open(encoding="utf-8-sig", newline="") as handle:
        checklist = list(csv.DictReader(handle))
    nonpass = [
        row["check_id"] for row in checklist
        if row["check_id"] not in {"F23", "F24"} and row["status"] != "PASS"
    ]
    external_gate_status = {
        row["check_id"]: row["status"] for row in checklist
        if row["check_id"] in {"F23", "F24"}
    }
    if any(value != "EXTERNAL_GATE_PENDING" for value in external_gate_status.values()):
        raise RuntimeError("F23-F24 must remain EXTERNAL_GATE_PENDING in the timestamp payload")

    excluded_parts = {"__pycache__", "execution", "registration_external"}
    payload_files = []
    for target in sorted(root.rglob("*")):
        if not target.is_file() or any(part in excluded_parts for part in target.parts):
            continue
        relative = target.relative_to(root).as_posix()
        if relative in {"16_freeze_manifest.json", "SHA256SUMS.txt"} or target.suffix == ".pyc":
            continue
        payload_files.append({"path": relative, "sha256": ""})
    manifest["files"] = payload_files

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
        manifest["status"] = "PAYLOAD_READY_PENDING_EXTERNAL_TIMESTAMP_AND_UNLOCK_GATE"
        manifest["external_gate_checks"] = external_gate_status

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
