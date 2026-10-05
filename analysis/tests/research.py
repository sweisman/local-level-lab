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

import numpy as np
from scipy.stats import beta, chi2

from conftest import geometric_truth
from lll import __version__, models
from lll.analyze import analyze, environment
from lll.collate import gate, pool_hierarchical, pool_multivariate, joint_model_tests
from lll.fit import TERM_NAMES
from lll.policy import POLICY_VERSION
from lll.synth import synthesize
from lll.inference_policy import digest
from lll.research_calibration import stratum, check_policy
from lll.research_design import (INTERACTIONS, PARTITIONS, seed_range, realize, simulator_options,
                                 freeze_manifest, validate_manifest, scenario, trajectory, streams, implementation_hash)


DRIFTS = (0, -.5, .5, -1, 1, -2, 2, -5, 5)
SCENARIOS = [f"drift{x:+g}" for x in DRIFTS] + ["smooth", "transition", "anisotropic", "correlated",
    "equator", "high_latitude", "dateline", "turn_dropout", "thermal", "long_drift", "hardware", *INTERACTIONS, "fuzz"]


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
               r.get("candidate_id"), r.get("partition", "development"), r.get("geometry"), r.get("variant"))
        groups.setdefault(key, []).append(r)
    out = []
    for key, rows in groups.items():
        analyzed = [r for r in rows if "rejected" in r]
        accepted = [r for r in analyzed if not r["exclusions"]]
        empirical = [r for r in accepted if r.get("rejected_empirical") is not None]
        ks = np.array([[r["k"][n] for n in TERM_NAMES] for r in analyzed if "k" in r])
        out.append({"truth": key[0], "scenario": key[1], "sampling": key[2], "block": key[3],
                    "candidate_id": key[4], "partition": key[5], "geometry": key[6], "variant": key[7],
                    "bias": (ks.mean(axis=0)-models.EXPECTED_K[key[0]]).tolist() if len(ks) else None,
                    "variance": np.var(ks, axis=0, ddof=1).tolist() if len(ks)>1 else None,
                    "joint_coverage95": rate_interval(sum(r.get("covariance", {}).get("joint", {}).get("covers95", False) for r in analyzed if "joint" in r.get("covariance", {})),
                                                      sum("joint" in r.get("covariance", {}) for r in analyzed)),
                    "attempted": len(rows), "analysis_failures": len(rows)-len(analyzed),
                    "eligibility_exclusions": len(analyzed)-len(accepted), "accepted": len(accepted),
                    "exclusion_reasons": dict(Counter(x for r in analyzed for x in r["exclusions"])),
                    "unconditional": rate_interval(sum(r["rejected"] for r in analyzed), len(analyzed)),
                    "conditional_on_acceptance": rate_interval(sum(r["rejected"] for r in accepted), len(accepted)),
                    "empirical_conditional_on_acceptance": rate_interval(sum(r["rejected_empirical"] for r in empirical), len(empirical)),
                    "complete_gated_rule": rate_interval(sum(r["rejected"] for r in accepted), len(rows))})
    return out


def flight_run(truth, scenario, seed, sampling, block, boot, variant, same_side_up_turns=False,
               *, partition="development", geometry="fixed", fit_options=None, design=None, decision_policy=None):
    from test_analysis import HARDWARE_FAULTS
    seed_range(partition, seed)
    design = design or realize(seed, scenario, partition=partition, geometry=geometry, variant=variant,
                               same_side_up_turns=same_side_up_turns, hardware=HARDWARE_FAULTS)
    if design["seed"] != seed or design["partition"] != partition or design["streams"] != streams(seed, partition):
        raise ValueError("replay design does not match partition and seed streams")
    settings = {"n_boot": boot, "bootstrap_sampling": sampling, "block_length": block, **(fit_options or {})}
    record = dict(truth=truth, scenario=scenario, seed=seed, sampling=sampling, block=block, variant=variant,
                  same_side_up_turns=same_side_up_turns, partition=partition, geometry=design["geometry"],
                  design=design, fit_options=settings, candidate_id=digest(settings))
    decision = {}
    if decision_policy is not None:
        check_policy(decision_policy)
        if decision_policy["analysis_version"] != __version__:
            raise ValueError("decision policy software version differs")
        if decision_policy.get("implementation_hash") != implementation_hash():
            raise ValueError("implementation changed after calibration")
        decision = dict(decision_thresholds=decision_policy["thresholds"][stratum(record)], decision_policy_hash=decision_policy["policy_hash"])
        record["decision_policy_hash"] = decision_policy["policy_hash"]
    start = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="lll-research-") as d:
            p = Path(d) / "session.zip"
            synthesize(p, truth, omega_in_fn=geometric_truth(truth), **simulator_options(design))
            r = analyze(p, fit_options={**settings, **design["analysis_options"], **decision, "seed": design["streams"]["bootstrap"]})
        if not r.get("fit"):
            return {**record, "failure": "no fit", "flags": r["flags"], "elapsed_s": time.monotonic()-start}
        f = r["fit"]
        unit = r["imu"]["unit_id"]
        # Explicit simulation assumption: provenance/bench qualification supplied, scientific gates retained.
        reasons = gate(r, {unit: [("", {"tier": "usable"})]}, allow_synthetic=True)
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
                "inference_policy": f["inference_policy"], "bootstrap": f["bootstrap"], "forward_axis": r.get("forward_axis"),
                "k_sd": f["k_sd"], "covariance": diagnostics, "convergence": f["convergence"],
                "prior_sensitivity": f["prior_sensitivity"], "identifiability": f["identifiability"],
                "wmm_shift_sigma": (r.get("fit_no_wmm_exclusion") or {}).get("k_shift_sigma"),
                "flags": r["flags"]}
    except Exception as exc:
        return {**record, "failure": repr(exc), "elapsed_s": time.monotonic()-start}


