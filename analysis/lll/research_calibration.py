# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline empirical thresholds and independent tail assessment. Never production policy."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta, binom

from . import models, __version__
from .inference_policy import digest
from .research_design import seed_range, implementation_hash
from .policy import research_eligible as eligible, eligibility_policies, eligibility_provenance, is_candidate, decision_stratum
from .runtime import numerical_environment, numerical_environment_hash, check_environment


def diagnostic_stratum(row):
    return json.dumps([row["scenario"], row.get("candidate_id"), row.get("geometry"), row.get("geometry_cell"),
                       row.get("variant"), row.get("model_test_rank")], separators=(",", ":"))


stratum = decision_stratum


def statistic(row):
    value = row.get("delta_chi2_identifiable")
    return value if value is not None else row.get("delta_chi2_raw")


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


def required_calibration_n(alpha, tail_observations=30, confidence=.95):
    """Enough draws that the target tail contains >=k observations with preregistered probability."""
    if not 0 < alpha < 1 or not 0 < confidence < 1 or not isinstance(tail_observations, (int, np.integer)) or tail_observations < 1:
        raise ValueError("invalid calibration tail-precision objective")
    low, high = tail_observations-1, max(tail_observations, 2)
    while binom.sf(tail_observations-1, high, alpha) < confidence:
        high *= 2
    while low+1 < high:
        mid = (low+high)//2
        if binom.sf(tail_observations-1, mid, alpha) >= confidence: high = mid
        else: low = mid
    return high


def validation_power_plan(alpha, family_size, design_rate, confidence=.95, power=.90):
    """Conservative failure budget with exact confidence bounds and binomial design power.

    Family power uses a union bound, without assuming independent tests. It assumes the
    specified true rate in every cell and is not validation evidence. Doubling the
    allowed failures finds a sufficient plan without claiming a globally minimal count.
    """
    if not 0 < design_rate < alpha or not 0 < power < 1:
        raise ValueError("validation design rate must be positive and below the claimed rate")
    failures = 0
    while True:
        count = required_accepted_n(alpha, family_size, confidence, failures)
        per_cell_power = float(binom.cdf(failures, count, design_rate))
        achieved = max(0., 1-family_size*(1-per_cell_power))
        if achieved >= power:
            return dict(required_accepted=count, allowed_failures=failures,
                        design_rate=design_rate, desired_power=power, achieved_power=achieved,
                        per_cell_power=per_cell_power, power_method="union bound over the validation family")
        failures = max(1, 2*failures)
        if failures > 1_000_000:
            raise ValueError("validation design rate is too close to the claimed rate for this planner")


def calibration_precision(config, alpha):
    count, confidence = config.get("calibration_tail_observations", 30), config.get("calibration_tail_confidence", .95)
    calibration_alpha = config.get("calibration_alpha")
    if calibration_alpha is None: calibration_alpha = alpha
    if not 0 < calibration_alpha <= alpha:
        raise ValueError("calibration tail target must be positive and no greater than the claimed rate")
    return {"tail_observations": count, "confidence": confidence, "calibration_alpha": calibration_alpha,
            "minimum_accepted": max(required_calibration_n(calibration_alpha, count, confidence), config.get("calibration_min_accepted") or 0)}


def preregistered_groups(config):
    if not config.get("operational_cells"):
        return None
    return {diagnostic_stratum({"scenario": scenario, "candidate_id": candidate, "variant": variant,
                               "model_test_rank": rank, "geometry": config["geometry"], "geometry_cell": geometry_cell}):
            {m: [] for m in models.MODELS}
            for candidate, variant, rank in (json.loads(cell) for cell in config["operational_cells"])
            for scenario in config["preregistered_scenarios"]
            for geometry_cell in config.get("preregistered_geometry_cells", [None])}


