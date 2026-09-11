"""Project preflight; report the authorized next action without moving active files."""
import argparse
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap
from werewolf_sft.io import ROOT, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--needed-gib", type=float, default=1.0)
    parser.add_argument("--reserve-gib", type=float, default=5.0)
    args = parser.parse_args()
    if any(not math.isfinite(v) or v < 0 for v in (args.needed_gib, args.reserve_gib)):
        raise ValueError("space requirements must be finite and nonnegative")
    current_drive = ROOT.anchor
    current = shutil.disk_usage(current_drive)
    destination = shutil.disk_usage("D:/")
    required = args.needed_gib + args.reserve_gib
    decision = "CONTINUE"
    project_bytes = None
    if current.free / 2**30 < required:
        if current_drive.lower().startswith("d:"):
            decision = "NOTIFY_RENT_CLOUD_SERVER"
        else:
            project_bytes = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file() and not p.is_symlink())
            decision = ("CHECKPOINT_THEN_MIGRATE_TO_D" if destination.free > project_bytes + required * 2**30
                        else "NOTIFY_RENT_CLOUD_SERVER")
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "workspace_drive": current_drive, "current_free_gib": current.free / 2**30,
              "d_free_gib": destination.free / 2**30, "needed_gib": args.needed_gib,
              "reserve_gib": args.reserve_gib, "project_bytes_if_measured": project_bytes,
              "decision": decision, "migration_target": "D:/Projects/Werewolf-AI",
              "instructions": "docs/disk_recovery.md"}
    write_json(ROOT / "reports/disk_status.json", report)
    print(json.dumps(report, ensure_ascii=False))
    if decision != "CONTINUE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
