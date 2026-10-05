# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned scientific eligibility; provenance is supplied separately by the curator."""
from datetime import datetime
import json
import re

import numpy as np

from . import models
from .inference_policy import digest

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
MODEL_CONTRASTS = tuple(f"{a}_vs_{b}" for i, a in enumerate(models.EXPECTED_K)
                        for b in list(models.EXPECTED_K)[i+1:])
MODEL_PAIRS = {name: tuple(name.split("_vs_")) for name in MODEL_CONTRASTS}
CANDIDATE_POLICY = {
    "version": "candidate-eligibility-2",
    "contrasts": MODEL_CONTRASTS,
    "retention_threshold": float(np.sqrt(1 - .95**2)),
    "minimum_model_test_rank": 1,
    "rank_stability_requirement": "optional preregistered relative singular-value margin; zero disables",
    "identifiability_source": "design_identifiability",
    "design_assumptions": {"version": "model-anchor-design-1", "anchors": list(models.EXPECTED_K),
                           "sigma_bin_dph": 3.0, "nuisance_state": "zero angle; unpenalized nuisance tangent at each model anchor"},
    "pairwise_eligibility": "same scientific gates with only the requested design contrast required",
    "require_bootstrap_valid_when_requested": True,
    "exclusions": {k: v for k, v in PRIMARY_EXCLUSIONS.items() if k != "k_not_identified"},
}


def eligibility_provenance(candidate=False):
    policy = CANDIDATE_POLICY if candidate else {"version": POLICY_VERSION, "exclusions": PRIMARY_EXCLUSIONS}
    return {"version": policy["version"], "policy_hash": digest(policy)}


def eligibility_policies():
    return {"legacy": eligibility_provenance(), "candidate": eligibility_provenance(True)}


def is_candidate(fit):
    return (fit.get("inference_policy", {}).get("settings", {}).get("engine") == "candidate-1"
            or fit.get("delta_chi2_identifiable") is not None or "model_test_rank" in fit)


def candidate_settings(settings):
    return bool(settings.get("design_only") or settings.get("research_candidate")
                or settings.get("crab_model", "constant") != "constant"
                or settings.get("noise_model", "global") != "global"
                or settings.get("bootstrap_refit", "linearized") != "linearized"
                or settings.get("forward_uncertainty") or settings.get("bias_model", "constant") == "dynamic"
                or settings.get("rank_min_relative_margin", 0.) > 0)


def contrast_eligibility(report, comparison=None):
    """Shared design criterion; a malformed report cannot certify a flight."""
    contrasts = report.get("model_contrast_information") or {}
    threshold = CANDIDATE_POLICY["retention_threshold"]
    valid = report.get("rank_threshold") == threshold
    names = MODEL_CONTRASTS if comparison is None else (comparison,)
    if comparison is not None and comparison not in MODEL_PAIRS:
        raise ValueError("unknown model comparison")
    margins, information = {}, {}
    for name in names:
        value = contrasts.get(name) or {}
        retention, info = value.get("retained_fraction"), value.get("information")
        if (not isinstance(retention, (int, float)) or not np.isfinite(retention) or retention < 0
                or not isinstance(info, (int, float)) or not np.isfinite(info) or info < 0
                or not isinstance(value.get("estimable"), bool)):
            valid = False
            continue
        margins[name], information[name] = float(retention-threshold), float(info)
    complete = valid and len(margins) == len(names)
    estimable = complete and all(contrasts[name].get("estimable") is True and margins[name] >= 0
                                 for name in names)
    return {"valid": bool(complete), "all_estimable": bool(estimable),
            "worst_margin": min(margins.values()) if complete else None,
            "worst_information": min(information.values()) if complete else None,
            "limiting_contrast": min(margins, key=margins.get) if complete else None}


def scientific_exclusions(result, comparison=None):
    """One scientific policy for session analysis, research and empirical campaigns."""
    fit = result.get("fit")
    if not fit:
        return ["no in-flight fit"]
    candidate = is_candidate(fit)
    policy = CANDIDATE_POLICY["exclusions"] if candidate else PRIMARY_EXCLUSIONS
    reasons = []
    if not fit.get("convergence", {}).get("converged", False):
        reasons.append("inference did not converge")
    if not candidate and fit.get("eligibility_policy") is not None and fit["eligibility_policy"] != eligibility_provenance():
        reasons.append("eligibility policy mismatch; reprocess")
    reasons.extend(policy[f] for f in sorted(set(result.get("flags", [])) & policy.keys()))
    if candidate:
        if fit.get("eligibility_policy") != eligibility_provenance(True):
            reasons.append("candidate eligibility policy mismatch; reprocess")
        design = fit.get("design_identifiability") or {}
        if design.get("assumptions") != CANDIDATE_POLICY["design_assumptions"]:
            reasons.append("design identifiability assumptions mismatch")
        if not design_eligibility(design, comparison)["all_estimable"]:
            reasons.append("model contrast not identified")
        if (fit.get("model_test_rank") or 0) < CANDIDATE_POLICY["minimum_model_test_rank"]:
            reasons.append("no identifiable model-test subspace")
        settings = fit.get("inference_policy", {}).get("settings", {})
        required_margin = settings.get("rank_min_relative_margin", 0.)
        information = fit.get("identifiability") or {}
        margin, cutoff = information.get("rank_boundary_margin"), information.get("rank_threshold")
        if required_margin > 0 and (margin is None or not cutoff or margin/cutoff < required_margin):
            reasons.append("unstable model-test rank")
        requested = settings.get("n_boot", fit.get("bootstrap", {}).get("requested"))
        if requested is None or (requested > 0 and fit.get("bootstrap", {}).get("bootstrap_valid") is not True):
            reasons.append("inadequate bootstrap convergence")
    if fit.get("decision_unavailable_stratum") and comparison is None:
        reasons.append("uncalibrated model-test rank")
    return list(dict.fromkeys(reasons))


def research_eligible(row):
    """External gate exclusions plus the same scientific inputs used by analysis."""
    return not row.get("failure") and not row.get("exclusions") and not scientific_exclusions(
        {"fit": row, "flags": row.get("flags", [])})


def decision_stratum(row):
    return json.dumps([row.get("candidate_id"), row.get("variant"), row.get("model_test_rank")], separators=(",", ":"))


def design_eligibility(report, comparison=None):
    criterion = contrast_eligibility(report, comparison)
    if report.get("assumptions") != CANDIDATE_POLICY["design_assumptions"]:
        criterion.update(valid=False, all_estimable=False, worst_margin=None, worst_information=None, limiting_contrast=None)
    return criterion
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
