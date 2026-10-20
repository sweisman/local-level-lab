# Preserve shared nonlinear reference errors

The saved constraint audit shows that further linear projection cannot repair
the retained nonlinear width. Build a separate mathematical enclosure that
preserves two common error vectors across all epochs. Keep the original physical
model, all 27 calibration directions and their bounds. No observed fits follow
from component tests.

## Initial velocity and the common clock

Track velocity changes from the uncertain initial velocity directly, rather
than subtracting two independently widened velocity bounds. The Cayley update
has the exact identity `(C(a)-I)v = -2 (I+[a]x)^-1 (a x v)`, permitting an
incremental-velocity recurrence with the existing bounded primitives.

Use a fixed initial coordinate metric. Split coordinate rates into that metric
times the uncertain initial velocity, a term for velocity change and a term for
metric change. Combine the reference velocity with the correlated prefix clock.
Its nonlinear product contains one shared physical vector

`gamma_v = delta_initial_velocity * delta_time_offset`.

Bound it componentwise from the original domain and represent it once, with the
appropriate known metric/time-slope coefficient at each epoch. Keep all remaining
clock error, dynamic motion, metric variation and cross terms. Internal state
bounds must include the full shared error; only the final factored observation
may separate it from the unshared remainder.

## Initial lever and attitude

For the initial body-to-navigation rotation `R0` and lever `L`, define

`gamma_L = R0(p)L(p) - R0(c)L(c) - D(R0 L)_c (p-c)`.

The existing rotation/lever bounds supply a common vector-radius bound. A zero
lever expansion center is allowed without setting the actual lever to zero:
the complete original lever domain remains. Nonzero centers need the full
derivative and bound, not a zero-center shortcut.

Separate `Rt L = R0 L + (Rt-R0)L`. Bound the latter as genuine motion: rotation
product telescoping bounds `||Rt-R0||` by accumulated body/navigation angular
motion, capped at two. The geographic metric's uncertainty and the first-order
lever contribution must remain in the dynamic remainder. It is invalid simply
to subtract the old initial-lever radius from a completed total bound.

## Joint representation and gates

One joint expansion definition binds the shared vectors to all epochs. Retain
the original 27 columns plus six bounded auxiliary error coordinates. Coefficients
may change with known metric/time slopes; the underlying shared variables cannot
be independently reselected per epoch. Zero or unidentified columns stay present.
An inconsistent binding or missing shared block must abstain.

First test the exact product/rotation decomposition and its bounds, including
nonzero centers and actual nonzero levers. Then connect it to a new native
candidate, preserving all field, transport, calibration and packet-boundary
terms. Qualify all candidates/processing cases against the unchanged engine and
independent known-motion controls. Save every native/Jacobian, shared binding,
inequality, error contribution and certificate. Future truth is unavailable to
the enclosure/region calculation.

Freeze a separate finite source/input/environment/call allowance before any new
study. Keep at most four numerical threads; no retries, expansions or signals.
A native qualification and a distinct usefulness comparison precede any
observed prediction work. Global numerical treatment, actual receiver-error
adequacy and independent confirmation remain additional gates. Existing data,
completed results and protected ESA groups remain untouched.

[Saved constraint outcome](../ilvis0-regrouped-constraint-audit/INTERPRETATION.md) ·
[Native decomposition](NATIVE_DECOMPOSITION.md) ·
[Canonical roadmap](../ANALYSIS_ROADMAP.md).
