# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline empirical thresholds and independent tail assessment. Never production policy."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta

from . import models
from .inference_policy import digest
from .research_design import seed_range


def diagnostic_stratum(row):
    return json.dumps([row["scenario"], row.get("candidate_id"), row.get("geometry"), row.get("variant")], separators=(",", ":"))


def decision_stratum(row):
    return json.dumps([row.get("candidate_id"), row.get("variant")], separators=(",", ":"))


stratum = decision_stratum


def statistic(row):
    value = row.get("delta_chi2_identifiable")
    return value if value is not None else row.get("delta_chi2_raw")


def eligible(row):
    rank = row.get("model_test_rank")
    return (not row.get("exclusions") and (rank is None or rank > 0)
            and row.get("convergence", {}).get("converged", True)
            and row.get("bootstrap", {}).get("bootstrap_valid", True))


def tail_upper(n, failures, family_size, confidence=.95):
    return 1. if failures == n else float(beta.ppf(1-(1-confidence)/family_size, failures+1, n-failures))


def required_accepted_n(alpha, family_size, confidence=.95, allowed_failures=0):
    if (not (0 < alpha < 1 and 0 < confidence < 1) or not isinstance(family_size, (int, np.integer)) or family_size < 1
            or not isinstance(allowed_failures, (int, np.integer)) or allowed_failures < 0):
        raise ValueError("invalid tail-campaign sizing inputs")
    def enough(n):
        return tail_upper(n, allowed_failures, family_size, confidence) <= alpha
    low, high = allowed_failures, max(allowed_failures+1, 2)
    while not enough(high):
        high *= 2
    while low+1 < high:
        mid = (low+high)//2
        if enough(mid): high = mid
        else: low = mid
    return high


def validate_records(campaign, partition):
    """Repeated seeds cannot increase the effective evidence count."""
    seen = set()
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != partition:
            raise ValueError("replays and other partitions are not independent evidence")
        seed_range(partition, row["seed"])
        key = (diagnostic_stratum(row), row["truth"], row["seed"])
        if key in seen: raise ValueError("duplicate simulation in evidence")
        seen.add(key)


def calibrate(campaign, *, min_accepted=None, alpha=.0027):
    if campaign.get("partition") != "calibration" or not campaign.get("manifest_hash"):
        raise ValueError("threshold selection requires a frozen calibration campaign")
    if (min_accepted is not None and min_accepted < 1) or not 0 < alpha < 1:
        raise ValueError("invalid calibration precision")
    validate_records(campaign, "calibration")
    config = campaign.get("config", {})
    frozen_alpha = config.get("campaign_plan", {}).get("alpha")
    if frozen_alpha is not None and alpha != frozen_alpha:
        raise ValueError("calibration alpha differs from the frozen campaign")
    groups, statistics = {}, {}
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != "calibration":
            raise ValueError("replays and other partitions are not calibration evidence")
        group = diagnostic_stratum(row)
        groups.setdefault(group, {m: [] for m in models.MODELS})
        values = statistic(row)
        if values is not None:
            cell = decision_stratum(row)
            field = "delta_chi2_identifiable" if row.get("delta_chi2_identifiable") is not None else "delta_chi2_raw"
            if cell in statistics and statistics[cell] != field:
                raise ValueError("mixed decision statistics in an operational cell")
            statistics[cell] = field
        if values is not None and eligible(row):
            if not np.isfinite(values[row["truth"]]):
                raise ValueError("nonfinite calibration statistic")
            groups[group][row["truth"]].append(values[row["truth"]])
    if not groups: raise ValueError("empty calibration campaign")
    expected_scenarios = config.get("preregistered_scenarios")
    if expected_scenarios is not None and set(expected_scenarios) != {r["scenario"] for r in campaign["records"]}:
        raise ValueError("calibration omits a preregistered scenario")
    if config.get("campaign_plan", {}).get("operational_strata", len(statistics)) != len(statistics):
        raise ValueError("calibration omits a preregistered candidate cell")
    preregistered = config.get("tail_min_accepted")
    if min_accepted is not None and preregistered is not None and min_accepted < preregistered:
        raise ValueError("calibration minimum is below the frozen campaign requirement")
    if min_accepted is None:
        min_accepted = preregistered or required_accepted_n(alpha, len(groups)*len(models.MODELS))
    thresholds, diagnostics, counts = {}, {}, {}
    for group, values in groups.items():
        if any(len(v) < min_accepted for v in values.values()):
            raise ValueError(f"insufficient accepted calibration flights for {group}")
        diagnostics[group] = {m: float(np.quantile(v, 1-alpha, method="higher")) for m, v in values.items()}
        sample = next(r for r in campaign["records"] if diagnostic_stratum(r) == group)
        cell = decision_stratum(sample)
        threshold = thresholds.setdefault(cell, {})
        for m in models.MODELS:
            threshold[m] = max(threshold.get(m, 0.), diagnostics[group][m])
        counts[group] = {m: len(v) for m, v in values.items()}
    content = {"version": "empirical-decision-2", "statistics": statistics, "alpha": alpha,
               "source_manifest_hash": campaign["manifest_hash"], "source_campaign_hash": digest(campaign),
               "analysis_version": campaign["analysis_version"], "thresholds": thresholds,
               "diagnostic_thresholds": diagnostics, "accepted": counts,
               "minimum_accepted_calibration": min_accepted,
               "implementation_hash": campaign.get("implementation_hash"),
               "validated_for_primary_claims": False}
    return {**content, "policy_hash": digest(content)}