def pooled_run(truth, seed, units, *, partition="development", bootstrap=0):
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
    return {"truth": truth, "scenario": f"pool-{units}-units", "seed": seed,
            "partition": partition, "candidate_id": digest({"pool_bootstrap": bootstrap}),
            "rejected": tests[truth]["rejected"], "exclusions": ["fewer than three units"] if units < 3 else [],
            "empirical": empirical,
            "rejected_empirical": (empirical or {}).get("tests", {}).get(truth, {}).get("rejected_experimental"),
            "items": items, "known_unit_covariance": U.tolist(), "marginal": marginal, "joint": joint}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenario", choices=SCENARIOS + ["all", "pool"], default="drift+0")
    ap.add_argument("--truth", choices=[*models.MODELS, "all"], default="sphere_rotating")
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--partition", choices=list(PARTITIONS), default="development")
    ap.add_argument("--geometry", choices=["fixed", "seeded"], default="seeded")
    ap.add_argument("--bootstrap", type=int, default=20)
    ap.add_argument("--sampling", nargs="+", choices=["moving", "segment"], default=["moving"])
    ap.add_argument("--blocks", nargs="+", type=int, default=[15])
    ap.add_argument("--crab-model", nargs="+", choices=["constant", "dynamic"], default=["constant"])
    ap.add_argument("--noise-model", nargs="+", choices=["global", "axis", "axis_segment"], default=["global"])
    ap.add_argument("--bootstrap-refit", nargs="+", choices=["linearized", "nonlinear"], default=["linearized"])
    ap.add_argument("--crab-rate-sigma-dph", nargs="+", type=float, default=[1.])
    ap.add_argument("--forward-uncertainty", action="store_true")
    ap.add_argument("--research-candidate", action="store_true", help="use candidate engine even for constant/global settings")
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--decision-policy", type=Path)
    ap.add_argument("--tail-min-accepted", type=int, default=2000)
    ap.add_argument("--write-manifest", type=Path, help="freeze configuration without running simulations")
    ap.add_argument("--replay", type=Path, help="replay the designs and fit settings in a research JSON")
    ap.add_argument("--units", nargs="+", type=int, default=[2, 3, 5, 10, 30])
    ap.add_argument("--variant", choices=["spp", "ble"], default="spp")
    ap.add_argument("--same-side-up-turns", action="store_true", help="turn the mounted IMU at 20, 50 and 80 flight minutes")
    ap.add_argument("-o", type=Path, required=True)
    args = ap.parse_args()
    from lll.research_design import plain
    decision_policy = json.loads(args.decision_policy.read_text()) if args.decision_policy else None
    if decision_policy: check_policy(decision_policy)
    config = {k: v for k, v in vars(args).items() if k not in ("o", "manifest", "write_manifest", "replay", "decision_policy")}
    config["decision_policy_hash"] = decision_policy["policy_hash"] if decision_policy else None
    seeds = seed_range(args.partition, args.seed, args.seeds)
    config["seed"] = seeds.start
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
            "partition": args.partition, "implementation_hash": source_hash,
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
                                      design=row["design"], fit_options=row["fit_options"], decision_policy=decision_policy))
            records[-1]["replay"] = True
            save()
        return
    truths = models.MODELS if args.truth == "all" else [args.truth]
    scenarios = SCENARIOS if args.scenario == "all" else [args.scenario]
    for truth in truths:
        for scenario in scenarios:
            for seed in seeds:
                if scenario == "pool":
                    records.extend(pooled_run(truth, seed, n, partition=args.partition, bootstrap=args.bootstrap) for n in args.units)
                else:
                    for s, b, crab, noise, refit, rate in itertools.product(args.sampling, args.blocks, args.crab_model,
                                                                           args.noise_model, args.bootstrap_refit, args.crab_rate_sigma_dph):
                        settings = dict(crab_model=crab, noise_model=noise, bootstrap_refit=refit,
                                        crab_rate_sigma_dph=rate, forward_uncertainty=args.forward_uncertainty,
                                        research_candidate=args.research_candidate)
                        records.append(flight_run(truth, scenario, seed, s, b, args.bootstrap, args.variant,
                                                  args.same_side_up_turns, partition=args.partition,
                                                  geometry=args.geometry, fit_options=settings, decision_policy=decision_policy))
                        save()
                save()
    print(f"{len(records)} runs in {time.monotonic()-start:.1f}s; {args.o}")


if __name__ == "__main__":
    main()
