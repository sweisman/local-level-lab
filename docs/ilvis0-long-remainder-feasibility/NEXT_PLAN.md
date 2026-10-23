# Distinguish loose bounds from real ambiguity

The first four completed cases have smaller bounds, but still fail the original
width targets. Preserve the complete six-case comparison before this follow-up.

The next diagnostic will search for two calibrations that fit the **original
five perturbed observations** but predict substantially different later positions.
It uses generated data, not aircraft measurements or reserved ESA recordings.

## Fixed comparison

- Keep all three physical candidates and both upstream-processing assumptions.
- Keep every original input increment, all 27 calibration coordinates, their
  original bounds, the ±1-second clock range and the same coordinate frame.
- Retain the five training times, their ±1 m coordinate allowances and the
  438-second prediction endpoint. Do not substitute noiseless training positions.
- Start each search at the fixture's saved, nonzero calibration. Search once
  toward each north-coordinate extreme: twelve fixed identities altogether.
- Use the actual nonlinear native positions and Jacobians in a constrained
  search. A linear proposal alone cannot qualify a candidate. Leave 0.01 m of
  training margin during search; this restricts the search without changing the
  declared physical domain or observation problem.
- Save every new point before its native call, including rejected points and
  failed outputs. Cache repeated point requests; do not charge a cached lookup
  as a new native evaluation. All new evaluations are charged before execution.
- Preserve every attempted point. An optimizer's success label does not establish
  training feasibility, uniqueness, an optimum or useful prediction bounds.

## Qualification and limits

First test the search adapter against independent nonlinear known-answer controls,
including a boundary optimum, a misleading linear proposal and exhaustion of its
call allowance. Check all parameter columns and native batch/counter behavior on
a small generated history. Use the common library and study runner.

The proposed full-history allowance is **12 identities**, each with at most
32 search batches and one separately charged verification batch. Each batch
queries all five training epochs and the prediction epoch. Maximum totals are
396 native batches, 2,376 queried epochs and 228,096,000 conservatively charged
packet visits. There are no trajectory-enclosure calls or aircraft fits.

Freeze four one-thread workers, a one-hour cooperative study ceiling and a
30-minute per-identity ceiling before launch. Do not overlap this allocation with
the current study. No retries, process signals or allowance expansion.

The exact [saved-pair audit](../../analysis/lll/ilvis0_truth_probes.py) will check
source/configuration bindings, every physical bound, actual training errors and
future separation. Verify artifact hashes and native execution separately.
Reevaluate each selected candidate once within its fixed verification allowance.

## Interpretation

A separation beyond 20 m north, 20 m east or 50 m height establishes a lower
width for the represented native calculation only after both training matches
are checked. A physical impossibility claim also needs a qualified numerical
error bound with sufficient margin. The saved-pair audit does not supply that
bound or an aircraft error law.

Finding no such pair proves neither uniqueness nor useful outer uncertainty.
If real ambiguity is established, the next comparison should add predeclared
training information rather than tighten calibration assumptions or widen the
targets. Neither outcome changes the 53-stretch findings or authorizes aircraft
prediction fits.

[Current comparison](README.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).
