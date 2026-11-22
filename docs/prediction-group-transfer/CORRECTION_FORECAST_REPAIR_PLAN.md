# Native-source repair for the three forecast-sensitivity cases

The first frozen study ended with three sealed technical failures and **zero**
native calls. Its source closure omitted `ilvis0_native.c`, so each worker
stopped before calculation. Keep that result unchanged. This separately
qualified v2 study repeats the same three preselected diagnostic cases,
training inputs, prediction-only comparison, one-call-per-case limits and
three one-thread allocation defined in
[the original plan](CORRECTION_FORECAST_PLAN.md). It adds the C and C++
translation units explicitly to the frozen source closure, with a test that
fails when either is missing. No receiver positions from the later interval
are staged or read. This is still a numerical-path diagnostic, not a new
Earth-model decision.

The initial v2 allowance is three native calls, with packet-visit ceilings
set from the three sealed layouts and a one-hour cooperative wall limit.
The existing five-test, source-bound task-recovery qualification must match
current bytes before launch. If a reboot interrupts v2, verify all leases
have exited, close it terminally, and prepare a separate continuation with
at most two charged attempts per task across v2 and its continuation, at
most three technical interruptions, one further hour and a 5 GiB free-space
floor. Never rerun a sealed technical or numerical result. Keep original
and repaired outcomes separately in the public study index.
