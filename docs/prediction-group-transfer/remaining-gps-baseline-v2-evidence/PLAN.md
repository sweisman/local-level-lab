# Correct the GPS baseline work ledger call

The [original freeze](REMAINING_GPS_BASELINE_PLAN.md) ended before evaluating
any of the 40 forecasts. The worker omitted the required `bound_steps`
field when charging for an extrapolation. All 40 sealed failure records
and task identities are preserved. The accounting regression exercises
the actual task-context charge implementation and reproduces the failure
with the original call.

Use the original frozen training and scoring bytes and its 40 task
definitions. The corrected call charges one operation with zero bound
steps. The original forecast, comparison and scoring rules are unchanged.
Use a fresh source and environment freeze, one thread and a 120-second
cooperative limit. Start no inertial fits and read no further recordings.
