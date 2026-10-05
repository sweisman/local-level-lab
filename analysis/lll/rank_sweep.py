# SPDX-License-Identifier: AGPL-3.0-or-later
"""Development-only cutoff sensitivity from recorded singular values; no refits."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from .policy import CANDIDATE_POLICY
from .research_calibration import diagnostic_stratum


def sweep(campaign, cutoffs=None, boundary_relative_width=.1):
    if campaign.get("partition") != "development":
        raise ValueError("rank cutoff tuning requires development evidence")
    baseline = CANDIDATE_POLICY["retention_threshold"]
    cutoffs = list(cutoffs) if cutoffs is not None else [baseline*f for f in (.5, .75, 1., 1.25, 1.5)]
    if not cutoffs or not np.isfinite(cutoffs).all() or min(cutoffs) <= 0 or not np.isfinite(boundary_relative_width) or boundary_relative_width < 0:
        raise ValueError("invalid rank sweep settings")
    groups, flights = {}, []
    for row in campaign["records"]:
        values = (row.get("identifiability") or {}).get("normalized_singular_values")
        if values is None: continue
        values = np.asarray(values, float)
        if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or np.any(values < 0):
            raise ValueError("invalid recorded singular values")
        ranks = [int(np.sum(values >= cutoff)) for cutoff in cutoffs]
        baseline_rank = int(np.sum(values >= baseline))
        margin = float(np.min(np.abs(values-baseline))/baseline)
        flight = {"seed": row["seed"], "truth": row["truth"], "stratum": diagnostic_stratum(row),
                  "baseline_rank": baseline_rank, "ranks": ranks, "rank_flips": any(rank != baseline_rank for rank in ranks),
                  "relative_boundary_margin": margin, "near_boundary": margin <= boundary_relative_width}
        flights.append(flight)
        groups.setdefault(flight["stratum"], []).append(flight)
    summaries = {key: {"flights": len(rows), "baseline_rank_counts": dict(Counter(r["baseline_rank"] for r in rows)),
                       "rank_flip_fraction": sum(r["rank_flips"] for r in rows)/len(rows),
                       "near_boundary_fraction": sum(r["near_boundary"] for r in rows)/len(rows)}
                 for key, rows in groups.items()}
    return {"partition": "development", "source": "recorded free-fit normalized singular values",
            "baseline_cutoff": baseline, "cutoffs": cutoffs, "boundary_relative_width": boundary_relative_width,
            "attempted": len(campaign["records"]), "analyzed": len(flights), "groups": summaries, "flights": flights,
            "note": "Diagnostic only; choose any stability restriction on development evidence and freeze it before calibration."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--cutoffs", nargs="+", type=float)
    parser.add_argument("--boundary-relative-width", type=float, default=.1)
    parser.add_argument("-o", type=Path, required=True)
    args = parser.parse_args()
    args.o.write_text(json.dumps(sweep(json.loads(args.campaign.read_text()), args.cutoffs, args.boundary_relative_width),
                                 indent=2, allow_nan=False)+"\n")


if __name__ == "__main__": main()
