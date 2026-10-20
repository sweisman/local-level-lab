# Preserve the common transform of changing force samples

The propagation observer points to a specific calculation term, not an
additional physical sensor error. This plan changes uncertainty accounting
while preserving every original physical candidate, calibration parameter,
bound, measurement and failure. No new aircraft fits follow from the plan.

## Common quantity

For the existing gain convention, let

\[
M(p)=R_0(p)\,\operatorname{diag}\left((1+g_x)^{-1},(1+g_y)^{-1},(1+g_z)^{-1}\right).
\]

The raw force difference is the current raw velocity increment divided by its
period, minus the corresponding first-packet quantity. Constant accelerometer
bias cancels from this difference. Its initial-frame contribution is
\(M(p)\,\Delta f_{\rm raw}(t)\), with the **same matrix at every epoch**.

For the existing midpoint factors, split the full force-difference action as

\[
Q R_0 P\,\Delta f
=(Q R_0 P-R_0)\,\Delta f+M(p)\,\Delta f_{\rm raw}.
\]

The first term retains the changing orientation. The second offers a common
matrix remainder that can be preserved across training and prediction times.
This is an algebraic identity, not an assumption that the aircraft is steady.

## Qualification sequence

1. Derive and implement a source-bound common-matrix component. Keep its centre,
   all 27 physical derivative columns and nine bounded matrix-error coordinates.
   Reuse the qualified rotation and reciprocal-gain bounds. Check units, signs,
   zero-error cases, boundary cases and an independent Rodrigues/calibration
   oracle before native use.
2. Derive the integrated cancellation before implementing a native candidate.
   Preserve the existing common acceleration term. A prospective velocity
   representation is initial velocity plus common acceleration times elapsed
   time, plus \(M\) acting on the accumulated raw force difference, plus a
   departure. Derive its exact midpoint update and position contribution;
   retain Coriolis, transport, gravity, lever and coordinate-metric terms.
3. Account explicitly for the common time offset in the raw-force integrals.
   A fixed-reference coefficient for the matrix error requires a bound on its
   clock-dependent departure. Do not treat packet fractions as independent or
   silently drop calibration/clock products.
4. Qualify a typed joint interface retaining the original 42 columns plus the
   nine common-matrix coordinates. Bind the fixed reference, domain, generated
   input and training inequalities. Auxiliary coordinates enclose errors; they
   are not additional physical choices at each epoch.
5. Only after component and native gates pass, run a separately frozen complete
   six-case/eight-sector comparison on the same 7.2-second inputs. Preserve
   unchanged physical bounds, known-truth retention, future-data separation,
   exact support certificates and failure records. Report full ranges honestly.

Each computational stage needs its own finite identities, evaluation allowance,
environment and four-thread allocation before launch. This prospective plan
creates no current run, retries, relaxed gates or recording-scale coverage claim.
Observed prediction work and protected ESA outcomes remain blocked by the
existing numerical and observational qualification requirements.

[Propagation diagnosis](../ilvis0-propagation-trace/INTERPRETATION.md) ·
[Current widths](../ilvis0-projected-future-bounds/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
