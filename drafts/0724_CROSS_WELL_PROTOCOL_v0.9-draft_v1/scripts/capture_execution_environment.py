#!/usr/bin/env python3
"""Capture the exact pre-freeze execution environment and code identity."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy
import pandas
import scipy
import sklearn
import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "registration" / "0726_execution_environment_lock_v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    code = [
        "scripts/run_layer_d_confirmatory.py",
        "scripts/execute_frozen_run.py",
        "scripts/build_frozen_scoring_source_map.py",
        "scripts/build_private_local_archive_locator.py",
        "scripts/validate_protocol.py",
        "scripts/generate_freeze_manifest.py",
    ]
    payload = {
        "status": "PREUNLOCK_EXECUTION_ENVIRONMENT_LOCKED",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "layer_D_numeric_ROP_accessed": False,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "packages": {
            "numpy": numpy.__version__, "pandas": pandas.__version__,
            "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__, "PyYAML": yaml.__version__,
        },
        "scientific_code_sha256": {path: sha256(ROOT / path) for path in code},
        "frozen_command": "python scripts/execute_frozen_run.py",
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(sha256(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
