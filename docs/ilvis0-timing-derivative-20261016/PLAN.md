# Fixed-endpoint timing diagnostic

The failed primary and repeat for stretch `fd7b81e48a4122b149c4925b`
have almost identical objectives but reject their local corrections. The
[saved audit](../ilvis0-final-stability-audit-20261015/INTERPRETATION.md)
identifies time alignment as the largest normalized correction coordinate.
This study checks that direction before another recovery fit.

The scope is fixed before native predictions:

- The earlier matched trial's failed primary and repeat, under profiled removal
  and the zero-background globe model.
- Its first completed control: `233183f67270980491416678`, unsubtracted increments,
  specified-background globe. The control is selected by the prior task order.
- Three endpoints, **34 native tangent calls maximum**, **zero optimizer starts**,
  no retries, one worker with four numerical threads. The control has ten calls;
  each failed endpoint has twelve. Failed or interrupted calls remain charged.
- Two identical center evaluations per endpoint, followed by symmetric time-offset
  perturbations of **0.1 microseconds, 10 microseconds, 1 millisecond and
  4 milliseconds**. Every other fitted parameter stays fixed.
- For the failed pair only, evaluate the full and half coupled correction from
  the saved original BVLS audit. No local solve is repeated.

Compare analytic, centered, left and right derivatives in physical position units.
Report per-axis errors, signed actual and linearized objective changes, changed
packet indices and distances to the nearest packet boundary. Branch indices use
the native kernel's left-interval convention and cumulative nominal intervals.
The smallest steps may encounter floating-point subtraction limits; larger steps
can cross intervals with different measured increments. Distinguish those effects
from a wrong derivative rather than declaring every discrepancy a defect.

Keep original increments, nominal clock, weights, physical models, calibration
bounds, wider arithmetic and all stopping limits unchanged. Hash original files,
selected endpoints, audit corrections, sources and numerical environment before
launch. Verify extraction provenance and reproduction of the saved central cost.
Atomic results, pre-call journals and exclusive locks support interruption-safe
continuation of unstarted identities. Completed work cannot restart.

Expected cost is tens of minutes at recent native-evaluation speeds. This is a
numerical diagnostic, not another fit, a revised scientific gate or permission to
relabel any stretch. Results determine whether a separate solver change is justified.
