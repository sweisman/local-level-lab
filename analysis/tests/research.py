"""Opt-in seeded research campaigns. Defaults run one pilot, never a tail campaign.

PYTHONPATH=analysis:server python analysis/tests/research.py --scenario drift+1 --seeds 1 -o pilot.json
Use --scenario all only after estimating and approving the pilot's runtime.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import tempfile
import time
import itertools
import math

import numpy as np
from scipy.stats import beta, chi2

from conftest import geometric_truth
from lll import __version__, models
from lll.analyze import analyze, environment
from lll.collate import gate, pool_hierarchical, pool_multivariate, joint_model_tests
from lll.fit import TERM_NAMES
from lll.policy import POLICY_VERSION, eligibility_policies, eligibility_provenance, candidate_settings, decision_stratum, MODEL_PAIRS, research_eligible
from lll.pairwise import flight_evidence, pool_evidence, decide, three_model_winner, shape_evidence, POOL_METHOD, check_pairwise_policy
from lll.runtime import numerical_environment, numerical_environment_hash
from lll.synth import synthesize
from lll.inference_policy import INFERENCE_POLICY, digest
from lll.research_calibration import stratum, check_policy, required_accepted_n, required_calibration_n, validation_power_plan
from lll.research_design import (INTERACTIONS, PARTITIONS, seed_range, realize, simulator_options,
                                 freeze_manifest, validate_manifest, scenario, trajectory, streams, implementation_hash, geometry_stress_matrix, protocol_geometry)


DRIFTS = (0, -.5, .5, -1, 1, -2, 2, -5, 5)
SCENARIOS = [f"drift{x:+g}" for x in DRIFTS] + ["smooth", "transition", "anisotropic", "correlated",
    "equator", "high_latitude", "dateline", "turn_dropout", "thermal", "long_drift", "hardware", *INTERACTIONS, "fuzz",
    "bias_step", "bias_ramp", "bias_rw_high", "bias_settling", "bias_very_long", "bias_mixed", "wind",
    "wind+bias_mixed", "wind+bias_mixed+correlated+thermal"]


def scenario_options(name):
    if name == "hardware":
        from test_analysis import HARDWARE_FAULTS
        return dict(HARDWARE_FAULTS)
    options, crab, _ = scenario(name)
    return {**options, "crab_trajectory": trajectory(crab)}


def rate_interval(k, n):
    if not n:
        return {"count": k, "n": 0, "rate": None, "ci95": None}
    return {"count": k, "n": n, "rate": k / n,
            "ci95": [0 if k == 0 else float(beta.ppf(.025, k, n-k+1)),
                     1 if k == n else float(beta.ppf(.975, k+1, n-k))]}


def summarize(records):
    groups = {}
    for r in records:
        key = (r["truth"], r["scenario"], r.get("sampling"), r.get("block"),
               r.get("candidate_id"), r.get("partition", "development"), r.get("geometry"), r.get("variant"),
               r.get("geometry_cell"), r.get("model_test_rank"))
        groups.setdefault(key, []).append(r)
    out = []
    for key, rows in groups.items():
        analyzed = [r for r in rows if "rejected" in r]
        decided = [r for r in analyzed if r["rejected"] is not None]
        accepted = [r for r in decided if not r["exclusions"]]
        empirical = [r for r in accepted if r.get("rejected_empirical") is not None]
        ks = np.array([[r["k"][n] for n in TERM_NAMES] for r in analyzed if "k" in r])
        information = [min(v["information"] for v in r["design_identifiability"]["model_contrast_information"].values())
                       for r in analyzed if (r.get("design_identifiability") or {}).get("model_contrast_information")]
        truth_vector = np.asarray(models.EXPECTED_K[key[0]])
        separated = [r for r in accepted if r.get("rejected_by_model") and
                     all(v is not None for v in r["rejected_by_model"].values())]
        pair_summary = {}
        for name, endpoints in MODEL_PAIRS.items():
            if not any(name in (row.get("pairwise") or {}) for row in rows): continue
            entries = [(row.get("pairwise") or {}).get(name, {}) for row in rows]
            informative = [entry for entry in entries if entry.get("eligible")]
            null_entries = [entry for entry in informative if key[0] in endpoints and
                            entry.get("rejected_by_model", {}).get(key[0]) is not None]
            pair_summary[name] = {"attempted": len(rows), "informative": len(informative),
                "abstentions": sum(entry.get("status", "abstain") == "abstain" for entry in entries),
                "conditional_false_rejection": rate_interval(sum(entry["rejected_by_model"][key[0]] for entry in null_entries), len(null_entries)),
                "conditional_power": rate_interval(sum(entry.get("preferred_model") == key[0] for entry in null_entries), len(null_entries)),
                "exclusion_reasons": dict(Counter(reason for entry in entries for reason in entry.get("exclusions", [])))}
        shapes = [shape_evidence(row.get('pairwise') or {}) for row in rows]
        expected_shape = 'disc' if key[0] == 'flat_still' else 'globe'
        shape_summary = dict(attempted=len(rows),
            informative=sum(bool(s['informative_comparisons']) for s in shapes),
            correct_preferences=sum(s['preferred_family'] == expected_shape for s in shapes),
            incorrect_preferences=sum(s['preferred_family'] not in (None, expected_shape) for s in shapes),
            abstentions=sum(s['status'] == 'abstain' for s in shapes),
            conflicts=sum(s['conflicting_preferences'] for s in shapes), error_rate_validated=False)
        out.append({"truth": key[0], "scenario": key[1], "sampling": key[2], "block": key[3],
                    "candidate_id": key[4], "partition": key[5], "geometry": key[6], "variant": key[7],
                    "geometry_cell": key[8], "model_test_rank": key[9],
                    "design_contrast_information": {"min": min(information), "median": float(np.median(information)), "max": max(information)} if information else None,
                    "experimental_pairwise": pair_summary,
                    'experimental_shape': shape_summary,
                    "bias": (ks.mean(axis=0)-models.EXPECTED_K[key[0]]).tolist() if len(ks) else None,
                    "variance": np.var(ks, axis=0, ddof=1).tolist() if len(ks)>1 else None,
                    "coefficient_rmse": np.sqrt(np.mean((ks-truth_vector)**2, axis=0)).tolist() if len(ks) else None,
                    "joint_coverage95": rate_interval(sum(r.get("covariance", {}).get("joint", {}).get("covers95", False) for r in analyzed if "joint" in r.get("covariance", {})),
                                                      sum("joint" in r.get("covariance", {}) for r in analyzed)),
                    "attempted": len(rows), "analysis_failures": len(rows)-len(analyzed),
                    "eligibility_exclusions": sum(bool(r["exclusions"]) for r in analyzed), "accepted": len(accepted),
                    "no_decision": len(analyzed)-len(decided),
                    "accepted_fraction": len(accepted)/len(rows),
                    "model_separation_power": (sum(not r["rejected_by_model"][key[0]] and
                                                     all(rejected for model, rejected in r["rejected_by_model"].items()
                                                         if model != key[0]) for r in separated)/len(separated)) if separated else None,
                    "exclusion_reasons": dict(Counter(x for r in analyzed for x in r["exclusions"])),
                    "unconditional": rate_interval(sum(r["rejected"] for r in decided), len(decided)),
                    "conditional_on_acceptance": rate_interval(sum(r["rejected"] for r in accepted), len(accepted)),
                    "empirical_conditional_on_acceptance": rate_interval(sum(r["rejected_empirical"] for r in empirical), len(empirical)),
                    "complete_gated_rule": rate_interval(sum(r["rejected"] for r in accepted), len(rows))})
    return out


def flight_run(truth, scenario, seed, sampling, block, boot, variant, same_side_up_turns=False,
               *, partition="development", geometry="fixed", fit_options=None, design=None, decision_policy=None, pairwise_decision_policy=None,
               diagnostics_directory=None):
    from test_analysis import HARDWARE_FAULTS
    seed_range(partition, seed)
    design = design or realize(seed, scenario, partition=partition, geometry=geometry, variant=variant,
                               same_side_up_turns=same_side_up_turns, hardware=HARDWARE_FAULTS)
    expected_streams = streams(seed, partition)
    if design.get('geometry') == 'observed' and (partition != 'development' or decision_policy is not None or pairwise_decision_policy is not None):
        raise ValueError('observed trajectory replay cannot apply empirical thresholds before domain enforcement')
    if design.get("design_version") == "simulation-design-1":
        expected_streams = {k: v for k, v in expected_streams.items() if k not in ("protocol", "missingness")}
    elif design.get("design_version") != "simulation-design-2":
        raise ValueError("unsupported replay design version")
    if design["seed"] != seed or design["partition"] != partition or design["streams"] != expected_streams:
        raise ValueError("replay design does not match partition and seed streams")
    settings = {"n_boot": boot, "bootstrap_sampling": sampling, "block_length": block, **(fit_options or {})}
    from lll.flight_domain import resolve_domain
    domain = resolve_domain(settings.get('flight_domain'),decision_policy,pairwise_decision_policy)
    if domain is not None: settings['flight_domain'] = domain
    record = dict(truth=truth, scenario=scenario, seed=seed, sampling=sampling, block=block, variant=variant,
                  same_side_up_turns=same_side_up_turns, partition=partition, geometry=design["geometry"],
                  design=design, fit_options=settings, candidate_id=digest(settings))
    record.update(candidate_engine="candidate" if candidate_settings(settings) else "legacy",
                  geometry_cell=design.get("geometry_cell"), numerical_environment=numerical_environment(),
                  numerical_environment_hash=numerical_environment_hash())
    decision = {}
    if decision_policy is not None:
        check_policy(decision_policy)
        if decision_policy["analysis_version"] != __version__:
            raise ValueError("decision policy software version differs")
        if decision_policy.get("implementation_hash") != implementation_hash():
            raise ValueError("implementation changed after calibration")
        decision = dict(decision_policy=decision_policy, decision_candidate_id=record["candidate_id"], decision_variant=variant)
        record["decision_policy_hash"] = decision_policy["policy_hash"]
    if pairwise_decision_policy is not None:
        check_pairwise_policy(pairwise_decision_policy, "flight")
        if pairwise_decision_policy.get("implementation_hash") != implementation_hash():
            raise ValueError("pairwise implementation changed after calibration")
        decision.update(pairwise_decision_policy=pairwise_decision_policy,
                        decision_candidate_id=record["candidate_id"], decision_variant=variant)
    start = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="lll-research-") as d:
            p = Path(d) / "session.zip"
            synthesize(p, truth, omega_in_fn=geometric_truth(truth), **simulator_options(design))
            options = {**settings, **design['analysis_options'], **decision, 'seed': design['streams']['bootstrap']}
            r = analyze(p,fit_options=options,**({'diagnostics_directory':diagnostics_directory} if diagnostics_directory is not None else {}))
        if not r.get("fit"):
            return {**record, "failure": "no fit", "flags": r["flags"], "slip": r.get("slip"), "elapsed_s": time.monotonic()-start}
        f = r["fit"]
        unit = r["imu"]["unit_id"]
        # Explicit simulation assumption: provenance/bench qualification supplied, scientific gates retained.
        reasons = gate(r, {unit: [("", {"tier": "usable"})]}, allow_synthetic=True)
        pairs = f.get("pairwise") or (flight_evidence(f, r["flags"]) if candidate_settings(settings) else {})
        pairs = {name: {**entry, "exclusions": list(dict.fromkeys(entry["exclusions"]+
                    gate(r, {unit: [("", {"tier": "usable"})]}, allow_synthetic=True, comparison=name)))}
                 for name, entry in pairs.items()}
        for name, entry in pairs.items():
            entry["eligible"] = not entry["exclusions"]
            decide(entry, name, entry.get("applied_thresholds"))
        delta = np.array(list(f["k"].values())) - models.EXPECTED_K[truth]
        diagnostics = {}
        for name, covariance in (("joint", f["k_cov"]), ("bootstrap", f["bootstrap"]["empirical_k_cov"])):
            if covariance is None:
                continue
            V = np.array(covariance)
            diagnostics[name] = {"covariance": covariance, "min_eigenvalue": float(np.linalg.eigvalsh(V).min()),
                                 "covers95": bool(delta @ np.linalg.pinv(V) @ delta <= chi2.ppf(.95, 3))}
        return {**record, "elapsed_s": time.monotonic()-start, "rejected": f["rejected"][truth], "exclusions": reasons, "k": f["k"],
                "delta_chi2_raw": f["delta_chi2_raw"], "rejected_by_model": f["rejected"], "p_vs_free": f["p_vs_free"],
                "delta_chi2_identifiable": f.get("delta_chi2_identifiable"), "model_test_rank": f.get("model_test_rank"),
                "inference_policy": f["inference_policy"], "eligibility_policy": f["eligibility_policy"],
                "bootstrap": f["bootstrap"], "forward_axis": r.get("forward_axis"),
                "sensor_bias": f.get("sensor_bias"),
                'domain_observables':f.get('domain_observables'),'domain_membership':f.get('domain_membership'),
                'domain_id':f.get('domain_id'),'flight_domain':f.get('flight_domain'),
                'wind_tas':f.get('wind_tas'),'wind_tas_test_near_boundary':f.get('wind_tas_test_near_boundary'),
                'mount_yaw':f.get('mount_yaw'),'mount_yaw_test_near_boundary':f.get('mount_yaw_test_near_boundary'),
                'magnetic_ambiguity_comparison':f.get('magnetic_ambiguity_comparison'),
                "k_sd": f["k_sd"], "covariance": diagnostics, "convergence": f["convergence"],
                "prior_sensitivity": f["prior_sensitivity"], "identifiability": f["identifiability"],
                "design_identifiability": f.get("design_identifiability"),
                "pairwise": pairs, "pairwise_three_model_winner": three_model_winner(pairs),
                'shape_evidence':shape_evidence(pairs),
                'pairwise_profile':f.get('pairwise_profile'),
                "wmm_shift_sigma": (r.get("fit_no_wmm_exclusion") or {}).get("k_shift_sigma"),
                "slip": r.get("slip"), "heading_diversity": r.get("heading_diversity"),
                "flags": r["flags"]}
    except Exception as exc:
        return {**record, "failure": repr(exc), "elapsed_s": time.monotonic()-start}


def planning_eligible(row, rank_margin):
    """Apply the proposed stability gate to pilot evidence without changing saved records."""
    policy = row.get("inference_policy", {})
    proposed = {**row, "inference_policy": {**policy, "settings": {
        **policy.get("settings", {}), "rank_min_relative_margin": rank_margin}}}
    return row.get("rejected") is not None and research_eligible(proposed)


def pooled_run(truth, seed, units, *, partition="development", bootstrap=0, pairwise=False, pairwise_decision_policy=None):
    from lll.collate import bootstrap_joint_tests
    rng = np.random.default_rng(streams(seed, partition)["pool"])
    items = []
    # Known correlated physical-unit effects, unequal covariances and repeated flights per unit.
    U = np.array([[.04, .025, -.01], [.025, .09, .02], [-.01, .02, .03]])
    for u in range(units):
        effect = rng.multivariate_normal(np.zeros(3), U)
        for _ in range(1 + u % 3):
            A = rng.normal(size=(3, 3)) * .06
            V = A @ A.T + np.diag([.01, .02, .03])
            k = np.asarray(models.EXPECTED_K[truth]) + effect + rng.multivariate_normal(np.zeros(3), V)
            items.append((str(u), dict(zip(TERM_NAMES, k)), dict(zip(TERM_NAMES, np.sqrt(np.diag(V)))), {}, V))
    marginal = pool_hierarchical(items)
    joint = pool_multivariate(items, marginal)
    tests = joint_model_tests(joint, marginal)
    empirical = bootstrap_joint_tests(items, n_boot=bootstrap, seed=streams(seed, partition)["bootstrap"]) if bootstrap else None
    pair_output = {}
    if pairwise:
        evidence = []
        for item in items:
            unit, k, _, _, covariance = item
            vector = np.asarray([k[name] for name in TERM_NAMES])
            pairs = {}
            for name, (a, b) in MODEL_PAIRS.items():
                direction = np.asarray(models.EXPECTED_K[a])-np.asarray(models.EXPECTED_K[b])
                coordinate = direction/(direction @ direction)
                pairs[name] = {"eligible": True, "estimate": float(coordinate @ (vector-np.asarray(models.EXPECTED_K[b]))),
                               "sd": float(np.sqrt(coordinate @ covariance @ coordinate))}
            evidence.append((unit, pairs))
        candidate_id = digest({"method": POOL_METHOD, "summary_simulator": "unit-effects-1"})
        if pairwise_decision_policy is not None:
            check_pairwise_policy(pairwise_decision_policy, "pool")
            if pairwise_decision_policy.get("implementation_hash") != implementation_hash():
                raise ValueError("pairwise pool implementation changed after calibration")
        output = pool_evidence(evidence, candidate_id, "summary", pairwise_decision_policy)
        pair_output = {"pairwise": output["pairwise"], "pairwise_three_model_winner": output["three_model_winner"],
                       'shape_evidence':output['shape_evidence'],
                       "pairwise_mode": "pool", "candidate_id": candidate_id, "variant": "summary", "model_test_rank": 1,
                       "eligibility_policy": eligibility_provenance(True), "numerical_environment": numerical_environment(),
                       "numerical_environment_hash": numerical_environment_hash()}
    return {"truth": truth, "scenario": f"pool-{units}-units", "seed": seed,
            "partition": partition, "candidate_id": digest({"pool_bootstrap": bootstrap}),
            "rejected": tests[truth]["rejected"], "exclusions": ["fewer than three units"] if units < 3 else [],
            "empirical": empirical,
            "rejected_empirical": (empirical or {}).get("tests", {}).get(truth, {}).get("rejected_experimental"),
            "items": items, "known_unit_covariance": U.tolist(), "marginal": marginal, "joint": joint, **pair_output}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenario", choices=SCENARIOS + ["all", "pool"], default="drift+0")
    ap.add_argument("--scenarios", nargs="+", choices=SCENARIOS,
                    help="explicit flight nuisance subset; use instead of --scenario")
    ap.add_argument("--truth", choices=[*models.MODELS, "all"], default="sphere_rotating")
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--partition", choices=list(PARTITIONS), default="development")
    ap.add_argument("--geometry", choices=["fixed", "seeded", "stress",'observed'], default="seeded")
    ap.add_argument('--trajectory',type=Path,help='frozen development trajectory replay specification')
    ap.add_argument('--diagnostics-root',type=Path,help='retain complete per-task diagnostic artifacts')
    ap.add_argument('--design-mode',choices=['anchor','envelope'],default='anchor')
    ap.add_argument('--pairwise-method',choices=['observable_coordinate','profile'],default='observable_coordinate')
    ap.add_argument('--magnetic-ambiguity',choices=['exclude','model_and_compare'],default='exclude')
    ap.add_argument('--flight-domain',type=Path,help='explicit preregistered observable route/protocol envelope')
    ap.add_argument("--geometry-cells", nargs="+", help="preregister a subset of stress-cell IDs")
    ap.add_argument("--protocol", type=Path, help="geometry/turn protocol JSON; requires --geometry fixed")
    ap.add_argument("--list-geometry-cells", action="store_true", help="write the matrix without running simulations")
    ap.add_argument("--bootstrap", type=int, default=20)
    ap.add_argument("--sampling", nargs="+", choices=["moving", "segment"], default=["moving"])
    ap.add_argument("--blocks", nargs="+", type=int, default=[15])
    ap.add_argument("--crab-model", nargs="+", choices=["constant", "dynamic", "wind",'wind_tas'], default=["constant"])
    ap.add_argument("--noise-model", nargs="+", choices=["global", "axis", "axis_segment"], default=["global"])
    ap.add_argument("--bias-model", nargs="+", choices=["constant", "dynamic"], default=["constant"])
    ap.add_argument("--bias-knot-seconds", nargs="+", type=float, default=[INFERENCE_POLICY["bias_knot_seconds"]])
    ap.add_argument("--bias-rw-sigma-dph-sqrth", nargs="+", type=float, default=[INFERENCE_POLICY["bias_rw_sigma_dph_sqrth"]])
    ap.add_argument("--bootstrap-refit", nargs="+", choices=["linearized", "nonlinear"], default=["linearized"])
    ap.add_argument("--crab-rate-sigma-dph", nargs="+", type=float, default=[1.])
    ap.add_argument("--crab-knot-seconds", nargs="+", type=float, default=[None])
    ap.add_argument("--forward-uncertainty", action="store_true")
    ap.add_argument('--forward-reference', choices=['legacy','matched'], default='legacy')
    ap.add_argument("--research-candidate", action="store_true", help="use candidate engine even for constant/global settings")
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--decision-policy", type=Path)
    ap.add_argument("--pairwise-evidence", action="store_true", help="preregister empirical pairwise decisions and their additional validation family")
    ap.add_argument("--pairwise-decision-policy", type=Path)
    ap.add_argument("--tail-min-accepted", type=int)
    ap.add_argument("--calibration-min-accepted", type=int)
    ap.add_argument("--calibration-tail-observations", type=int, default=30)
    ap.add_argument("--calibration-tail-confidence", type=float, default=.95)
    ap.add_argument("--calibration-alpha", type=float, help="threshold tail target; defaults to the claimed 0.0027 rate")
    ap.add_argument("--validation-design-rate", type=float, help="assumed true false-rejection rate for validation power planning")
    ap.add_argument("--validation-power", type=float, default=.90)
    ap.add_argument("--model-test-ranks", type=int, nargs="+", choices=[1, 2, 3], default=[1, 2, 3],
                    help="candidate ranks to preregister; other ranks abstain under the frozen rule")
    ap.add_argument("--rank-min-relative-margin", type=float, default=0., help="optional preregistered rank-boundary stability gate")
    ap.add_argument("--allowed-failures", type=int, default=0)
    ap.add_argument("--tail-confidence", type=float, default=.95)
    ap.add_argument("--development-campaign", type=Path, help="pilot JSON used only for campaign cost estimates")
    ap.add_argument("--write-manifest", type=Path, help="freeze configuration without running simulations")
    ap.add_argument('--write-sharded-plan',type=Path,help='freeze deterministic flight shards without running any tasks')
    ap.add_argument('--shards',type=int,default=2,help='fixed shard count; execution uses at most two local workers')
    ap.add_argument("--replay", type=Path, help="replay the designs and fit settings in a research JSON")
    ap.add_argument("--units", nargs="+", type=int, default=[2, 3, 5, 10, 30])
    ap.add_argument("--variant", choices=["spp", "ble"], default="spp")
    ap.add_argument("--same-side-up-turns", action="store_true", help="turn the mounted IMU at 20, 50 and 80 flight minutes")
    ap.add_argument("--turn-schedule", nargs="*", type=float, help="explicit same-side-up turn times in flight minutes")
    ap.add_argument("--turn-min-spacing", type=float, default=10.)
    ap.add_argument("--turn-edge-margin", type=float, default=5.)
    ap.add_argument("-o", type=Path, required=True)
    args = ap.parse_args()
    if args.magnetic_ambiguity=='model_and_compare':
        if args.partition!='development' or args.decision_policy or args.pairwise_decision_policy:
            ap.error('magnetic two-path candidate is development only pending dual-path calibration')
        if args.design_mode!='envelope' or args.pairwise_method!='profile':
            ap.error('magnetic comparison requires --design-mode envelope --pairwise-method profile')
        if args.bootstrap>0 and any(v!='nonlinear' for v in args.bootstrap_refit):
            ap.error('magnetic comparison bootstrap requires nonlinear refits')
    if 'wind_tas' in args.crab_model:
        if args.design_mode!='envelope': ap.error('physical wind/TAS requires --design-mode envelope')
        if args.bootstrap>0 and any(v!='nonlinear' for v in args.bootstrap_refit):
            ap.error('physical wind/TAS bootstrap requires --bootstrap-refit nonlinear')
    if args.pairwise_method == 'profile' and args.bootstrap > 0 and any(
            refit != 'nonlinear' for refit in args.bootstrap_refit):
        ap.error('pair profiles with bootstrap require --bootstrap-refit nonlinear')
    trajectory_input=json.loads(args.trajectory.read_text()) if args.trajectory else None
    if (args.geometry=='observed') != (trajectory_input is not None):
        ap.error('observed geometry requires --trajectory; other geometry cannot use it')
    if args.geometry=='observed' and (args.partition!='development' or args.decision_policy or args.pairwise_decision_policy):
        ap.error('observed replay is development only without empirical policies')
    if args.pairwise_method=='profile' and args.design_mode!='envelope':
        ap.error('pair profile requires --design-mode envelope')
    if args.scenarios and args.scenario != "drift+0":
        ap.error("use --scenarios instead of --scenario for an explicit flight subset")
    stress_cells = geometry_stress_matrix()
    if args.list_geometry_cells:
        args.o.write_text(json.dumps(stress_cells, indent=2)+"\n")
        return
    protocol = protocol_geometry(json.loads(args.protocol.read_text())) if args.protocol else None
    if protocol is not None and (args.geometry != "fixed" or args.geometry_cells or args.same_side_up_turns
                                 or args.turn_schedule is not None or args.scenario == "pool"):
        ap.error("--protocol requires fixed flight geometry and its own turn schedule")
    geometry_cells = args.geometry_cells or [cell["id"] for cell in stress_cells] if args.geometry == "stress" else [None]
    if protocol is not None: geometry_cells = ["protocol-"+digest(protocol)]
    if trajectory_input is not None: geometry_cells = ['trajectory-'+trajectory_input['trajectory_hash']]
    if args.geometry_cells and args.geometry != "stress": ap.error("--geometry-cells requires --geometry stress")
    if args.geometry == "stress" and (not set(geometry_cells) <= {cell["id"] for cell in stress_cells}
                                     or args.same_side_up_turns or args.turn_schedule is not None):
        ap.error("stress geometry requires known cells and their preregistered turn schedules")
    if args.partition != "development" and not args.replay and args.truth != "all":
        ap.error("calibration and validation campaigns require --truth all")
    from lll.research_design import plain
    decision_policy = json.loads(args.decision_policy.read_text()) if args.decision_policy else None
    if decision_policy: check_policy(decision_policy)
    pairwise_policy = json.loads(args.pairwise_decision_policy.read_text()) if args.pairwise_decision_policy else None
    if pairwise_policy: check_pairwise_policy(pairwise_policy, "pool" if args.scenario == "pool" else "flight")
    from lll.flight_domain import resolve_domain
    try:
        domain = resolve_domain(json.loads(args.flight_domain.read_text()) if args.flight_domain else None,
                                decision_policy,pairwise_policy)
    except ValueError as exc: ap.error(str(exc))
    if domain is not None and args.scenario=='pool': ap.error('summary pooling has a separate domain; flight domains do not transfer')
    if args.partition!='development' and args.scenario!='pool' and domain is None:
        ap.error('new flight calibration/validation requires --flight-domain or a domain-bound decision policy')
    config = {k: v for k, v in vars(args).items() if k not in ("o", "manifest", "write_manifest", "replay", "decision_policy", "pairwise_decision_policy", "development_campaign", "protocol",'trajectory','diagnostics_root','flight_domain','write_sharded_plan','shards')}
    config['flight_domain'] = domain
    config['trajectory_input']=trajectory_input
    config["protocol"] = protocol
    config["decision_policy_hash"] = decision_policy["policy_hash"] if decision_policy else None
    config["pairwise_decision_policy_hash"] = pairwise_policy["policy_hash"] if pairwise_policy else None
    config["pairwise_evidence"] = bool(args.pairwise_evidence or pairwise_policy or args.pairwise_method=='profile')
    scenarios = sorted(set(args.scenarios)) if args.scenarios else SCENARIOS if args.scenario == "all" else [args.scenario]
    if args.geometry in ('stress','observed') or protocol is not None:
        geometry_scenarios = {"equator", "high_latitude", "dateline", "turn_dropout", "turn_dropout_drift", "fuzz"}
        if args.scenario != "all" and set(scenarios) & geometry_scenarios:
            ap.error("stress cells and explicit protocols require nuisance-only scenarios")
        scenarios = [s for s in scenarios if s not in geometry_scenarios]
    jobs = []
    for s, b, crab, noise, refit, rate, crab_knot, bias, knot, rw in itertools.product(
            args.sampling, args.blocks, args.crab_model, args.noise_model, args.bootstrap_refit,
            args.crab_rate_sigma_dph, args.crab_knot_seconds, args.bias_model, args.bias_knot_seconds, args.bias_rw_sigma_dph_sqrth):
        jobs.append(dict(n_boot=args.bootstrap, bootstrap_sampling=s, block_length=b, crab_model=crab,
                         noise_model=noise, bootstrap_refit=refit, crab_rate_sigma_dph=rate,
                         forward_uncertainty=args.forward_uncertainty, crab_knot_seconds=crab_knot,
                         research_candidate=args.research_candidate or config["pairwise_evidence"], bias_model=bias, bias_knot_seconds=knot,
                         bias_rw_sigma_dph_sqrth=rw, rank_min_relative_margin=args.rank_min_relative_margin))
        if args.design_mode!='anchor': jobs[-1]['design_mode']=args.design_mode
        if args.pairwise_method!='observable_coordinate': jobs[-1]['pairwise_method']=args.pairwise_method
        if args.magnetic_ambiguity!='exclude': jobs[-1]['magnetic_ambiguity']=args.magnetic_ambiguity
        if args.forward_reference!='legacy':
            if not args.forward_uncertainty or not jobs[-1]['research_candidate']:
                ap.error('matched forward reference requires --forward-uncertainty and research candidate')
            jobs[-1]['forward_reference']=args.forward_reference
        if domain is not None: jobs[-1]['flight_domain']=domain
    jobs = list({digest(job): job for job in jobs}.values())
    operational_cells = sorted({decision_stratum({"candidate_id": digest(job), "variant": args.variant, "model_test_rank": rank,
                                                  'domain_id':domain['domain_id'] if domain else None})
                                for job in jobs for rank in (args.model_test_ranks if candidate_settings(job) else [None])})
    candidate_count = len(operational_cells)
    attempt_cells = candidate_count*len(scenarios)*len(geometry_cells)*len(models.MODELS)
    family_size = attempt_cells
    if config["pairwise_evidence"]:
        pair_candidates = len(jobs) if args.pairwise_method == 'profile' else candidate_count
        family_size += pair_candidates*len(scenarios)*len(geometry_cells)*2*len(MODEL_PAIRS)
    if args.scenario == "pool" and config["pairwise_evidence"]:
        if decision_policy is not None: ap.error("summary pairwise pooling uses --pairwise-decision-policy")
        family_size = len(args.units)*2*len(MODEL_PAIRS)
        attempt_cells = len(args.units)*len(models.MODELS)
        config["preregistered_pool_units"] = args.units
        pool_candidate = digest({"method": POOL_METHOD, "summary_simulator": "unit-effects-1"})
        operational_cells = [decision_stratum({"candidate_id": pool_candidate, "variant": "summary", "model_test_rank": 1})]
        candidate_count = 1
        from lll.pairwise_calibration import group as pair_group
        config["preregistered_pairwise_groups"] = [pair_group({"scenario": f"pool-{units}-units",
            "candidate_id": pool_candidate, "variant": "summary", "model_test_rank": 1, "geometry": None,
            "pairwise": {name: {"n_units": units}}}, name, "pool") for units in args.units for name in MODEL_PAIRS]
    if decision_policy is not None:
        candidate_count = len(decision_policy["thresholds"])
        family_size = len(decision_policy["diagnostic_thresholds"])*len(models.MODELS)
        operational_cells = sorted(decision_policy["thresholds"])
        attempt_cells = len(decision_policy["diagnostic_thresholds"])*len(models.MODELS)
    if pairwise_policy is not None:
        family_size += pairwise_policy["family_size"] if decision_policy else 0
        if decision_policy is None: family_size = pairwise_policy["family_size"]
        primary_diagnostics = set(decision_policy["diagnostic_thresholds"]) if decision_policy else set()
        pair_diagnostics = {json.loads(key)[0] for key in pairwise_policy["diagnostic_thresholds"]}
        attempt_cells = len(primary_diagnostics | pair_diagnostics)*len(models.MODELS)
        if pairwise_policy["mode"] == "flight":
            # Pair-line threshold keys contain a comparison/method, not a global rank.
            # Recover campaign cells from diagnostic metadata rather than misreading those keys.
            pair_cells=set()
            for diagnostic in pair_diagnostics:
                fields=json.loads(diagnostic)
                pair_cells.add(decision_stratum({'candidate_id':fields[1],'variant':fields[4],
                    'model_test_rank':fields[5],'domain_id':fields[6] if len(fields)>6 else None}))
            operational_cells = sorted(set(decision_policy["thresholds"] if decision_policy else ()) | pair_cells)
            candidate_count = len(operational_cells)
    alpha = decision_policy["alpha"] if decision_policy else .0027
    calibration_alpha = args.calibration_alpha if args.calibration_alpha is not None else (
        (decision_policy or pairwise_policy or {}).get("calibration_alpha", alpha))
    if not 0 < calibration_alpha <= alpha: ap.error("calibration alpha must be positive and no greater than the claimed rate")
    for policy in (decision_policy, pairwise_policy):
        if policy is not None and policy.get("calibration_alpha", alpha) != calibration_alpha:
            ap.error("calibration alpha differs from the frozen decision policy")
    config["calibration_alpha"] = calibration_alpha
    power_plan = None
    if args.validation_design_rate is not None:
        power_plan = validation_power_plan(alpha, family_size, args.validation_design_rate, args.tail_confidence, args.validation_power)
        args.allowed_failures = max(args.allowed_failures, power_plan["allowed_failures"])
        config["allowed_failures"] = args.allowed_failures
    required = required_accepted_n(alpha, family_size, args.tail_confidence, args.allowed_failures)
    if args.tail_min_accepted is not None and args.tail_min_accepted < required:
        ap.error(f"tail minimum {args.tail_min_accepted} is below exact required count {required}")
    config["tail_min_accepted"] = args.tail_min_accepted or required
    calibration_required = required_calibration_n(calibration_alpha, args.calibration_tail_observations, args.calibration_tail_confidence)
    if args.calibration_min_accepted is not None and args.calibration_min_accepted < calibration_required:
        ap.error(f"calibration minimum is below tail-precision required count {calibration_required}")
    config["calibration_min_accepted"] = args.calibration_min_accepted or calibration_required
    planned_minimum = (config["tail_min_accepted"] if args.partition == "validation" else config["calibration_min_accepted"]
                       if args.partition == "calibration" else max(config["tail_min_accepted"], config["calibration_min_accepted"]))
    pilot = json.loads(args.development_campaign.read_text()) if args.development_campaign else None
    if pilot is not None and pilot.get("partition") != "development":
        ap.error("cost estimates require a development campaign")
    pilot_rows = pilot["records"] if pilot else []
    acceptance_groups = {}
    for row in pilot_rows:
        key = tuple(row.get(k) for k in ("scenario", "candidate_id", "geometry", "geometry_cell", "variant", "truth"))
        acceptance_groups.setdefault(key, []).append(row)
    probabilities = []
    for group in acceptance_groups.values():
        ranks = ([1] if any(row.get("pairwise_mode") == "pool" for row in group) else
                 args.model_test_ranks if any(row.get("candidate_engine") == "candidate" for row in group) else [None])
        if (decision_policy or pairwise_policy) and group[0].get("candidate_engine") == "candidate":
            covered = [json.loads(cell)[2] for cell in operational_cells if json.loads(cell)[:2] ==
                       [group[0].get("candidate_id"), group[0].get("variant")]]
            if covered: ranks = sorted(set(covered))
        probabilities.extend(sum(row.get("model_test_rank") == rank and planning_eligible(row, args.rank_min_relative_margin)
                                 for row in group)/len(group) for rank in ranks)
    acceptance = min(probabilities) if probabilities else None
    runtimes = [r["elapsed_s"] for r in pilot["records"] if r.get("elapsed_s") is not None] if pilot else []
    seconds = float(np.mean(runtimes)) if runtimes else None
    config["campaign_plan"] = {"decision_cells": candidate_count*len(models.MODELS),
                               "validation_power_plan": power_plan,
                               "attempt_cells": attempt_cells,
                               "operational_strata": candidate_count, "validation_family_size": family_size,
                               "required_accepted_per_cell": planned_minimum,
                               "required_accepted_validation": config["tail_min_accepted"],
                               "required_accepted_calibration": config["calibration_min_accepted"], "allowed_failures": args.allowed_failures,
                               "confidence": args.tail_confidence, "alpha": alpha,
                               "pilot_campaign_hash": digest(pilot) if pilot else None,
                               "development_acceptance_probability": acceptance,
                               "acceptance_estimate_method": "minimum diagnostic/truth cell acceptance with proposed rank margin, including failed attempts; historical pilot is provisional",
                               "estimated_attempts_total": math.ceil(planned_minimum/acceptance)*attempt_cells if acceptance else None,
                               "estimated_calibration_attempts_total": math.ceil(config["calibration_min_accepted"]/acceptance)*attempt_cells if acceptance else None,
                               "estimated_validation_attempts_total": math.ceil(config["tail_min_accepted"]/acceptance)*attempt_cells if acceptance else None,
                               "pilot_seconds_per_attempt": seconds,
                               "estimated_compute_seconds": math.ceil(planned_minimum/acceptance)*attempt_cells*seconds if acceptance and seconds else None,
                               "estimated_combined_compute_seconds": (math.ceil(config["calibration_min_accepted"]/acceptance)+math.ceil(config["tail_min_accepted"]/acceptance))*attempt_cells*seconds if acceptance and seconds else None}
    config["preregistered_scenarios"] = [f"pool-{units}-units" for units in args.units] if args.scenario == "pool" else scenarios
    config["preregistered_geometry_cells"] = [None] if args.scenario == "pool" else geometry_cells
    config["geometry_domain"] = [{key: value for key, value in cell.items() if key != "simulator"}
                                 for cell in stress_cells if cell["id"] in geometry_cells] if args.geometry == "stress" else None
    if protocol is not None: config["geometry_domain"] = [{"id": geometry_cells[0], **protocol}]
    if trajectory_input is not None:
        config['geometry_domain'] = [{'id':geometry_cells[0], 'trajectory_hash':trajectory_input['trajectory_hash'],
                                     'mode':trajectory_input['mode'], 'evidence_use':'development only'}]
    if args.scenario == "pool": config["geometry"] = None
    config["operational_cells"] = operational_cells
    seeds = seed_range(args.partition, args.seed, args.seeds)
    config["seed"] = seeds.start
    if args.write_sharded_plan:
        if args.replay or args.scenario=='pool' or args.write_manifest:
            ap.error('sharded preparation requires fresh flight tasks and a single plan output')
        from lll.campaign_shards import build_plan
        try: plan=build_plan(freeze_manifest(config),jobs,args.shards,decision_policy,pairwise_policy)
        except ValueError as exc: ap.error(str(exc))
        args.write_sharded_plan.write_text(json.dumps(plain(plan),indent=2,allow_nan=False)+'\n')
        return
    if args.write_manifest:
        args.write_manifest.write_text(json.dumps(freeze_manifest(config), indent=2)+"\n")
        return
    manifest_hash = None
    if args.manifest:
        manifest_hash = validate_manifest(json.loads(args.manifest.read_text()), config)
    if args.partition != "development" and not manifest_hash and not args.replay:
        ap.error("calibration and validation require --manifest")
    start, records = time.monotonic(), []
    source_hash = implementation_hash()
    def save():
        args.o.write_text(json.dumps(plain({"analysis_version": __version__, "policy_version": POLICY_VERSION,
            "environment": environment(), "elapsed_s": time.monotonic()-start, "config": config,
            "manifest_hash": manifest_hash, "manifest": freeze_manifest(config) if manifest_hash else None,
            "partition": args.partition, "implementation_hash": source_hash, "eligibility_policies": eligibility_policies(),
            "numerical_environment": numerical_environment(), "numerical_environment_hash": numerical_environment_hash(),
        "simulation_assumption": "approved provenance and usable bench tier; remaining gates applied",
            "summary": summarize(records), "records": records}), indent=2, allow_nan=False)+"\n")
    if args.replay:
        original = json.loads(args.replay.read_text())
        # Replays are diagnostics, never fresh holdout evidence.
        for row in original["records"]:
            if "design" not in row:
                ap.error("replay requires flight design records")
            records.append(flight_run(row["truth"], row["scenario"], row["seed"], row["sampling"], row["block"],
                                      row["fit_options"]["n_boot"], row["variant"], partition=row["partition"],
                                      design=row["design"], fit_options=row["fit_options"], decision_policy=decision_policy,
                                      pairwise_decision_policy=pairwise_policy,
                                      diagnostics_directory=None if args.diagnostics_root is None else
                                      args.diagnostics_root/digest({'replay':True,'truth':row['truth'],
                                          'design':row['design'],'settings':row['fit_options']})))
            records[-1]["replay"] = True
            save()
        return
    truths = models.MODELS if args.truth == "all" else [args.truth]
    for truth in truths:
        for scenario in scenarios:
            for seed in seeds:
                if scenario == "pool":
                    records.extend(pooled_run(truth, seed, n, partition=args.partition, bootstrap=args.bootstrap,
                                               pairwise=config["pairwise_evidence"], pairwise_decision_policy=pairwise_policy) for n in args.units)
                else:
                    for job, geometry_cell in itertools.product(jobs, geometry_cells):
                        settings = {k: v for k, v in job.items() if k not in ("n_boot", "bootstrap_sampling", "block_length")}
                        design = realize(seed, scenario, partition=args.partition, geometry=args.geometry,
                                         variant=args.variant, same_side_up_turns=args.same_side_up_turns,
                                         hardware=scenario_options("hardware") if scenario == "hardware" else None,
                                         turn_schedule=args.turn_schedule, turn_min_spacing=args.turn_min_spacing,
                                         turn_edge_margin=args.turn_edge_margin, geometry_cell=geometry_cell, protocol=protocol,
                                         trajectory_input=trajectory_input)
                        records.append(flight_run(truth, scenario, seed, job["bootstrap_sampling"], job["block_length"], args.bootstrap, args.variant,
                                                  args.same_side_up_turns, partition=args.partition,
                                                  geometry=args.geometry, fit_options=settings, decision_policy=decision_policy,
                                                  pairwise_decision_policy=pairwise_policy,
                                                  design=design,diagnostics_directory=None if args.diagnostics_root is None else
                                                  args.diagnostics_root/digest({'truth':truth,'design':design,'settings':job})))
                        save()
                save()
    print(f"{len(records)} runs in {time.monotonic()-start:.1f}s; {args.o}")


if __name__ == "__main__":
    main()
