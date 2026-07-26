#!/usr/bin/env python3
"""Frozen launcher that captures console output from the single T3 run."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "registration_external" / "0726_external_unlock_gate_completed_v1.json"
OUTPUT = ROOT / "execution" / "0726_layer_d_frozen_run_v1"


def main() -> int:
    if OUTPUT.exists():
        raise SystemExit(f"Refusing overwrite or rerun: {OUTPUT}")
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_layer_d_confirmatory.py"),
        "--protocol-root", str(ROOT),
        "--unlock-gate", str(GATE),
        "--output-root", str(OUTPUT),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    destination = OUTPUT
    if not destination.exists():
        destination = ROOT / "execution" / "0726_layer_d_frozen_run_v1.failed"
        destination.mkdir(parents=True, exist_ok=False)
    (destination / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (destination / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    (destination / "frozen_command.txt").write_text(
        subprocess.list2cmdline(command) + "\n", encoding="utf-8"
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
