# Deterministic multi-start software qualification

The horizontal-only IMU21 diagnosis finds differing locally stationary solutions,
not a gross timing-derivative fault. The next candidate retains the existing
ridge-probe solver and adds a fixed timing-start list. No score or physical
stopping threshold changes. Selection considers every attempt: if the lowest
returned cost belongs to an unfinished fit, the multi-start result is unfinished.

## Known answers

Use four bounded, four-column constructed least-squares systems. Their timing
cost is an asymmetric double well with a known algebraic minimum; a curved
calibration coordinate tracks timing. Include both well orientations, a true
timing optimum at the bound, and an exactly invisible nuisance coordinate.
Another coordinate has its unconstrained optimum outside the box. All columns
remain present, including the zero column. Expected minima are calculated from
polynomial stationary points and box endpoints, independently of the optimizer.

For each system use two independently fixed non-timing seeds, each with timing
starts **−0.8, 0, +0.8**: **24 starts /4,800 residual-tangent calls maximum**,
200 calls per start, four numerical threads, a **120-second wall ceiling**.
These are cheap constructed functions, not synthetic flights, native airborne
predictions or observed-data fits. Charge calls and starts before execution,
freeze sources/environment, preserve all outcomes, and never retry identities.

## Qualification

Both selected solutions per system must pass the unchanged fresh numerical
gate, agree with the independent best cost within 1e−8 relative to max(cost,1),
and agree with the known predicted residuals within 1e−5 absolute. The two best
solutions must also agree within the existing 1 mm axis-RMS /1 cm epoch-maximum
prediction limits. Individual local-well solutions and failures remain visible.
Do not require unique values of the invisible nuisance parameter.

A pass qualifies this start-selection mechanism only on these controls. It
does not establish global optimality, likelihood calibration or archive-wide
performance. Any observed test needs a separate source/input/environment freeze,
fixed starts and a finite allowance. The original 53-stretch findings stay fixed.
