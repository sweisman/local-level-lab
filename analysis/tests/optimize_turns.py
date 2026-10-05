# SPDX-License-Identifier: AGPL-3.0-or-later
"""Development-only, paired search for same-side-up IMU turn schedules."""
import argparse
import json
import math
from pathlib import Path

from research import flight_run
from lll import models
from lll.research_design import realize, seed_range, validate_turn_schedule, implementation_hash, DESIGN_VERSION
from lll.inference_policy import INFERENCE_POLICY, digest


def search(*, seeds, scenarios, max_turns=6, grid_min=5., min_spacing=10.,
           edge_margin=5., beam_width=1, pilot_seconds=None, estimate_only=False):
    seeds = list(seeds)
    if not seeds or not scenarios or max_turns < 0 or max_turns > 6 or beam_width < 1 or grid_min <= 0:
        raise ValueError("invalid optimizer inputs")
    designs = {(seed, scenario): realize(seed, scenario, turn_schedule=[])
               for seed in seeds for scenario in scenarios}
    shortest = min(sum(leg[1] for leg in d["simulator"]["legs"]) for d in designs.values())
    validate_turn_schedule([], shortest, min_spacing, edge_margin)
    grid = [i*grid_min for i in range(1, math.ceil(shortest/grid_min))
            if edge_margin <= i*grid_min <= shortest-edge_margin]
    upper = (1+max_turns*max(1, beam_width)*len(grid))*len(designs)*len(models.MODELS)
    if estimate_only:
        return {"upper_bound_fits": upper, "pilot_seconds_per_fit": pilot_seconds,
                "estimated_seconds_upper": upper*pilot_seconds if pilot_seconds is not None else None}
    cache = {}
    def evaluate(schedule):
        key = tuple(schedule)
        if key in cache: return cache[key]
        info, smallest, details = [], [], []
        for (seed, scenario), base in designs.items():
            duration = sum(leg[1] for leg in base["simulator"]["legs"])
            turns = validate_turn_schedule(schedule, duration, min_spacing, edge_margin)
            design = {**base, "simulator": {**base["simulator"], "index_turns": turns}}
            for truth in models.MODELS:
                row = flight_run(truth, scenario, seed, "moving", 15, 0, "spp", design=design,
                                 fit_options={"research_candidate": True, "crab_model": "dynamic",
                                              "noise_model": "axis_segment", "bias_model": "dynamic", "design_only": True})
                report = row.get("identifiability") or {}
                contrasts = report.get("model_contrast_information") or {}
                converged = row.get("convergence", {}).get("converged", False)
                score = min((v["information"] for v in contrasts.values()), default=0.) if converged else 0.
                info.append(score)
                smallest.append(min(report.get("normalized_singular_values", [0.])) if converged else 0.)
                details.append({"seed": seed, "scenario": scenario, "truth": truth,
                                "information": score, "rank": report.get("estimable_rank"),
                                "singular_values": report.get("singular_values"),
                                "condition_number": report.get("condition_number"),
                                "model_contrast_information": contrasts,
                                "expected_k_sd_without_priors": report.get("expected_k_sd_without_priors"),
                                "k_sd": row.get("k_sd"), "elapsed_s": row.get("elapsed_s"),
                                "failure": row.get("failure")})
        result = {"turn_schedule_min": list(schedule), "worst_contrast_information": min(info),
                  "worst_normalized_singular_value": min(smallest), "flights": details}
        cache[key] = result
        return result
    best = evaluate(())
    frontier = [best]
    def score(result):
        return result["worst_contrast_information"], result["worst_normalized_singular_value"]
    beam = [()]
    for _ in range(max_turns):
        candidates = {tuple(sorted((*schedule, t))) for schedule in beam for t in grid if t not in schedule}
        feasible = [s for s in candidates if all(
            not _invalid_schedule(s, sum(leg[1] for leg in d["simulator"]["legs"]), min_spacing, edge_margin)
            for d in designs.values())]
        if not feasible: break
        ranked = sorted((evaluate(s) for s in feasible),
                        key=lambda r: (-r["worst_contrast_information"], -r["worst_normalized_singular_value"], r["turn_schedule_min"]))
        beam = [tuple(r["turn_schedule_min"]) for r in ranked[:beam_width]]
        frontier.append(ranked[0])
        if score(ranked[0]) > score(best):
            best = ranked[0]
    return {"best": best, "frontier_by_turn_count": frontier,
            "schedule_scores": [{k: v for k, v in result.items() if k != "flights"} for result in cache.values()],
            "design_version": DESIGN_VERSION, "implementation_hash": implementation_hash(),
            "inference_policy_hash": digest(INFERENCE_POLICY),
            "search_method": "deterministic beam search; no global-optimum guarantee",
            "evaluated_schedules": len(cache), "upper_bound_fits": upper,
            "scenarios": list(scenarios), "seeds": seeds, "settings": {"max_turns": max_turns,
            "grid_min": grid_min, "min_spacing_min": min_spacing, "edge_margin_min": edge_margin,
            "beam_width": beam_width}}


def _invalid_schedule(schedule, duration, spacing, margin):
    try: validate_turn_schedule(schedule, duration, spacing, margin)
    except ValueError: return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--routes", type=int, default=2)
    ap.add_argument("--scenarios", nargs="+", default=["bias_mixed", "wind"])
    ap.add_argument("--max-turns", type=int, default=6)
    ap.add_argument("--grid-min", type=float, default=5.)
    ap.add_argument("--min-spacing", type=float, default=10.)
    ap.add_argument("--edge-margin", type=float, default=5.)
    ap.add_argument("--beam-width", type=int, default=1)
    ap.add_argument("--pilot-seconds", type=float)
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("-o", type=Path, required=True)
    args = ap.parse_args()
    result = search(seeds=seed_range("development", args.seed, args.routes), scenarios=args.scenarios,
                    max_turns=args.max_turns, grid_min=args.grid_min, min_spacing=args.min_spacing,
                    edge_margin=args.edge_margin, beam_width=args.beam_width,
                    pilot_seconds=args.pilot_seconds, estimate_only=args.estimate_only)
    args.o.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__": main()
