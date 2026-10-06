# SPDX-License-Identifier: AGPL-3.0-or-later
"""Development-only, paired search for same-side-up IMU turn schedules."""
import argparse
import json
import math
import numpy as np
from pathlib import Path

from research import flight_run
from lll import models
from lll.research_design import realize, seed_range, validate_turn_schedule, implementation_hash, DESIGN_VERSION
from lll.inference_policy import INFERENCE_POLICY, digest
from lll.policy import design_eligibility, eligibility_provenance
from lll.policy import CANDIDATE_POLICY


def search(*, seeds, scenarios, max_turns=6, grid_min=5., min_spacing=10.,
           edge_margin=5., beam_width=16, crab_models=("dynamic", "wind"),
           pilot_seconds=None, pilot_evaluation_seconds=None, estimate_only=False):
    seeds = list(seeds)
    scenarios, crab_models = list(scenarios), list(dict.fromkeys(crab_models))
    if not seeds or not scenarios or max_turns < 0 or max_turns > 6 or beam_width < 1 or grid_min <= 0:
        raise ValueError("invalid optimizer inputs")
    if not crab_models or any(model not in ("dynamic", "wind") for model in crab_models):
        raise ValueError("optimizer crab models must be dynamic and/or wind")
    if not all(math.isfinite(v) for v in (grid_min, min_spacing, edge_margin)) or (pilot_seconds is not None and (not math.isfinite(pilot_seconds) or pilot_seconds < 0)):
        raise ValueError("invalid optimizer cost or grid settings")
    if pilot_evaluation_seconds is not None and (not math.isfinite(pilot_evaluation_seconds) or pilot_evaluation_seconds < 0):
        raise ValueError("invalid evaluation timing")
    designs = {(seed, scenario): realize(seed, scenario, turn_schedule=[])
               for seed in seeds for scenario in scenarios}
    shortest = min(sum(leg[1] for leg in d["simulator"]["legs"]) for d in designs.values())
    validate_turn_schedule([], shortest, min_spacing, edge_margin)
    grid = [i*grid_min for i in range(1, math.ceil(shortest/grid_min))
            if edge_margin <= i*grid_min <= shortest-edge_margin]
    evaluations = (1+max_turns*beam_width*len(grid))*len(designs)*len(models.MODELS)*len(crab_models)
    upper = 2*evaluations  # Each design-only evaluation performs two free fits.
    if estimate_only:
        return {"upper_bound_fits": upper, "upper_bound_evaluations": evaluations,
                "crab_models": crab_models, "beam_width": beam_width, "pilot_seconds_per_fit": pilot_seconds,
                "upper_bound_anchor_svd_evaluations": evaluations*len(CANDIDATE_POLICY["design_assumptions"]["anchors"]),
                "pilot_seconds_per_evaluation": pilot_evaluation_seconds,
                "cost_basis": "complete design evaluation" if pilot_evaluation_seconds is not None else "free fits only; simulation/SVD overhead excluded",
                "estimated_seconds_upper": evaluations*pilot_evaluation_seconds if pilot_evaluation_seconds is not None else
                                           upper*pilot_seconds if pilot_seconds is not None else None}
    cache = {}
    def evaluate(schedule):
        key = tuple(schedule)
        if key in cache: return cache[key]
        details = []
        for (seed, scenario), base in designs.items():
            duration = sum(leg[1] for leg in base["simulator"]["legs"])
            turns = validate_turn_schedule(schedule, duration, min_spacing, edge_margin)
            design = {**base, "simulator": {**base["simulator"], "index_turns": turns}}
            for truth in models.MODELS:
                for crab_model in crab_models:
                    row = flight_run(truth, scenario, seed, "moving", 15, 0, "spp", design=design,
                                     fit_options={"research_candidate": True, "crab_model": crab_model,
                                                  "noise_model": "axis_segment", "bias_model": "dynamic", "design_only": True})
                    report = row.get("design_identifiability") or {}
                    criterion = design_eligibility(report)
                    rank = report.get("estimable_rank")
                    valid = (criterion["valid"] and isinstance(rank, int) and rank >= 0
                             and not row.get("failure") and row.get("convergence", {}).get("converged", False))
                    details.append(_json_safe({"seed": seed, "scenario": scenario, "truth": truth,
                                    "crab_model": crab_model, "valid": bool(valid),
                                    "all_estimable": bool(valid and criterion["all_estimable"] and (report.get("estimable_rank") or 0) > 0),
                                    "margin": criterion["worst_margin"] if valid else None,
                                    "information": criterion["worst_information"] if valid else None,
                                    "limiting_contrast": criterion["limiting_contrast"], "rank": report.get("estimable_rank"),
                                    "singular_values": report.get("singular_values"),
                                    "condition_number": report.get("condition_number"),
                                    "model_contrast_information": report.get("model_contrast_information"),
                                    "free_fit_identifiability": row.get("identifiability"),
                                    "model_test_rank": row.get("model_test_rank"),
                                    "expected_k_sd_without_priors": report.get("expected_k_sd_without_priors"),
                                    "k_sd": row.get("k_sd"), "elapsed_s": row.get("elapsed_s"),
                                    "failure": row.get("failure")}))
        valid = all(d["valid"] for d in details)
        limiting = min(details, key=lambda d: (d["valid"], d["margin"] if d["margin"] is not None else -math.inf,
                                              d["information"] if d["information"] is not None else -math.inf))
        result = {"turn_schedule_min": list(schedule), "valid_evaluations": valid,
                  "all_estimable": all(d["all_estimable"] for d in details),
                  "worst_estimability_margin": min(d["margin"] for d in details) if valid else None,
                  "worst_contrast_information": min(d["information"] for d in details) if valid else None,
                  "limiting_evaluation": {k: limiting[k] for k in ("seed", "scenario", "truth", "crab_model", "limiting_contrast")},
                  "flights": details}
        cache[key] = result
        return result
    best = evaluate(())
    frontier = [best]
    beam = [()]
    for _ in range(max_turns):
        candidates = {tuple(sorted((*schedule, t))) for schedule in beam for t in grid if t not in schedule}
        feasible = [s for s in sorted(candidates) if all(
            not _invalid_schedule(s, sum(leg[1] for leg in d["simulator"]["legs"]), min_spacing, edge_margin)
            for d in designs.values())]
        if not feasible: break
        ranked = sorted((evaluate(s) for s in feasible),
                        key=_ranking)
        beam = [tuple(r["turn_schedule_min"]) for r in ranked[:beam_width]]
        frontier.append(ranked[0])
        if _ranking(ranked[0]) < _ranking(best):
            best = ranked[0]
    return {"best": best if best["all_estimable"] else None, "best_diagnostic": best,
            "feasible_winner": best["all_estimable"], "frontier_by_turn_count": frontier,
            "schedule_scores": [{k: v for k, v in result.items() if k != "flights"} for result in cache.values()],
            "design_version": DESIGN_VERSION, "implementation_hash": implementation_hash(),
            "inference_policy_hash": digest(INFERENCE_POLICY),
            "eligibility_policy": eligibility_provenance(True), "crab_models": crab_models,
            "score_order": ["all_estimable", "worst_estimability_margin", "worst_contrast_information"],
            "search_method": "deterministic beam search; no global-optimum guarantee",
            "evaluated_schedules": len(cache), "upper_bound_fits": upper, "upper_bound_evaluations": evaluations,
            "scenarios": list(scenarios), "seeds": seeds, "settings": {"max_turns": max_turns,
            "grid_min": grid_min, "min_spacing_min": min_spacing, "edge_margin_min": edge_margin,
            "beam_width": beam_width}}


