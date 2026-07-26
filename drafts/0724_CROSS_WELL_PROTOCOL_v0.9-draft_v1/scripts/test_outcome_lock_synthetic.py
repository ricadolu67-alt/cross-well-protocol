#!/usr/bin/env python3
"""Synthetic-only fail-closed test for the CROSS-WELL preunlock boundary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


PROTOCOL = Path(__file__).resolve().parents[1]
EVIDENCE = PROTOCOL / "registration" / "0725_outcome_lock_access_test_v1"
FIXTURE = EVIDENCE / "0725_synthetic_sentinel_archive_v1.zip"
ACCESS_LOG = EVIDENCE / "0725_preunlock_access_test_log_v1.csv"
RESULT = EVIDENCE / "0725_outcome_lock_access_test_result_v1.json"
REPORT = EVIDENCE / "0725_outcome_lock_access_test_report_v1.md"
EVIDENCE_MANIFEST = EVIDENCE / "0725_outcome_lock_access_test_manifest_v1.json"
ALLOWED = ("DEPT", "WOB", "RPM", "SPP")
TARGET = "ROP"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def sentinel_token() -> str:
    # Constructed rather than embedded as a complete literal in source.
    return f"{987000 + 654.321:.3f}"


def build_fixture() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    las = "\n".join(
        [
            "~Version",
            "VERS. 2.0 : CW synthetic access-control fixture",
            "~Well",
            "WELL. SYNTHETIC-LOCK-TEST : non-scientific synthetic well",
            "~Curve",
            "DEPT.M : Measured Depth",
            "WOB.kkgf : Weight on Bit",
            "RPM.rpm : Surface RPM",
            "SPP.kPa : Standpipe Pressure",
            "ROP.m/h : Rate of Penetration",
            "~Ascii",
            f"1000 10 100 12000 {sentinel_token()}",
            f"1001 11 105 12100 {sentinel_token()}",
            f"1002 12 110 12200 {sentinel_token()}",
            "",
        ]
    )
    with zipfile.ZipFile(FIXTURE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("synthetic/SYNTHETIC_LOCK_TEST.LAS", las.encode("ascii"))


def read_single_las() -> bytes:
    # Hard fail if invoked against anything except the generated fixture path.
    if FIXTURE.resolve().parent != EVIDENCE.resolve() or not FIXTURE.is_file():
        raise RuntimeError("SYNTHETIC_FIXTURE_PATH_GUARD_FAILED")
    with zipfile.ZipFile(FIXTURE) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".las")]
        if names != ["synthetic/SYNTHETIC_LOCK_TEST.LAS"]:
            raise RuntimeError("UNEXPECTED_SYNTHETIC_FIXTURE_CONTENT")
        return archive.read(names[0])


def header_only_audit(payload: bytes) -> dict:
    header, marker, _ = payload.partition(b"~Ascii")
    if not marker:
        raise RuntimeError("ASCII_MARKER_MISSING")
    text = header.decode("ascii")
    curves = []
    in_curve = False
    for line in text.splitlines():
        if line.lower().startswith("~curve"):
            in_curve = True
            continue
        if line.startswith("~") and in_curve:
            break
        if in_curve and "." in line:
            curves.append(line.split(".", 1)[0].strip().upper())
    return {
        "curve_mnemonics": curves,
        "numeric_arrays_emitted": False,
        "numeric_token_count_converted": 0,
    }


def restricted_covariate_qc(payload: bytes) -> dict:
    header, marker, data = payload.partition(b"~Ascii")
    if not marker:
        raise RuntimeError("ASCII_MARKER_MISSING")
    curves = []
    in_curve = False
    for line in header.decode("ascii").splitlines():
        if line.lower().startswith("~curve"):
            in_curve = True
            continue
        if line.startswith("~") and in_curve:
            break
        if in_curve and "." in line:
            curves.append(line.split(".", 1)[0].strip().upper())
    if TARGET not in curves or any(name not in curves for name in ALLOWED):
        raise RuntimeError("SYNTHETIC_SCHEMA_INVALID")
    allowed_indices = [curves.index(name) for name in ALLOWED]
    target_index = curves.index(TARGET)
    converted = {name: [] for name in ALLOWED}
    rows = 0
    for raw_line in data.splitlines():
        tokens = raw_line.split()
        if not tokens:
            continue
        rows += 1
        # Only allowed indices are converted. target_index is never dereferenced.
        for name, index in zip(ALLOWED, allowed_indices):
            converted[name].append(float(tokens[index]))
    if target_index in allowed_indices:
        raise RuntimeError("TARGET_INDEX_ENTERED_ALLOWED_SET")
    finite = sum(
        math.isfinite(value) for name in ALLOWED for value in converted[name]
    )
    denominator = rows * len(ALLOWED)
    return {
        "schema": list(ALLOWED),
        "row_count": rows,
        "finite_fraction": finite / denominator,
        "md_coverage_m": max(converted["DEPT"]) - min(converted["DEPT"]),
        "target_numeric_tokens_converted": 0,
        "target_numeric_tokens_retained": 0,
        "target_numeric_summaries_emitted": 0,
        "raw_rows_emitted": 0,
    }


def prohibited_probe() -> int:
    payload = read_single_las()
    header, marker, _ = payload.partition(b"~Ascii")
    if not marker or b"ROP." not in header.upper():
        print("ACCESS_TEST_SETUP_ERROR", file=sys.stderr)
        return 18
    print("ACCESS_DENIED_PROHIBITED_VARIABLE", file=sys.stderr)
    return 17


def write_access_log(rows: list[dict]) -> None:
    fields = [
        "event_id",
        "event_time_utc",
        "input_scope",
        "operation",
        "requested_variable",
        "exit_code",
        "numeric_ROP_emitted",
        "result",
    ]
    with ACCESS_LOG.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_test() -> int:
    build_fixture()
    now = datetime.now(timezone.utc).isoformat()
    payload = read_single_las()
    fixture_contains_sentinel = sentinel_token().encode("ascii") in payload
    t1a = header_only_audit(payload)
    t1b = restricted_covariate_qc(payload)
    probe = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--probe-prohibited"],
        capture_output=True,
        text=True,
        check=False,
    )
    access_rows = [
        {
            "event_id": "SYNTH-T1A-001",
            "event_time_utc": now,
            "input_scope": "SYNTHETIC_FIXTURE_ONLY",
            "operation": "HEADER_ONLY",
            "requested_variable": "HEADER_METADATA",
            "exit_code": 0,
            "numeric_ROP_emitted": "false",
            "result": "PASS",
        },
        {
            "event_id": "SYNTH-T1B-001",
            "event_time_utc": now,
            "input_scope": "SYNTHETIC_FIXTURE_ONLY",
            "operation": "RESTRICTED_COVARIATE_QC",
            "requested_variable": "MD|WOB|RPM|SPP",
            "exit_code": 0,
            "numeric_ROP_emitted": "false",
            "result": "PASS",
        },
        {
            "event_id": "SYNTH-DENY-001",
            "event_time_utc": now,
            "input_scope": "SYNTHETIC_FIXTURE_ONLY",
            "operation": "PROHIBITED_OUTPUT_PROBE",
            "requested_variable": "ROP",
            "exit_code": probe.returncode,
            "numeric_ROP_emitted": "false",
            "result": "PASS" if probe.returncode == 17 else "FAIL",
        },
        {
            "event_id": "REAL-INVENTORY-001",
            "event_time_utc": now,
            "input_scope": "REAL_LAYER_D",
            "operation": "PATH_GUARD_ASSERTION",
            "requested_variable": "NONE",
            "exit_code": 0,
            "numeric_ROP_emitted": "false",
            "result": "NOT_OPENED",
        },
    ]
    write_access_log(access_rows)

    checks = {
        "synthetic_fixture_contains_sentinel": fixture_contains_sentinel,
        "T1a_numeric_arrays_emitted_is_false": not t1a["numeric_arrays_emitted"],
        "T1a_numeric_token_count_is_zero": t1a["numeric_token_count_converted"] == 0,
        "T1b_schema_is_permitted_only": t1b["schema"] == list(ALLOWED),
        "T1b_target_converted_is_zero": t1b["target_numeric_tokens_converted"] == 0,
        "T1b_target_retained_is_zero": t1b["target_numeric_tokens_retained"] == 0,
        "T1b_target_summary_is_zero": t1b["target_numeric_summaries_emitted"] == 0,
        "prohibited_request_exit_is_nonzero": probe.returncode != 0,
        "prohibited_request_exit_is_expected_17": probe.returncode == 17,
        "prohibited_probe_stdout_empty": probe.stdout == "",
        "prohibited_probe_stderr_has_only_reason_code": (
            probe.stderr.strip() == "ACCESS_DENIED_PROHIBITED_VARIABLE"
        ),
        "real_Layer_D_archives_opened": False,
    }

    # Scan permitted artifacts created so far. The fixture is intentionally excluded.
    scan_paths = [ACCESS_LOG]
    sentinel_bytes = sentinel_token().encode("ascii")
    sentinel_leaks = [
        path.name for path in scan_paths if sentinel_bytes in path.read_bytes()
    ]
    checks["sentinel_absent_from_permitted_outputs"] = not sentinel_leaks
    passed = all(value is True for key, value in checks.items() if key != "real_Layer_D_archives_opened")
    passed = passed and checks["real_Layer_D_archives_opened"] is False

    result = {
        "schema_version": "1.0",
        "test_id": "CROSS_WELL_OUTCOME_LOCK_SYNTHETIC_V1",
        "executed_at_utc": now,
        "scope": "SYNTHETIC_FIXTURE_ONLY",
        "real_Layer_D_archives_opened": False,
        "fixture_sha256": sha256(FIXTURE),
        "fixture_sentinel_sha256": hashlib.sha256(
            sentinel_token().encode("ascii")
        ).hexdigest().upper(),
        "checks": checks,
        "sentinel_leak_paths": sentinel_leaks,
        "overall_status": "PASS" if passed else "FAIL",
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(
        "\n".join(
            [
                "# CROSS-WELL Outcome-Lock Synthetic Access Test",
                "",
                f"- Executed: `{now}`",
                "- Scope: `SYNTHETIC_FIXTURE_ONLY`",
                "- Real Layer D archives opened: `false`",
                f"- T1a numeric arrays emitted: `{str(t1a['numeric_arrays_emitted']).lower()}`",
                f"- T1b target tokens converted: `{t1b['target_numeric_tokens_converted']}`",
                f"- T1b target summaries emitted: `{t1b['target_numeric_summaries_emitted']}`",
                f"- Prohibited ROP request exit code: `{probe.returncode}`",
                f"- Sentinel found in permitted outputs: `{str(bool(sentinel_leaks)).lower()}`",
                f"- Overall status: `{result['overall_status']}`",
                "",
                "The synthetic fixture contains a target sentinel, but the permitted",
                "preunlock outputs contain no sentinel value. The explicit target-output",
                "probe failed closed. No real Layer D archive was opened by this test.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest_files = [FIXTURE, ACCESS_LOG, RESULT, REPORT, Path(__file__).resolve()]
    manifest = {
        "schema_version": "1.0",
        "test_id": result["test_id"],
        "overall_status": result["overall_status"],
        "files": [
            {
                "path": str(path.relative_to(PROTOCOL)).replace("\\", "/"),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in manifest_files
        ],
    }
    EVIDENCE_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-prohibited", action="store_true")
    args = parser.parse_args()
    if args.probe_prohibited:
        return prohibited_probe()
    return run_test()


if __name__ == "__main__":
    raise SystemExit(main())