def check_policy(policy):
    if policy.get("version") != "empirical-decision-2":
        raise ValueError("decision policy requires recalibration with the current operational strata")
    content = {k: v for k, v in policy.items() if k != "policy_hash"}
    if digest(content) != policy.get("policy_hash"):
        raise ValueError("empirical decision policy hash mismatch")


def assess(campaign, policy, *, min_accepted=None):
    check_policy(policy)
    if campaign.get("partition") != "validation" or not campaign.get("manifest_hash"):
        raise ValueError("tail assessment requires a frozen validation campaign")
    validate_records(campaign, "validation")
    config = campaign["config"]
    required = config.get("tail_min_accepted")
    if required is None or required < 1 or (min_accepted is not None and min_accepted != required):
        raise ValueError("minimum accepted sample size must be preregistered in the manifest")
    if config.get("decision_policy_hash") != policy["policy_hash"]:
        raise ValueError("validation did not preregister this decision policy")
    if campaign.get("implementation_hash") != policy.get("implementation_hash"):
        raise ValueError("inference implementation changed after calibration")
    groups = {(group, m): [] for group in policy["diagnostic_thresholds"] for m in models.MODELS}
    confidence = config.get("tail_confidence", .95)
    minimum = required_accepted_n(policy["alpha"], len(groups), confidence, config.get("allowed_failures", 0))
    if required < minimum:
        raise ValueError("preregistered minimum is below the exact tail-campaign requirement")
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != "validation":
            raise ValueError("replays and other partitions are not validation evidence")
        key = (diagnostic_stratum(row), row["truth"])
        if key not in groups: raise ValueError("validation stratum has no calibrated threshold")
        if row.get("rejected") is not None:
            if row.get("decision_policy_hash") != policy["policy_hash"]:
                raise ValueError("complete gate must run with the frozen decision rule")
            if eligible(row):
                groups[key].append(row)
    family_size = len(groups)
    out = []
    for (group, truth), rows in groups.items():
        n = len(rows); k = sum(r["rejected"] for r in rows)
        upper = tail_upper(n, k, family_size, confidence)
        out.append({"stratum": group, "truth": truth, "accepted": n, "rejections": k,
                    "rate": k/n if n else None, "simultaneous_upper": upper, "confidence": confidence,
                    **({"simultaneous_upper95": upper} if confidence == .95 else {}),
                    "status": "inconclusive" if n < required else ("pass" if upper <= policy["alpha"] else "not_validated")})
    return {"decision_policy_hash": policy["policy_hash"], "family_size": family_size,
            "criterion": f"simultaneous one-sided {100*confidence:g}% upper bounds <= alpha", "results": out,
            "validated": bool(out) and all(r["status"] == "pass" for r in out)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["calibrate", "assess"])
    ap.add_argument("campaign", type=Path)
    ap.add_argument("--policy", type=Path)
    ap.add_argument("--min-accepted", type=int)
    ap.add_argument("--alpha", type=float, default=.0027)
    ap.add_argument("-o", type=Path, required=True)
    args = ap.parse_args()
    campaign = json.loads(args.campaign.read_text())
    if args.mode == "calibrate": result = calibrate(campaign, min_accepted=args.min_accepted, alpha=args.alpha)
    else:
        if args.policy is None: ap.error("assess requires --policy")
        result = assess(campaign, json.loads(args.policy.read_text()))
    args.o.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__": main()
