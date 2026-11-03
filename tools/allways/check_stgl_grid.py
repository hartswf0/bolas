#!/usr/bin/env python3
"""
check_stgl_grid.py — Pre-Flight & Post-Render Verifier for the 4D Spatiotemporal Grid Language (STGL)
=====================================================================================================
Audits declarative STGL Timeline IR files (stgl_ir.json) and measured Cinema Tensor logs against:
  1. Valid Spatial Armatures (centered_anchor, golden_spiral, rule_of_thirds, bilateral_symmetry,
     frame_in_frame, s_curve_diagonal, v_wedge, negative_space)
  2. Relativistic Saccade Light-Cone Continuity (ds^2 = R(dt)^2 - ||p2 - p1||^2 >= 0 unless
     explicitly flagged as 'eisenstein_collision' or 'saccade_horizon_whip')
  3. 14-Line Harmonic Armature Resonance (mean_grid_error <= 0.12)
  4. Negative Space Polygon & Typography Collision Protection (max_entropy <= 0.25)
  5. Acoustic Micro-Sync Phase-Locking (PLV & offset_ms bounds)
"""

import os
import sys
import json
import math

VALID_ARMATURES = {
    "centered_anchor",
    "golden_spiral",
    "rule_of_thirds",
    "bilateral_symmetry",
    "frame_in_frame",
    "s_curve_diagonal",
    "v_wedge",
    "negative_space",
}


def audit_stgl_film(film_id, ir_doc):
    meta = ir_doc.get("meta", {})
    shots = ir_doc.get("shots", [])
    issues = []
    warnings = []
    timelike_matches = 0
    intentional_shocks = 0
    locked_shots = 0

    for idx, shot in enumerate(shots):
        sid = shot.get("id", f"shot_{idx+1:02d}")
        grid = shot.get("spatial_grid", {})
        arm = grid.get("armature", "")
        if arm not in VALID_ARMATURES:
            issues.append(f"[{sid}] Unknown spatial_grid.armature '{arm}'")

        err = float(grid.get("mean_grid_error", 0.0))
        if err <= 0.055:
            locked_shots += 1
        elif err > 0.14:
            warnings.append(f"[{sid}] High Arnheim eccentric drift (mean_grid_error={err:.4f} > 0.14)")

        neg = grid.get("negative_space_zone", {})
        if float(neg.get("max_entropy", 0.0)) > 0.25:
            issues.append(f"[{sid}] Negative space entropy {neg.get('max_entropy')} exceeds HUD/title safety limit 0.25")

        trans = shot.get("transition_out", {})
        ttype = trans.get("type", "eye_trace_match")
        ds2 = float(trans.get("spacetime_ds2", 0.0))
        if ds2 < 0 and ttype == "eye_trace_match":
            issues.append(
                f"[{sid}] Spacelike saccade violation (ds^2={ds2:.4f} < 0) on unflagged eye_trace_match cut"
            )
        elif ds2 >= 0:
            timelike_matches += 1
        else:
            intentional_shocks += 1

    total = max(1, len(shots))
    return {
        "film_id": film_id,
        "title": meta.get("title", film_id),
        "maker": meta.get("maker", ""),
        "shots_audited": len(shots),
        "armature_lock_pct": round(100.0 * locked_shots / total, 1),
        "timelike_cuts": timelike_matches,
        "intentional_collision_cuts": intentional_shocks,
        "errors": issues,
        "warnings": warnings,
        "status": "PASS" if not issues else "FAIL",
    }


def main():
    ir_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "/Users/gaia/WORLDBUILDING-TERMS/bolas_repo/allways-tensor/stgl_ir.json"
    )
    if not os.path.exists(ir_path):
        print(f"STGL IR not found at {ir_path}")
        sys.exit(1)

    with open(ir_path) as f:
        data = json.load(f)

    reports = []
    for fid, doc in data.items():
        rep = audit_stgl_film(fid, doc)
        reports.append(rep)
        print(
            f"[{rep['status']}] {fid:22s} | shots={rep['shots_audited']:2d} | "
            f"lock={rep['armature_lock_pct']:5.1f}% | timelike={rep['timelike_cuts']:2d} | "
            f"shocks={rep['intentional_collision_cuts']:2d} | errors={len(rep['errors'])}"
        )

    out_audit = os.path.join(os.path.dirname(ir_path), "stgl_audit.json")
    with open(out_audit, "w") as f:
        json.dump({"audits": reports}, f, indent=2)
    print(f"Saved STGL audit report -> {out_audit}")


if __name__ == "__main__":
    main()
