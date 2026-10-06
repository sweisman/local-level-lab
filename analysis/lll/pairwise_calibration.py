# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate empirical calibration for experimental flight or pooled pairwise decisions."""
import argparse
import json
from pathlib import Path

import numpy as np

from . import __version__
from .inference_policy import digest
from .pairwise import pair_stratum, check_pairwise_policy, POOL_METHOD, PROFILE_POOL_METHOD
from .policy import MODEL_PAIRS, eligibility_policies, scientific_exclusions
from .research_calibration import (diagnostic_stratum, validate_records, calibration_precision,
                                   preregistered_groups, required_accepted_n, tail_upper)
from .runtime import numerical_environment, numerical_environment_hash


def group(row, comparison, mode):
    entry=(row.get('pairwise') or {}).get(comparison,{})
    diagnostic_row={**row,'model_test_rank':1} if entry.get('method')=='pair-line-profile-1' else row
    return json.dumps([diagnostic_stratum(diagnostic_row), comparison,
                       row["pairwise"][comparison].get("n_units") if mode == "pool" else None], separators=(",", ":"))


def eligible(row, comparison, mode):
    entry = (row.get("pairwise") or {}).get(comparison) or {}
    if not entry.get("eligible") or entry.get("exclusions") or not entry.get("statistics"):
        return False
    if mode == "pool":
        return row.get("pairwise_mode") == "pool" and entry.get("method") in (POOL_METHOD,PROFILE_POOL_METHOD) and entry.get("n_units", 0) >= 3
    return not scientific_exclusions({"fit": row, "flags": row.get("flags", [])}, comparison)


def calibrate(campaign, mode="flight", alpha=.0027, min_accepted=None):
    if mode not in ("flight", "pool") or campaign.get("partition") != "calibration" or not campaign.get("manifest_hash"):
        raise ValueError("pairwise calibration requires a frozen calibration campaign and a known mode")
    validate_records(campaign, "calibration")
    config = campaign.get("config", {})
    frozen_alpha = config.get("campaign_plan", {}).get("alpha")
    if frozen_alpha is not None and alpha != frozen_alpha: raise ValueError("pairwise alpha differs from the frozen campaign")
    precision = calibration_precision(config, alpha)
    if min_accepted is not None and min_accepted < precision["minimum_accepted"]:
        raise ValueError("pairwise calibration minimum is below frozen tail precision")
    minimum = min_accepted or precision["minimum_accepted"]
    samples, cells = {}, {}
    declared = preregistered_groups(config) if mode == "flight" else None
    if declared and config.get('pairwise_method')=='profile':
        declared={json.dumps([*json.loads(key)[:-1],1],separators=(',',':')):value for key,value in declared.items()}
    if declared:
        for diagnostic in declared:
            for name, endpoints in MODEL_PAIRS.items():
                key = json.dumps([diagnostic, name, None], separators=(",", ":"))
                samples[key] = {model: [] for model in endpoints}
    if mode == "pool" and config.get("preregistered_pairwise_groups"):
        for key in config["preregistered_pairwise_groups"]:
            name = json.loads(key)[1]
            samples[key] = {model: [] for model in MODEL_PAIRS[name]}
        declared = True
    for row in campaign["records"]:
        for name, endpoints in MODEL_PAIRS.items():
            if name not in (row.get("pairwise") or {}): continue
            key = group(row, name, mode)
            if declared and key not in samples: continue
            samples.setdefault(key, {model: [] for model in endpoints})
            cells[key] = (pair_stratum(row, name, mode), name)
            if row["truth"] in endpoints and eligible(row, name, mode):
                value = row["pairwise"][name]["statistics"][row["truth"]]
                if not np.isfinite(value) or value < 0: raise ValueError("invalid pairwise calibration statistic")
                samples[key][row["truth"]].append(value)
    if not samples: raise ValueError("no pairwise calibration samples")
    thresholds, diagnostics, counts, diagnostic_cells = {}, {}, {}, {}
    for key, values in samples.items():
        if any(len(v) < minimum for v in values.values()): raise ValueError("insufficient accepted pairwise calibration flights or pools")
        cell, name = cells[key]
        threshold = thresholds.setdefault(cell, {}).setdefault(name, {})
        diagnostics[key] = {model: float(np.quantile(v, 1-precision["calibration_alpha"], method="higher")) for model, v in values.items()}
        for model, value in diagnostics[key].items(): threshold[model] = max(threshold.get(model, 0.), value)
        counts[key] = {model: len(v) for model, v in values.items()}
        diagnostic_cells[key] = {"cell": cell, "comparison": name}
    methods = sorted({entry.get('method','observable-coordinate-1') for row in campaign['records']
                      for entry in (row.get('pairwise') or {}).values()})
    content = {"version": "pairwise-empirical-2" if set(methods)&{'pair-line-profile-1',PROFILE_POOL_METHOD} else 'pairwise-empirical-1', "mode": mode, "alpha": alpha,
               'statistic_methods':methods,
               "calibration_alpha": precision["calibration_alpha"],
               "analysis_version": __version__, "implementation_hash": campaign.get("implementation_hash"),
               "source_manifest_hash": campaign["manifest_hash"], "source_campaign_hash": digest(campaign),
               "eligibility_policies": eligibility_policies(), "numerical_environment": numerical_environment(),
               "numerical_environment_hash": numerical_environment_hash(), "thresholds": thresholds,
               "diagnostic_thresholds": diagnostics, "diagnostic_cells": diagnostic_cells, "accepted": counts,
               "family_size": 2*len(diagnostics), "calibration_precision": precision,
               "minimum_accepted_calibration": minimum, "validated_for_primary_claims": False}
    content["calibrated_domain"] = {"geometry_mode": config.get("geometry"), "geometry_cells": config.get("geometry_domain"),
                                    "scenarios": config.get("preregistered_scenarios"), "pool_units": config.get("preregistered_pool_units")}
    return {**content, "policy_hash": digest(content)}


