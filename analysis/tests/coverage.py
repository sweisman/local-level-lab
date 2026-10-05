# SPDX-License-Identifier: AGPL-3.0-or-later
"""Coverage study: do the per-flight intervals and model tests mean what they say?

    python analysis/tests/coverage.py [seeds] > coverage.md
    python analysis/tests/coverage.py --null N [--workers W]

For each truth and seed, a north-east-south flight with every hardware fault at once
(test_analysis.HARDWARE_FAULTS) is synthesized from geometric truth and analysed. The output is
the fraction of 95 % intervals (k ± 1.96 σ) that contain the true k, per term, and how often the
true model is rejected at the nominal 3σ threshold (0.27 %). Not run in CI: about 15 minutes for 30
seeds.

--null runs only the false-rejection study, N flights per truth in parallel, and reports the empirical
rate with a Clopper–Pearson interval. Zero rejections in 90 flights only bounds the rate below about
4.0 % (two-sided 95 %); showing it is near 0.27 % needs thousands of flights, so this is run offline (about
10 s per flight per core).
"""
from __future__ import annotations

import sys
import tempfile
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from conftest import geometric_truth  # noqa: E402
from lll import models  # noqa: E402
from lll.analyze import analyze  # noqa: E402
from lll.fit import TERM_NAMES  # noqa: E402
from lll.synth import synthesize  # noqa: E402
from test_analysis import HARDWARE_FAULTS, NES_LEGS  # noqa: E402


def clopper_pearson(k, n, conf=0.95):
    from scipy.stats import beta
    a = (1 - conf) / 2
    lo = 0.0 if k == 0 else float(beta.ppf(a, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - a, k + 1, n - k))
    return lo, hi


def _null_one(args):
    truth, seed = args
    from research import flight_run
    return flight_run(truth, "hardware", seed, "moving", 30, 300, "spp")


def null_study(n, workers=None):
    from research import summarize
    from lll.research_design import seed_range
    jobs = [(truth, seed) for truth in models.MODELS for seed in seed_range("development", 10_000, n)]
    with Pool(workers) as pool:
        out = list(pool.imap_unordered(_null_one, jobs, chunksize=4))
    return {"partition": "development", "validation_evidence": False, "summary": summarize(out), "records": out}


def study(seeds=30):
    from lll.research_design import seed_range
    campaign_seeds = seed_range("development", 100, seeds)
    tmp = Path(tempfile.mkdtemp(prefix="lll-coverage-"))
    hits = {n: 0 for n in TERM_NAMES}
    total = {n: 0 for n in TERM_NAMES}
    rejected, runs = 0, 0
    worst = {n: [] for n in TERM_NAMES}
    for truth in models.MODELS:
        for seed in campaign_seeds:
            p = tmp / "s.zip"
            synthesize(p, truth, seed=seed, fs=20.0, legs=NES_LEGS, omega_in_fn=geometric_truth(truth), **HARDWARE_FAULTS)
            f = analyze(p).get("fit")
            if not f:
                continue
            runs += 1
            rejected += bool(f["rejected"][truth])
            for n, e in zip(TERM_NAMES, models.EXPECTED_K[truth]):
                z = abs(f["k"][n] - e) / f["k_sd"][n]
                total[n] += 1
                hits[n] += z <= 1.96
                worst[n].append(z)
    return hits, total, rejected, runs, worst


if __name__ == "__main__":
    if "--partition" in sys.argv or "--manifest" in sys.argv:
        # Modern partitioned coverage uses the same enforced manifest and complete gate.
        from research import main
        main()
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--null":
        n = int(sys.argv[2])
        workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else None
        import json
        print(json.dumps(null_study(n, workers), indent=2))
        sys.exit(0)
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    hits, total, rejected, runs, worst = study(seeds)
    print(f"Coverage under every hardware fault at once: {runs} flights ({seeds} seeds × {len(models.MODELS)} truths).\n")
    print("| term | 95 % interval covers the truth | 95th percentile of |k − true| / σ |")
    print("|---|---|---|")
    for n in TERM_NAMES:
        print(f"| {n} | {100 * hits[n] / total[n]:.0f} % | {np.percentile(worst[n], 95):.2f} |")
    lo, hi = clopper_pearson(rejected, runs)
    print(f"\nTrue model rejected at the nominal 3σ threshold: {rejected} of {runs} flights "
          f"(95 % Clopper–Pearson upper bound {100 * hi:.1f} %; nominal 0.27 %). This many flights can't "
          "resolve a 0.27 % rate: see --null.")