def validate_records(campaign, partition):
    """Repeated seeds cannot increase the effective evidence count."""
    seen = set()
    if campaign.get("eligibility_policies") != eligibility_policies():
        raise ValueError("campaign eligibility policy mismatch; regenerate the campaign")
    check_environment(campaign.get("numerical_environment"))
    if campaign.get("numerical_environment_hash", numerical_environment_hash()) != numerical_environment_hash():
        raise ValueError("campaign numerical environment hash mismatch")
    if campaign.get("implementation_hash") is not None and campaign["implementation_hash"] != implementation_hash():
        raise ValueError("campaign implementation changed; regenerate the campaign")
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != partition:
            raise ValueError("replays and other partitions are not independent evidence")
        seed_range(partition, row["seed"])
        check_environment(row.get("numerical_environment"))
        if row.get("numerical_environment_hash", numerical_environment_hash()) != numerical_environment_hash():
            raise ValueError("record numerical environment hash mismatch")
        if not row.get("failure") and row.get("eligibility_policy") != eligibility_provenance(is_candidate(row),
                row.get('inference_policy',{}).get('settings',row.get('fit_options',{}))):
            raise ValueError("record eligibility policy mismatch; regenerate the campaign")
        key = (diagnostic_stratum({**row, "model_test_rank": None}), row["truth"], row["seed"])
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
    groups, statistics = preregistered_groups(config) or {}, {}
    declared = bool(config.get("operational_cells"))
    samples = {}
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != "calibration":
            raise ValueError("replays and other partitions are not calibration evidence")
        group = diagnostic_stratum(row)
        values = statistic(row)
        if declared and group not in groups:
            continue  # Unpreregistered ranks cannot manufacture calibrated operational cells.
        if values is None and not declared:
            continue
        groups.setdefault(group, {m: [] for m in models.MODELS})
        samples.setdefault(group, row)
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
    precision = calibration_precision(config, alpha)
    if min_accepted is not None and min_accepted < precision["minimum_accepted"]:
        raise ValueError("calibration minimum is below the frozen tail-precision requirement")
    min_accepted = min_accepted or precision["minimum_accepted"]
    thresholds, diagnostics, counts = {}, {}, {}
    for group, values in groups.items():
        if any(len(v) < min_accepted for v in values.values()):
            raise ValueError(f"insufficient accepted calibration flights for {group}")
        diagnostics[group] = {m: float(np.quantile(v, 1-precision["calibration_alpha"], method="higher")) for m, v in values.items()}
        sample = samples[group]
        cell = decision_stratum(sample)
        threshold = thresholds.setdefault(cell, {})
        for m in models.MODELS:
            threshold[m] = max(threshold.get(m, 0.), diagnostics[group][m])
        counts[group] = {m: len(v) for m, v in values.items()}
    content = {"version": "empirical-decision-4", "statistics": statistics, "alpha": alpha,
               "calibration_alpha": precision["calibration_alpha"],
               "numerical_environment": numerical_environment(), "numerical_environment_hash": numerical_environment_hash(),
               "stratum_fields": ["candidate_id", "variant", "model_test_rank"],
               "calibrated_domain": {"geometry_mode": config.get("geometry"), "geometry_cells": config.get("geometry_domain"),
                                     "scenarios": config.get("preregistered_scenarios")},
               "eligibility_policies": eligibility_policies(),
               "source_manifest_hash": campaign["manifest_hash"], "source_campaign_hash": digest(campaign),
               "analysis_version": campaign["analysis_version"], "thresholds": thresholds,
               "diagnostic_thresholds": diagnostics, "accepted": counts,
               "minimum_accepted_calibration": min_accepted,
               "calibration_precision": precision,
               "implementation_hash": campaign.get("implementation_hash"),
               "validated_for_primary_claims": False}
    return {**content, "policy_hash": digest(content)}


def check_policy(policy):
    if policy.get("version") != "empirical-decision-4":
        raise ValueError("decision policy requires recalibration with the current eligibility policy")
    content = {k: v for k, v in policy.items() if k != "policy_hash"}
    if digest(content) != policy.get("policy_hash"):
        raise ValueError("empirical decision policy hash mismatch")
    if policy.get("eligibility_policies") != eligibility_policies():
        raise ValueError("empirical decision eligibility policy mismatch")
    check_environment(policy.get("numerical_environment"))
    if policy.get("numerical_environment_hash") != numerical_environment_hash():
        raise ValueError("empirical decision numerical environment hash mismatch")
    if policy.get("analysis_version") != __version__:
        raise ValueError("empirical decision software version differs")
    if policy.get("implementation_hash") is not None and policy["implementation_hash"] != implementation_hash():
        raise ValueError("empirical decision implementation changed after calibration")


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
    family_size = max(len(groups), config.get("campaign_plan", {}).get("validation_family_size", len(groups)))
    minimum = required_accepted_n(policy["alpha"], family_size, confidence, config.get("allowed_failures", 0))
    if required < minimum:
        raise ValueError("preregistered minimum is below the exact tail-campaign requirement")
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != "validation":
            raise ValueError("replays and other partitions are not validation evidence")
        key = (diagnostic_stratum(row), row["truth"])
        if key not in groups:
            if not eligible(row) or row.get("rejected") is None:
                continue
            raise ValueError("validation stratum has no calibrated threshold")
        if row.get("rejected") is not None:
            if row.get("decision_policy_hash") != policy["policy_hash"]:
                raise ValueError("complete gate must run with the frozen decision rule")
            if eligible(row):
                groups[key].append(row)
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
