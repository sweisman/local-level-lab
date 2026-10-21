# Native qualification using the actual calibration box

The first integrated source study is complete and failed qualification at
18/24 controls. All six broad cases stopped at a nonlinear-cap check. Its
results and unused allowance remain preserved; this is a separate candidate
and finite study.

The diagnosis shows that the proof replaced the asymmetric bias/gain box with
a larger symmetric box. The revised proof retains the actual intervals,
including the reference point for the Taylor path. It leaves all physical
bounds, existing nonlinear caps, reference centers, rows and shared columns
unchanged. Local checks confirm the previously failed cap comparison and all
six model/processing native cases.

Run the same original 24 generated controls. Acceptance remains 1 micrometre
for reference/stationary predictions, 0.002 normalized derivative steps with
20 micrometres tolerance, and 10 micrometres numerical allowance for nonlinear
containment. Every registered control must complete and pass.

## Separate finite allowance

- 24 identities, no retries or optimizer starts.
- 78 full native evaluations and 19,632 native packet visits maximum.
- 348 complete enclosure bounds and 30,144 world/source bound steps maximum.
- Separately reserve at most 348 source setups, 7,536 compiled reference steps
  and 7,536 rounded body bounds before their enclosures run.
- Four single-thread workers; four total numerical threads.
- 60 seconds per bound, checked cooperatively; 600 seconds overall.

Freeze implementation, generated inputs, compiler and numerical environment.
Preserve failures and charges. No aircraft observations or protected ESA data
enter this qualification. A successful result permits a new prediction
comparison; it does not establish useful complete ranges or calibrated coverage.

[Preserved failed study](../ilvis0-source-native-controls/INTERPRETATION.md) ·
[Cap diagnosis](../ilvis0-source-native-controls/CAP_DIAGNOSIS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
