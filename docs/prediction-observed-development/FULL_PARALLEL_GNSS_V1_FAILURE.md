# First full-flight parallel receiver attempt

The [original fixed plan](FULL_PARALLEL_GNSS_PLAN.md) rejected a
non-increasing printed receiver sequence while parsing the `mosaic03` PPP
export. The run stopped before writing a comparison. It made zero Earth-model
fits and read no reserved ESA flight.

Inspection of the unchanged source found exactly one transition, at source
line 100,050: printed sequence `00099999` at GPS time 403978.60015225 s is
followed by `00000000` at 403978.80015206 s, in the same GPS week. The
times continue forward by about 0.2 s. All 160,134 printed `mosaic03`
records otherwise have increasing sequence/time. This is consistent with a
five-digit sequence counter rolling over inside an eight-character field;
the initial strict parser has no rule for that transition.

The failed method's code SHA-256 is
`87a7dadfbcabd46820bdf8ce1556809b43650b8e11d0cc4a358155c18c1dd95f`;
its plan SHA-256 is
`e14f3bc61b0c31ea09d2bc70dc98119ca5e28d7a238bf21c9eed287a20d6e6fb`.
The original `mosaic03` SHA-256 is
`e6706cbe2971c25dc07d03446d8a77b9a48f673be0d967d1a8a11de59578555d`.
The strict-parser failure remains the outcome of this attempt. A separate
method must explicitly validate the counter rollover before comparison.
