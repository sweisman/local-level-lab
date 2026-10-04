# SPDX-License-Identifier: AGPL-3.0-or-later
"""Coverage study: do the per-flight intervals and model tests mean what they say?

    python analysis/tests/coverage.py [seeds] > coverage.md

For each truth and seed, a north-east-south flight with every hardware fault at once
(test_analysis.HARDWARE_FAULTS) is synthesized from geometric truth and analysed. The output is
the fraction of 95 % intervals (k ± 1.96 σ) that contain the true k, per term, and how often the
true model is rejected at 3σ (nominal 0.27 %). Not run in CI: about 15 minutes for 30 seeds.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from conftest import geometric_truth  # noqa: E402
from lll import models  # noqa: E402
from lll.analyze import analyze  # noqa: E402
from lll.fit import TERM_NAMES  # noqa: E402
from lll.synth import synthesize  # noqa: E402
from test_analysis import HARDWARE_FAULTS, NES_LEGS  # noqa: E402


def study(seeds=30):
    tmp = Path(tempfile.mkdtemp(prefix="lll-coverage-"))
    hits = {n: 0 for n in TERM_NAMES}
    total = {n: 0 for n in TERM_NAMES}
    rejected, runs = 0, 0
    worst = {n: [] for n in TERM_NAMES}
    for truth in models.MODELS:
        for seed in range(100, 100 + seeds):
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
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    hits, total, rejected, runs, worst = study(seeds)
    print(f"Coverage under every hardware fault at once: {runs} flights ({seeds} seeds × {len(models.MODELS)} truths).\n")
    print("| term | 95 % interval covers the truth | 95th percentile of |k − true| / σ |")
    print("|---|---|---|")
    for n in TERM_NAMES:
        print(f"| {n} | {100 * hits[n] / total[n]:.0f} % | {np.percentile(worst[n], 95):.2f} |")
    print(f"\nTrue model rejected at 3σ: {rejected} of {runs} flights (nominal 0.27 %).")
