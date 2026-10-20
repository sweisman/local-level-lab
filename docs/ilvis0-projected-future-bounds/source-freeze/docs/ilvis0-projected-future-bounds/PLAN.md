# Recompute future bounds after certified coordinate projection

The complete longer comparison and saved certificate audit pass all 48 cases.
Exact coordinate projection tightens initial velocity, initial position and
three auxiliary acceleration-error coordinates. This study measures whether
those changes improve the complete future ranges before any longer native run.

Keep all six candidate/processing cases, eight original orientation sectors,
1,600-packet generated inputs, fixed reference expansion, original physical
bounds and all 42 columns. Reuse saved training constraints, future native values
and all 27 native derivatives. Independently recompute only the future nonlinear
bound at 7.2 seconds. The physical bound domain must contain both the certified
projected physical box and the original expansion point; its hull must remain
inside the earlier domain. Do not change reference caps or bindings.

Use the qualified joint support method on the full projected 42-coordinate box.
Keep the exact certificates and compare raw new ranges against the saved ranges;
do not hide unchanged or wider outcomes. Check known-control retention and
future containment where the known truth belongs to the sector. Native/bound
central values must still agree within 1 micrometre. This measures usefulness
of an existing conservative construction, not actual aircraft error.

Freeze 48 identities, one bound and six LP proposals per identity: 48 bounds,
76,800 reserved packet steps, 288 LP proposals and at most 576 support
certificates. Charge/reserve before operations. No new native integration calls,
original-file reads, observed fits or retries. Four workers use one thread each;
allow 1,800 cooperative seconds overall and 120 per bound. Expected runtime is
roughly 6–10 minutes from the preceding comparison, with no signals or extension.

Preserve every outcome. Further recording-scale expansion requires a documented
usefulness assessment, adequate numerical treatment and observational error
qualification; this trial does not authorize aircraft prediction fits.
