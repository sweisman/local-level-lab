# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned scientific eligibility; provenance is supplied separately by the curator."""
from datetime import datetime
import re

import numpy as np

POLICY_VERSION = "pilot-2"
PRIMARY_EXCLUSIONS = {
    "no_cal_pre": "missing a calibration", "no_cal_post": "missing a calibration",
    "k_not_identified": "curvature not identified", "prior_dominated": "prior-dominated",
    "wmm_selection_sensitive": "depends on the WMM slip exclusion",
    "imu_range_inconsistent": "inconsistent gyro range",
    "imu_accel_range_inconsistent": "inconsistent accelerometer range",
    "imu_corrupt_bytes": "significant IMU corruption",
    "imu_changed_mid_session": "mixed instruments",
    "imu_config_unverified": "unverified instrument configuration",
    "orientation_unresolved": "unresolved orientation",
    "imu_turn_gap": "unresolved turn gap",
    "inference_nonconvergence": "inference did not converge",
    "gnss_invalid_data": "conflicting GNSS fixes",
    "recording_data_loss": "recording data loss",
    "no_heading_reference_vertical_only": "no independent forward axis",
    "single_heading": "insufficient heading diversity",
}
BENCH_CHECKS = ("decode", "sample_rate", "scale", "autozero", "range", "stability",
                "reversal", "recovery", "temperature")


def verified_config(detail, imu):
    registers = {int(r, 16): int(v, 16) for r, v in re.findall(r"(0x[0-9a-fA-F]+)=(0x[0-9a-fA-F]+)\b", detail)}
    rate_code = {10: 6, 20: 7, 50: 8, 100: 9, 200: 11}.get((imu.get("config") or {}).get("rate_hz"))
    return ("ok=true" in detail.split() and registers.get(0x63) == 1
            and rate_code is not None and registers.get(3) == rate_code
            and registers.get(0x20) in (0, 1, 2, 3) and registers.get(0x21) in (0, 1, 2, 3)
            and (imu.get("variant") != "spp" or registers.get(2) == 0x17))


def utc_seconds(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.timestamp() if dt.tzinfo is not None else None
    except (ValueError, TypeError, AttributeError):
        return None


def provenance_reasons(result, approval):
    if not approval or approval.get("status") != "approved" or not approval.get("unit_id"):
        return ["unverified provenance"]
    if approval.get("sha256") != result.get("input_sha256"):
        return ["approval hash mismatch"]
    bench = approval.get("bench") or {}
    when = utc_seconds(result.get("flight_started_utc"))
    approved = utc_seconds(bench.get("approved_at"))
    if (bench.get("unit_id") != approval["unit_id"] or bench.get("tier") not in ("usable", "qualified")
            or not all(bench.get("checks", {}).get(k) is True for k in BENCH_CHECKS)
            or when is None or approved is None or approved >= when):
        return ["no complete bench approval before flight"]
    if not {"rate_hz", "gyro_range_dps", "accel_range_g", "auto_zero"} <= (bench.get("config") or {}).keys():
        return ["incomplete bench configuration"]
    cfg = (result.get("imu") or {}).get("config") or {}
    cfg = dict(cfg)
    decode = (result.get("imu") or {}).get("decode") or {}
    for key, measured in (("gyro_range_dps", "gyro_range_used_dps"), ("accel_range_g", "accel_range_used_g")):
        if measured in decode:
            cfg[key] = decode[measured]
    if any(cfg.get(k) != v for k, v in (bench.get("config") or {}).items()):
        return ["instrument settings differ from bench certificate"]
    return []


def heading_diversity(bins):
    """Ten-degree course groups; two must each retain 600 s and differ by >=30 degrees."""
    refs, duration = [], []
    angles = np.degrees(bins["psi"]) % 360
    order = np.lexsort((np.asarray(bins["dt"]), angles))
    if len(order):
        sorted_angles = angles[order]
        gaps = np.diff(np.r_[sorted_angles, sorted_angles[0] + 360])
        # Ties choose the smallest normalized bearing after the cut.
        cuts = (np.flatnonzero(gaps == gaps.max()) + 1) % len(order)
        cut = min(cuts, key=lambda i: sorted_angles[i])
        order = np.roll(order, -int(cut))
    for j in order:
        angle, dt = angles[j], bins["dt"][j]
        for i, ref in enumerate(refs):
            if abs((angle - ref + 180) % 360 - 180) < 10:
                duration[i] += float(dt)
                break
        else:
            refs.append(float(angle)); duration.append(float(dt))
    good = [a for a, t in zip(refs, duration) if t >= 600]
    adequate = any(abs((a - b + 180) % 360 - 180) >= 30 for i, a in enumerate(good) for b in good[i + 1:])
    return {"adequate": adequate, "provisional": True, "min_separation_deg": 30,
            "min_seconds_per_heading": 600, "groups": [{"heading_deg": a, "seconds": t} for a, t in zip(refs, duration)]}