def _ranking(result):
    return (-int(result["all_estimable"]), -int(result["valid_evaluations"]),
            -result["worst_estimability_margin"] if result["worst_estimability_margin"] is not None else math.inf,
            -result["worst_contrast_information"] if result["worst_contrast_information"] is not None else math.inf,
            len(result["turn_schedule_min"]), result["turn_schedule_min"])


def search_geometry(designs,*,max_turns=6,grid_min=5.,min_spacing=10.,edge_margin=5.,
                    beam_width=16,crab_models=('dynamic','wind'),maneuver_buffer_s=120.,
                    comparison=None,estimate_only=False):
    from lll.design_geometry import geometry_kinematics,geometry_problem
    from lll.design_envelope import envelope_information
    from lll.maneuvers import maneuver_mask,turn_motion_check
    from lll.policy import MODEL_PAIRS
    if comparison is not None and comparison not in MODEL_PAIRS: raise ValueError('unknown comparison')
    if not designs or not 0<=max_turns<=6 or beam_width<1 or grid_min<=0:
        raise ValueError('invalid geometry optimizer inputs')
    if not all(math.isfinite(v) for v in (grid_min,min_spacing,edge_margin,maneuver_buffer_s)) or maneuver_buffer_s < 0:
        raise ValueError('invalid geometry optimizer grid or buffer')
    if not crab_models or not set(crab_models)<={'dynamic','wind'}: raise ValueError('invalid crab models')
    geometry=[geometry_kinematics(d) for d in designs]
    duration=min(v[1]/60. for v in geometry)
    validate_turn_schedule([],duration,min_spacing,edge_margin)
    masks=[maneuver_mask(k,buffer_s=maneuver_buffer_s) for k,_ in geometry]
    grid=[i*grid_min for i in range(1,math.ceil(duration/grid_min))
          if edge_margin<=i*grid_min<=duration-edge_margin and all(
              turn_motion_check(mask,i*grid_min*60.-1.,i*grid_min*60.+25.)['safe'] for mask in masks)]
    upper=(1+max_turns*beam_width*len(grid))*len(designs)
    states_per_schedule=sum(9 if crab=='dynamic' else 13 for crab in crab_models)*3*3*(1+2*(max_turns+1))
    from lll.runtime import numerical_environment,numerical_environment_hash
    from lll.design_envelope import ENVELOPE_ASSUMPTIONS
    estimate=dict(upper_bound_schedules=1+max_turns*beam_width*len(grid),upper_bound_fits=0,
        upper_bound_anchor_svd_evaluations=upper*states_per_schedule,feasible_grid_min=grid,
        maneuver_buffer_s=maneuver_buffer_s,comparison=comparison,
        implementation_hash=implementation_hash(),numerical_environment=numerical_environment(),
        numerical_environment_hash=numerical_environment_hash(),input_designs_hash=digest(designs),
        envelope_assumptions=ENVELOPE_ASSUMPTIONS,
        evidence_scope='finite assumed-geometry envelope; no simulator, fit, power or acceptance certification')
    if estimate_only: return estimate
    cache={}
    def evaluate(schedule):
        key=tuple(schedule)
        if key in cache: return cache[key]
        details=[]
        for design,kin in zip(designs,geometry):
            for crab in crab_models:
                try:
                    problem=geometry_problem(design,schedule,crab,kin=kin)
                    report=envelope_information(problem)
                    if comparison is not None:
                        report={**report,'model_contrast_information':report['untruncated_contrasts']}
                    score=design_eligibility(report,comparison)
                    details.append(dict(track=design.get('geometry_cell'),crab_model=crab,**score))
                except (ValueError,np.linalg.LinAlgError) as exc:
                    details.append(dict(valid=False,all_estimable=False,worst_margin=None,worst_information=None,failure=str(exc)))
        valid=all(v['valid'] for v in details)
        row=dict(turn_schedule_min=list(schedule),valid_evaluations=valid,
            all_estimable=valid and all(v['all_estimable'] for v in details),
            worst_estimability_margin=min(v['worst_margin'] for v in details) if valid else None,
            worst_contrast_information=min(v['worst_information'] for v in details) if valid else None,details=details)
        cache[key]=row; return row
    best=evaluate(()); beam=[()]; frontier=[best]
    for _ in range(max_turns):
        schedules={tuple(sorted((*s,t))) for s in beam for t in grid if t not in s}
        schedules=[s for s in sorted(schedules) if not _invalid_schedule(s,duration,min_spacing,edge_margin)]
        if not schedules: break
        ranked=sorted((evaluate(s) for s in schedules),key=_ranking)
        beam=[tuple(v['turn_schedule_min']) for v in ranked[:beam_width]]; frontier.append(ranked[0])
        if _ranking(ranked[0])<_ranking(best): best=ranked[0]
    return dict(**estimate,best=best if best['all_estimable'] else None,best_diagnostic=best,
        feasible_winner=best['all_estimable'],frontier_by_turn_count=frontier,schedule_scores=list(cache.values()),
        evaluated_schedules=len(cache),
        search_method='deterministic geometry-envelope beam search; no global-optimum guarantee',
        score_order=['all_estimable','worst_estimability_margin','worst_contrast_information'],
        settings=dict(max_turns=max_turns,grid_min=grid_min,min_spacing=min_spacing,edge_margin=edge_margin,
                      beam_width=beam_width,crab_models=list(crab_models)))


