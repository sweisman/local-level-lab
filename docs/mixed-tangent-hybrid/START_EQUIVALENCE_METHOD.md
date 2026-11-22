# Checking nearly tied optimizer starts

The faster calculation matches the established forecast on the opened ESA
development recording, but its original **exact start-choice gate failed** in
three of eight globe settings. That result remains failed. A new method must
show that changing between nearly tied training starts cannot change the
forecast in a meaningful way before the faster calculation can replace the
established one.

The [software comparator](../../analysis/lll/ilvis0_start_equivalence.py)
accepts two complete sets of fits made from the same training data. Its caller
must bind the exact training input and forecast time grid. It picks each
method's primary start by **training cost only**, with start number breaking
an exact tie. Given an explicitly supplied relative cost tolerance and a
forecast distance tolerance, it checks:

1. Every fit passed its own numerical gate; both methods used the same starts
   and bound input and forecast times.
2. Each start's training cost agrees between methods within the cost tolerance.
3. A changed primary start belongs to the near-minimum cost set in **both**
   methods.
4. **Every** near-minimum forecast from one method is close to **every**
   near-minimum forecast from the other at every future time. The comparison
   uses forecast-to-forecast distance, never the later receiver measurements.

Six deterministic checks cover a harmless start switch, a near tie with
different predictions, a material cost switch, a failed fit, changed bindings,
unequal forecast lengths, zero-cost behavior and invalid numerical values. These checks qualify
the helper's logic only. They do **not** set either tolerance, reclassify the
three saved disagreements, or qualify the faster method on aircraft data.

The [next generated study](START_EQUIVALENCE_STUDY_PLAN.md) fixes the cost
tolerance at the existing 1e-8 fit cost-change threshold and keeps the
existing 0.01 m forecast target. It tests both starts in every generated
model/processing setting. Only after that gate may a separately selected
development input test the revised rule. The original exact-start failure
and protected ESA confirmation groups remain unchanged.

[Saved start-cost audit](START_TIE_AUDIT.md) ·
[Original observed gate](../esa-observed-model-dispatch-v2/README.md).
