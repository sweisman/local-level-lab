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


def stratum(row):
    return json.dumps([row["scenario"], row.get("candidate_id"), row.get("geometry"), row.get("variant")], separators=(",", ":"))


def validate_records(campaign, partition):
    """Repeated seeds cannot increase the effective evidence count."""
    seen = set()
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != partition:
            raise ValueError("replays and other partitions are not independent evidence")
        seed_range(partition, row["seed"])
        key = (stratum(row), row["truth"], row["seed"])
        if key in seen: raise ValueError("duplicate simulation in evidence")
        seen.add(key)


def calibrate(campaign, *, min_accepted=2000, alpha=.0027):
    if campaign.get("partition") != "calibration" or not campaign.get("manifest_hash"):
        raise ValueError("threshold selection requires a frozen calibration campaign")
    if min_accepted < 1 or not 0 < alpha < 1:
        raise ValueError("invalid calibration precision")
    validate_records(campaign, "calibration")
    groups = {}
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != "calibration":
            raise ValueError("replays and other partitions are not calibration evidence")
        groups.setdefault(stratum(row), {m: [] for m in models.MODELS})
        if "delta_chi2_raw" in row and not row["exclusions"]:
            groups[stratum(row)][row["truth"]].append(row["delta_chi2_raw"][row["truth"]])
    if not groups: raise ValueError("empty calibration campaign")
    thresholds, counts = {}, {}
    for group, values in groups.items():
        if any(len(v) < min_accepted for v in values.values()):
            raise ValueError(f"insufficient accepted calibration flights for {group}")
        thresholds[group] = {m: float(np.quantile(v, 1-alpha, method="higher")) for m, v in values.items()}
        counts[group] = {m: len(v) for m, v in values.items()}
    content = {"version": "empirical-decision-1", "statistic": "delta_chi2_raw", "alpha": alpha,
               "source_manifest_hash": campaign["manifest_hash"], "source_campaign_hash": digest(campaign),
               "analysis_version": campaign["analysis_version"], "thresholds": thresholds, "accepted": counts,
               "implementation_hash": campaign.get("implementation_hash"),
               "validated_for_primary_claims": False}
    return {**content, "policy_hash": digest(content)}


def check_policy(policy):
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
    groups = {(group, m): [] for group in policy["thresholds"] for m in models.MODELS}
    for row in campaign["records"]:
        if row.get("replay") or row.get("partition") != "validation":
            raise ValueError("replays and other partitions are not validation evidence")
        key = (stratum(row), row["truth"])
        if key not in groups: raise ValueError("validation stratum has no calibrated threshold")
        if "rejected" in row:
            if row.get("decision_policy_hash") != policy["policy_hash"]:
                raise ValueError("complete gate must run with the frozen decision rule")
            if not row["exclusions"]: groups[key].append(row)
    family_size = len(groups)
    out = []
    for (group, truth), rows in groups.items():
        n = len(rows); k = sum(r["rejected"] for r in rows)
        upper = 1. if k == n else float(beta.ppf(1-.05/family_size, k+1, n-k))
        out.append({"stratum": group, "truth": truth, "accepted": n, "rejections": k,
                    "rate": k/n if n else None, "simultaneous_upper95": upper,
                    "status": "inconclusive" if n < required else ("pass" if upper <= policy["alpha"] else "not_validated")})
    return {"decision_policy_hash": policy["policy_hash"], "family_size": family_size,
            "criterion": "simultaneous one-sided 95% upper bounds <= alpha", "results": out,
            "validated": bool(out) and all(r["status"] == "pass" for r in out)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["calibrate", "assess"])
    ap.add_argument("campaign", type=Path)
    ap.add_argument("--policy", type=Path)
    ap.add_argument("--min-accepted", type=int, default=2000)
    ap.add_argument("-o", type=Path, required=True)
    args = ap.parse_args()
    campaign = json.loads(args.campaign.read_text())
    if args.mode == "calibrate": result = calibrate(campaign, min_accepted=args.min_accepted)
    else:
        if args.policy is None: ap.error("assess requires --policy")
        result = assess(campaign, json.loads(args.policy.read_text()))
    args.o.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__": main()
