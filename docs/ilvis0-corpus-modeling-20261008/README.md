# Extending conditional modeling to the kept airborne corpus

The [six-file first pass](../ilvis0-exploratory-20261008/README.md) is complete.
All 24 fits produced finite results, but none converged within its evaluation
allowance. We preserve those outcomes and extend the investigation under a
separate source, data and numerical-environment freeze.

The inventory tracks **232 kept originals: 129 IMU6, 5 IMU8 and 98 IMU21 files**.
Each receives a fitted or unsupported outcome with its reason. No original is
deleted. Filenames and instrument streams do not necessarily represent independent
flights; overlapping streams and duplicate recordings must not be counted as
independent evidence.

For each file, select the longest complete interval supported by actual receiver
positions, capped at ten minutes, with earliest-time ties and at least one minute
of support. Selection uses packet status, timing, installation epochs and receiver
completeness, before any model-dependent residual. No interpolation or smoothing
of science measurements is introduced.

This is a **motion-model investigation**, including aircraft maneuvers and climb
where present. It does not reclassify those intervals as steady level flight or
alter the earlier level-flight screening gate. The raw IMU drives the predicted
motion; fused navigation remains outside the observations.

Each of the three Earth models profiles the same bias, gain, orientation, timing,
lever-arm and possible Earth-rate-removal assumptions as the first pass. Conversion
hypotheses are separately stated for IMU6, IMU8 and IMU21. Per-file agreement with
fused references and earlier failures remain decoder diagnostics; they do not
become independent calibration evidence. Unknown/mixed types, unsupported layouts,
time mappings or insufficient complete data yield an explicit abstention.

The initial solver spent most of its allowance rebuilding 27 nuisance derivatives.
The continuation reuses and updates that derivative matrix between steps, with
occasional fresh calculations. Before calling a fit converged, it recalculates
the actual derivatives at two steps and checks the freshly computed projected
gradient. A solver's own success flag alone is insufficient. Local rank and this
numerical tolerance are diagnostics, not statistical confidence or global-optimum
guarantees. The six prepared representatives are processed first.

The finite scope is three primary fits per file: at most 696 primary starts,
with 68 additional starts reserved for interruption recovery, a maximum of two
starts per file/model, and 200 total numerical evaluations per start. Every
interrupted start stays charged. At most two CPU threads are used. Unsupported
files consume no optimizer start. This is a separately authorized real-data
continuation, not a resumption or expansion of a synthetic campaign.

The worker writes hashed atomic per-fit and per-file results, a fsynced start
journal, a lock and live status. It rejects changed sources, inputs, compiler
artifact or environment on resume. Failed and unconverged fits remain visible.
It retains no extra corpus-wide raw CSV copies; the hashed compressed originals
and packet offsets support reproduction. The six-file native caches remain.

Eleven focused extension tests pass: numerical recovery and exact-gradient checking,
native/GPS-only extraction, truncation/hash rejection, distinct conversion scales,
orientation initialization, cached-result corruption and interrupted-start limits.
There is no calibrated model rejection, pooled winner claim or production promotion.

The first corpus worker stopped while writing its first fit because of a missing
import. Its source freeze and one charged start remain preserved. The repaired
worker uses a new freeze and carries that start forward, leaving at most 763 new
starts within the same 764-start aggregate ceiling. A result-writer regression
test and a carried-attempt-limit test cover the repair.

Run or resume only an unfinished worker after checking its status and process lock:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 /home/sweisman/venv/bin/python analysis/tests/ilvis0_corpus_modeling_worker.py --detach
```

Current output is in `data/ilvis0-corpus-modeling-v2-20261008/`; the log is
`data/ilvis0-corpus-modeling-v2-20261008.log`. The worker needs no network, credentials
or model calls. A completed study must stay frozen.

A separate lightweight watcher automatically audits the completed attempt ledger
and packages the human-readable results, per-fit/unsupported inventories and
provenance. It does no fitting. If the worker or watcher is interrupted, recovery
instructions are in `AGENTS.md`; packaging alone never requires repeating fits.
