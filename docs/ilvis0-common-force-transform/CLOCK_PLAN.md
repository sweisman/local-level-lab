# Common clock and integrated raw-force differences

This stage qualifies supplied binary force coefficients as a mathematical
piecewise-constant integration map. It does not certify complete floating-point
execution, change packet timestamps or interpolate scientific measurements.

For period \(d_i\), binary accumulated tag \(s_i\), and one query time \(t\),
write \(q_i(t)=\operatorname{clip}(t-s_i,0,d_i)\). The native midpoint form for
the raw-force contribution has the recurrence

\[
G_i=G_{i-1}+f_iq_i,\qquad
H_i=H_{i-1}+q_i(G_{i-1}+f_iq_i/2).
\]

Here \(f_i\) is the supplied three-axis raw force difference. The same \(t\)
controls every packet. Exact rational evaluation preserves binary coefficients.
An independent suffix-weight formula checks the recurrence:

\[
H=\sum_i f_iq_i\left(q_i/2+\sum_{j>i}q_j\right).
\]

## Packet-tag defect

Let \(T_i=\sum_{j<i}d_j\) be exact contiguous starts and let
\(D=\max_i|s_i-T_i|\). Monotonicity gives
\(Q_i(t-D)\le q_i(t)\le Q_i(t+D)\), where \(Q_i\) uses \(T_i\).
Consequently \(\sum_i|q_i-Q_i|\le2D\). This keeps a single clock defect;
it does not multiply a worst timing error by the number of packets.

If \(F_a\) bounds the absolute force on axis \(a\), then
\(|G_a-G_a^{\rm ideal}|\le2DF_a\). For the quadratic functional \(H\),
\(|\partial H_a/\partial q_i|\le F_a\sum_jq_j\). Along the segment joining
the two clipped-period vectors, this yields
\(|H_a-H_a^{\rm ideal}|\le2DF_a\min(P,t+D)\), with total duration \(P\).

## Common-clock remainder

Compute the actual and ideal centre integrals exactly. For radius \(r\), use
the force variation over the whole query interval to bound the first-order
remainder of \(G\). The ideal \(H\) remainder is at most
\(\tfrac12 r^2\max|f_a|\). Add the global tag-defect allowance, the exact
centre discrepancy, and the centre-velocity discrepancy times \(r\).
A point clock domain has exactly zero variable-clock remainder.

For the matrix-weighted term, preserve

\[
M H(t)=M_cH_c+J_M\delta p\,H_c+M_cH'_c\delta t
+E_MH_c+(M-M_c)H'_c\delta t+M E_H.
\]

Only \(E_MH_c\) becomes the nine fixed shared matrix-error coordinates.
The last two terms require explicit global bounds. Rounding of centre,
derivative and shared coefficients must also be included when exact rational
coefficients are exported as binary floats. Preserve all 27 physical columns.

## Gates

Local controls cover exact constant-force answers, independent suffix
quadrature, changing coefficients, rounded tags, point domains, invalid inputs
and finite resource failures. A separately frozen component qualification must
then check the weighted identity with an independent rotation/gain oracle.
Native midpoint cancellation and the typed 51-column prediction interface
remain later gates. No observed fits or campaign allowance is created here.
