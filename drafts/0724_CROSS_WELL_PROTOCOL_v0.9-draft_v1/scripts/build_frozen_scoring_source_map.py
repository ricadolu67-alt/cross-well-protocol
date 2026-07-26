#!/usr/bin/env python3
"""Build the pre-unlock scoring-source map without reading member payloads."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT.parent
INVENTORY = DRAFTS / "0725_CROSS_WELL_preunlock_integration_v4" / "0725_combined_acquisition_inventory_v5.csv"
FAMILY_STATUS = DRAFTS / "0725_CROSS_WELL_preunlock_integration_v4" / "0725_combined_T1b_family_status_v4.csv"
COHORT = ROOT / "11e_final_preunlock_cohort_manifest.csv"
CONTRACTS = [
    ROOT / "05_measurement_semantic_contract.csv",
    ROOT / "05d_extension_v4_measurement_semantic_contract.csv",
]
OUT = ROOT / "registration" / "0726_frozen_scoring_source_map_v1.csv"
REPORT = ROOT / "registration" / "0726_frozen_scoring_source_map_report_v1.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    inventory = read_csv(INVENTORY)
    for row in inventory:
        recorded = Path(row["source_path"])
        alternatives = [
            recorded,
            Path("D:/data") / row["basin_folder"] / row["file_name"],
            Path.home() / "Downloads" / row["file_name"],
        ]
        existing = [path for path in alternatives if path.is_file()]
        size_matched = [
            path for path in existing
            if path.stat().st_size == int(row["size_bytes"])
        ]
        if len(size_matched) == 1:
            row["source_path"] = str(size_matched[0])
    inv_by_name: dict[str, list[dict[str, str]]] = {}
    for row in inventory:
        inv_by_name.setdefault(row["file_name"].casefold(), []).append(row)

    statuses = {
        row["nopta_well_id"]: row for row in read_csv(FAMILY_STATUS)
    }
    contract_by_scope: dict[str, list[dict[str, str]]] = {}
    for contract in CONTRACTS:
        for row in read_csv(contract):
            if row["ambiguity_status"] == "PASS":
                contract_by_scope.setdefault(row["archive_scope"], []).append(row)

    member_index: dict[str, list[dict[str, str]]] = {}

    def locate_by_member(member: str) -> list[dict[str, str]]:
        if member in member_index:
            return member_index[member]
        matches: list[dict[str, str]] = []
        for item in inventory:
            path = Path(item["source_path"])
            if not path.is_file() or path.suffix.casefold() != ".zip":
                continue
            try:
                with zipfile.ZipFile(path) as zf:
                    names = set(zf.namelist())
                if member in names:
                    matches.append(item)
            except (OSError, zipfile.BadZipFile):
                continue
        member_index[member] = matches
        return matches

    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for family in read_csv(COHORT):
        if family["T2_qualified"].lower() != "true":
            continue
        scope_prefix = (
            f'{family["basin_context"]}|{family["petroleum_field"]}|'
            f'{family["nopta_well_id"]}|'
        )
        scopes = [scope for scope in contract_by_scope if scope.startswith(scope_prefix)]
        if len(scopes) != 1:
            errors.append(f'{family["dependence_family_id"]}: semantic scope count={len(scopes)}')
            continue
        scope = scopes[0]
        member = scope[len(scope_prefix):]
        mappings = contract_by_scope[scope]
        by_canonical = {row["canonical_name"]: row for row in mappings}
        required = {
            "measured_depth", "weight_on_bit", "surface_rotary_speed",
            "standpipe_pressure", "rate_of_penetration",
        }
        if set(by_canonical) != required:
            errors.append(f'{family["dependence_family_id"]}: incomplete canonical mapping')
            continue

        status = statuses.get(family["nopta_well_id"], {})
        archive_name = status.get("selected_archive_name") or status.get("archive_names") or family.get("archive_names", "")
        candidates = inv_by_name.get(archive_name.casefold(), []) if archive_name else []
        if len(candidates) != 1:
            candidates = locate_by_member(member)
        if len(candidates) != 1:
            errors.append(
                f'{family["dependence_family_id"]}: archive resolution count={len(candidates)} for {member}'
            )
            continue
        archive = candidates[0]
        path = Path(archive["source_path"])
        with zipfile.ZipFile(path) as zf:
            if member not in set(zf.namelist()):
                errors.append(f'{family["dependence_family_id"]}: selected member missing')
                continue

        row = {
            "record_status": "PREUNLOCK_FROZEN_SOURCE_MAP",
            "dependence_family_id": family["dependence_family_id"],
            "basin_context": family["basin_context"],
            "petroleum_field": family["petroleum_field"],
            "nopta_well_id": family["nopta_well_id"],
            "well_name": family["well_name"],
            "archive_name": archive["file_name"],
            "archive_source_pool": archive["source_pool"],
            "archive_basin_folder": archive["basin_folder"],
            "archive_sha256": archive["sha256"].upper(),
            "selected_source_object": member,
            "md_mnemonic": by_canonical["measured_depth"]["raw_mnemonic"],
            "md_original_uom": by_canonical["measured_depth"]["original_uom"],
            "md_conversion": by_canonical["measured_depth"]["conversion"],
            "wob_mnemonic": by_canonical["weight_on_bit"]["raw_mnemonic"],
            "wob_original_uom": by_canonical["weight_on_bit"]["original_uom"],
            "wob_conversion": by_canonical["weight_on_bit"]["conversion"],
            "rpm_mnemonic": by_canonical["surface_rotary_speed"]["raw_mnemonic"],
            "rpm_original_uom": by_canonical["surface_rotary_speed"]["original_uom"],
            "rpm_conversion": by_canonical["surface_rotary_speed"]["conversion"],
            "spp_mnemonic": by_canonical["standpipe_pressure"]["raw_mnemonic"],
            "spp_original_uom": by_canonical["standpipe_pressure"]["original_uom"],
            "spp_conversion": by_canonical["standpipe_pressure"]["conversion"],
            "rop_mnemonic": by_canonical["rate_of_penetration"]["raw_mnemonic"],
            "rop_original_uom": by_canonical["rate_of_penetration"]["original_uom"],
            "rop_conversion": by_canonical["rate_of_penetration"]["conversion"],
            "numeric_member_payload_read_during_map_build": "false",
        }
        rows.append(row)

    if errors:
        raise SystemExit("\n".join(errors))
    rows.sort(key=lambda row: (row["basin_context"], row["petroleum_field"], row["dependence_family_id"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report = (
        "# Frozen scoring-source map\n\n"
        f"- Qualified families mapped: {len(rows)}\n"
        f"- Unique archives: {len({row['archive_sha256'] for row in rows})}\n"
        "- Public payload stores archive names and hashes but no machine-local absolute paths.\n"
        "- Resolution used frozen cohort, semantic contract, acquisition inventory, "
        "and ZIP central-directory names only.\n"
        "- Numeric member payloads read: no.\n"
        f"- CSV SHA-256: `{sha256(OUT)}`\n"
    )
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({"families": len(rows), "sha256": sha256(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