def assess(campaign, policy):
    mode = policy.get("mode")
    check_pairwise_policy(policy, mode)
    if campaign.get("partition") != "validation" or not campaign.get("manifest_hash"):
        raise ValueError("pairwise assessment requires a frozen independent validation campaign")
    validate_records(campaign, "validation")
    config = campaign.get("config", {})
    if config.get("pairwise_decision_policy_hash") != policy["policy_hash"]:
        raise ValueError("validation did not preregister this pairwise decision policy")
    if campaign.get("implementation_hash") != policy.get("implementation_hash"):
        raise ValueError("pairwise implementation changed after calibration")
    groups = {(key, model): [] for key, values in policy["diagnostic_thresholds"].items() for model in values}
    family = max(len(groups), config.get("campaign_plan", {}).get("validation_family_size", len(groups)))
    confidence = config.get("tail_confidence", .95)
    required = config.get("tail_min_accepted", 0)
    if required < required_accepted_n(policy["alpha"], family, confidence, config.get("allowed_failures", 0)):
        raise ValueError("pairwise accepted-sample minimum is below the exact validation requirement")
    for row in campaign["records"]:
        for name, endpoints in MODEL_PAIRS.items():
            if row["truth"] not in endpoints or name not in (row.get("pairwise") or {}): continue
            entry = row["pairwise"][name]
            if eligible(row, name, mode):
                key = (group(row, name, mode), row["truth"])
                if key not in groups: raise ValueError("uncalibrated pairwise diagnostic stratum")
                if entry.get("decision_policy_hash") != policy["policy_hash"]:
                    raise ValueError("pairwise validation did not apply the frozen rule")
                rejected = entry.get("rejected_by_model", {}).get(row["truth"])
                if rejected is None: raise ValueError("eligible pairwise validation entry has no endpoint decision")
                groups[key].append(bool(rejected))
    results = []
    for (key, model), values in groups.items():
        n, k = len(values), sum(values)
        upper = tail_upper(n, k, family, confidence)
        results.append({"stratum": key, "truth": model, "accepted": n, "rejections": k,
                        "simultaneous_upper": upper, "status": "inconclusive" if n < required else
                        "pass" if upper <= policy["alpha"] else "not_validated"})
    return {"mode": mode, "policy_hash": policy["policy_hash"], "family_size": family, "results": results,
            "validated": bool(results) and all(r["status"] == "pass" for r in results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["calibrate", "assess"])
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--mode", choices=["flight", "pool"], default="flight")
    parser.add_argument("--policy", type=Path)
    parser.add_argument("-o", type=Path, required=True)
    args = parser.parse_args()
    campaign = json.loads(args.campaign.read_text())
    if args.action == "assess" and not args.policy: parser.error("assessment requires --policy")
    output = calibrate(campaign, args.mode) if args.action == "calibrate" else assess(campaign, json.loads(args.policy.read_text()))
    args.o.write_text(json.dumps(output, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__": main()