def _json_safe(value):
    if isinstance(value, dict): return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value): return None
    return value


def _invalid_schedule(schedule, duration, spacing, margin):
    try: validate_turn_schedule(schedule, duration, spacing, margin)
    except ValueError: return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=600600)
    ap.add_argument('--mode',choices=['geometry','pipeline'],default='geometry')
    ap.add_argument('--track-plan',type=Path)
    ap.add_argument('--track-id')
    ap.add_argument('--protocol',type=Path)
    ap.add_argument('--comparison',choices=list(CANDIDATE_POLICY['contrasts']))
    ap.add_argument('--maneuver-buffer-s',type=float,default=120.)
    ap.add_argument("--routes", type=int, default=2)
    ap.add_argument("--scenarios", nargs="+", default=["bias_mixed", "wind"])
    ap.add_argument("--max-turns", type=int, default=6)
    ap.add_argument("--grid-min", type=float, default=5.)
    ap.add_argument("--min-spacing", type=float, default=10.)
    ap.add_argument("--edge-margin", type=float, default=5.)
    ap.add_argument("--beam-width", type=int, default=16)
    ap.add_argument("--crab-models", nargs="+", choices=["dynamic", "wind"], default=["dynamic", "wind"])
    ap.add_argument("--pilot-seconds", type=float)
    ap.add_argument("--pilot-evaluation-seconds", type=float, help="measured complete flight/design evaluation time, including SVD and simulation")
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("-o", type=Path, required=True)
    args = ap.parse_args()
    if args.mode=='geometry':
        from lll.trajectory import track_spec
        if args.track_plan:
            cases=json.loads(args.track_plan.read_text())['observed_track_cases']
            if args.track_id: cases=[v for v in cases if v['id']==args.track_id]
            if not cases: ap.error('no matching track in the frozen plan')
            designs=[realize(args.seed,'wind+bias_mixed',geometry='observed',trajectory_input=track_spec(v))
                     for v in cases if v['status']=='prepared_geometry_only']
        else:
            protocol=json.loads(args.protocol.read_text()) if args.protocol else None
            designs=[realize(seed,'wind+bias_mixed',geometry='fixed' if protocol else 'seeded',protocol=protocol)
                     for seed in seed_range('development',args.seed,args.routes)]
        result=search_geometry(designs,max_turns=args.max_turns,grid_min=args.grid_min,
            min_spacing=args.min_spacing,edge_margin=args.edge_margin,beam_width=args.beam_width,
            crab_models=args.crab_models,maneuver_buffer_s=args.maneuver_buffer_s,
            comparison=args.comparison,estimate_only=args.estimate_only)
        if args.track_plan:
            result['blocked_tracks']=[{'id':v['id'],'status':v['status']} for v in cases
                                      if v['status']!='prepared_geometry_only']
        args.o.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n'); return
    result = search(seeds=seed_range("development", args.seed, args.routes), scenarios=args.scenarios,
                    max_turns=args.max_turns, grid_min=args.grid_min, min_spacing=args.min_spacing,
                    edge_margin=args.edge_margin, beam_width=args.beam_width, crab_models=args.crab_models,
                    pilot_seconds=args.pilot_seconds, pilot_evaluation_seconds=args.pilot_evaluation_seconds, estimate_only=args.estimate_only)
    args.o.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__": main()
