#!/usr/bin/env python3
"""Create the private path sidecar identified by hash in the unlock gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT.parent
INVENTORY = DRAFTS / "0725_CROSS_WELL_preunlock_integration_v4" / "0725_combined_acquisition_inventory_v5.csv"
SOURCE_MAP = ROOT / "registration" / "0726_frozen_scoring_source_map_v1.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--verify-sha256", action="store_true", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit(f"Refusing overwrite: {output}")
    expected = {row["archive_sha256"].upper(): row for row in read_csv(SOURCE_MAP)}
    inventory = read_csv(INVENTORY)
    rows = []
    for digest, source in sorted(expected.items()):
        matches = [row for row in inventory if row["sha256"].upper() == digest]
        if len(matches) != 1:
            raise RuntimeError(f"Inventory hash resolution count={len(matches)} for {digest}")
        item = matches[0]
        candidates = [
            Path(item["source_path"]),
            Path("D:/data") / item["basin_folder"] / item["file_name"],
            Path.home() / "Downloads" / item["file_name"],
        ]
        path = next(
            (
                candidate.resolve() for candidate in candidates
                if candidate.is_file() and candidate.stat().st_size == int(item["size_bytes"])
            ),
            None,
        )
        if path is None:
            raise RuntimeError(f"No size-matched local path for {digest}")
        actual = sha256(path)
        if actual != digest:
            raise RuntimeError(f"SHA-256 mismatch: {path}")
        rows.append({
            "archive_sha256": digest,
            "archive_name": source["archive_name"],
            "archive_path": str(path),
            "size_bytes": path.stat().st_size,
            "verified_sha256": actual,
        })
    payload = {
        "status": "PRIVATE_PREUNLOCK_PATH_SIDECAR",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "layer_D_numeric_ROP_accessed": False,
        "publication_status": "DO_NOT_PUBLISH_MACHINE_LOCAL_PATHS",
        "archives": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"archives": len(rows), "locator_sha256": sha256(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
