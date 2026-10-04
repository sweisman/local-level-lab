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

import numpy as np
from scipy.stats import beta, chi2

from conftest import geometric_truth
from lll import __version__, models
from lll.analyze import analyze, environment
from lll.collate import gate, pool_hierarchical, pool_multivariate, joint_model_tests
from lll.fit import TERM_NAMES
from lll.policy import POLICY_VERSION
from lll.synth import synthesize


DRIFTS = (0, -.5, .5, -1, 1, -2, 2, -5, 5)
SCENARIOS = [f"drift{x:+g}" for x in DRIFTS] + ["smooth", "transition", "anisotropic", "correlated",
    "equator", "high_latitude", "dateline", "turn_dropout", "thermal", "long_drift", "hardware"]


def scenario_options(name):
    if name == "hardware":
        from test_analysis import HARDWARE_FAULTS
        return dict(HARDWARE_FAULTS)
    if name.startswith("drift"):
        rate = float(name[5:])
        return {"crab_trajectory": lambda t: rate * t / 3600}
    return {
        "smooth": {"crab_trajectory": lambda t: 5 * np.sin(2 * np.pi * t / 7200)},
        "transition": {"crab_trajectory": lambda t: 5 * (1 - np.cos(np.pi * np.clip((t - 2400) / 300, 0, 1)))},
        "anisotropic": {"gyro_noise_cov": np.diag([1, 4, 9])},
        "correlated": {"gyro_noise_cov": [[1, .7, .2], [.7, 2, .4], [.2, .4, 1]]},
        "equator": {"lat0": 0., "legs": ((10, 30), (100, 30), (190, 30))},
        "high_latitude": {"lat0": 65., "legs": ((90, 30), (180, 30), (270, 30))},
        "dateline": {"lat0": 20., "lon0": 179., "legs": ((90, 45), (180, 45))},
        "turn_dropout": {"index_turns": ((40, "z"),), "link_dropouts": ((40.02, 3),)},
        "thermal": {"flight_temp_rise_c": 12, "temp_coef_dph_per_c": (1, -.5, 2), "temp_lag_s": 180},
        "long_drift": {"long_drift_dph": (3, -2, 4), "long_drift_period_s": 5400},
    }[name]


def rate_interval(k, n):
    if not n:
        return {"count": k, "n": 0, "rate": None, "ci95": None}
    return {"count": k, "n": n, "rate": k / n,
            "ci95": [0 if k == 0 else float(beta.ppf(.025, k, n-k+1)),
                     1 if k == n else float(beta.ppf(.975, k+1, n-k))]}


def summarize(records):
    groups = {}
    for r in records:
        key = (r["truth"], r["scenario"], r.get("sampling"), r.get("block"))
        groups.setdefault(key, []).append(r)
    out = []
    for key, rows in groups.items():
        analyzed = [r for r in rows if "rejected" in r]
        accepted = [r for r in analyzed if not r["exclusions"]]
        out.append({"truth": key[0], "scenario": key[1], "sampling": key[2], "block": key[3],
                    "attempted": len(rows), "analysis_failures": len(rows)-len(analyzed),
                    "eligibility_exclusions": len(analyzed)-len(accepted), "accepted": len(accepted),
                    "exclusion_reasons": dict(Counter(x for r in analyzed for x in r["exclusions"])),
                    "unconditional": rate_interval(sum(r["rejected"] for r in analyzed), len(analyzed)),
                    "conditional_on_acceptance": rate_interval(sum(r["rejected"] for r in accepted), len(accepted)),
                    "complete_gated_rule": rate_interval(sum(r["rejected"] for r in accepted), len(rows))})
    return out


def flight_run(truth, scenario, seed, sampling, block, boot, variant, same_side_up_turns=False):
    record = dict(truth=truth, scenario=scenario, seed=seed, sampling=sampling, block=block, variant=variant,
                  same_side_up_turns=same_side_up_turns)
    try:
        with tempfile.TemporaryDirectory(prefix="lll-research-") as d:
            p = Path(d) / "session.zip"
            opts = dict(fs=20., legs=((10, 30), (100, 30), (190, 30)), variant=variant)
            opts.update(scenario_options(scenario))
            if same_side_up_turns:
                opts["index_turns"] = ((20, "z"), (50, "z"), (80, "z"))
            synthesize(p, truth, seed=seed, omega_in_fn=geometric_truth(truth), **opts)
            r = analyze(p, fit_options={"n_boot": boot, "seed": seed, "bootstrap_sampling": sampling, "block_length": block})
        if not r.get("fit"):
            return {**record, "failure": "no fit", "flags": r["flags"]}
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
        return {**record, "rejected": f["rejected"][truth], "exclusions": reasons, "k": f["k"],
                "k_sd": f["k_sd"], "covariance": diagnostics, "convergence": f["convergence"],
                "prior_sensitivity": f["prior_sensitivity"], "identifiability": f["identifiability"],
                "wmm_shift_sigma": (r.get("fit_no_wmm_exclusion") or {}).get("k_shift_sigma"),
                "flags": r["flags"]}
    except Exception as exc:
        return {**record, "failure": repr(exc)}


def pooled_run(truth, seed, units):
    rng = np.random.default_rng(seed)
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
    return {"truth": truth, "scenario": f"pool-{units}-units", "seed": seed,
            "rejected": tests[truth]["rejected"], "exclusions": ["fewer than three units"] if units < 3 else [],
            "known_unit_covariance": U.tolist(), "marginal": marginal, "joint": joint}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenario", choices=SCENARIOS + ["all", "pool"], default="drift+0")
    ap.add_argument("--truth", choices=[*models.MODELS, "all"], default="sphere_rotating")
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--seed", type=int, default=10000)
    ap.add_argument("--bootstrap", type=int, default=100)
    ap.add_argument("--sampling", nargs="+", choices=["moving", "segment"], default=["moving", "segment"])
    ap.add_argument("--blocks", nargs="+", type=int, default=[5, 15, 30])
    ap.add_argument("--units", nargs="+", type=int, default=[2, 3, 5, 10, 30])
    ap.add_argument("--variant", choices=["spp", "ble"], default="spp")
    ap.add_argument("--same-side-up-turns", action="store_true", help="turn the mounted IMU at 20, 50 and 80 flight minutes")
    ap.add_argument("-o", type=Path, required=True)
    args = ap.parse_args()
    start, records = time.monotonic(), []
    truths = models.MODELS if args.truth == "all" else [args.truth]
    scenarios = SCENARIOS if args.scenario == "all" else [args.scenario]
    for truth in truths:
        for scenario in scenarios:
            for seed in range(args.seed, args.seed + args.seeds):
                if scenario == "pool":
                    records.extend(pooled_run(truth, seed, n) for n in args.units)
                else:
                    records.extend(flight_run(truth, scenario, seed, s, b, args.bootstrap, args.variant,
                                              args.same_side_up_turns)
                                   for s in args.sampling for b in args.blocks)
                args.o.write_text(json.dumps({"analysis_version": __version__, "policy_version": POLICY_VERSION,
                    "environment": environment(), "elapsed_s": time.monotonic()-start,
                    "simulation_assumption": "approved provenance and usable bench tier; remaining gates applied",
                    "summary": summarize(records), "records": records}, indent=2))
    print(f"{len(records)} runs in {time.monotonic()-start:.1f}s; {args.o}")


if __name__ == "__main__":
    main()
