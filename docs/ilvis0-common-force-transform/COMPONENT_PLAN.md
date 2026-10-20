# Common force-transform component qualification

For each matrix column, reuse the qualified rotation Taylor bound and the
qualified reciprocal-gain bound applied to that column's unit basis vector.
For centre values \(R_c,d_c\), changes \(\Delta_R,\Delta_d\) and first-order
remainders \(r_R,r_d\), the product remainder is bounded by
\(\lVert R_c\rVert r_d+r_R\lVert d_c\rVert+\Delta_R\Delta_d\).
This follows by expanding the product and retaining its complete cross term.
A column-norm bound also bounds every entry in that column.

Store the nine entrywise remainder caps, all 27 physical derivative columns
and a binding to the complete reference. A fixed known force-integral vector
maps these same nine errors into three output coordinates; it does not create
fresh errors at later epochs. The augmented design must retain 51 columns.
Clock-dependent integrals and native propagation are explicitly unqualified.

Freeze 24 generated controls: six source configurations, each under full,
sector-4, fixed-point and reciprocal-gain-boundary domains. The boundary control
uses a synthetic gain limit of 0.9 solely to test the mathematics; it changes
no aircraft bound or candidate. Use 64 predefined/bounded probes per control,
54 independent derivative-oracle evaluations and four weighted-map identities
per probe. Totals: 1,536 probes, 1,296 derivative evaluations and 6,144 maps.

Acceptance: independent Rodrigues/reciprocal-gain agreement within 3e-13,
weighted-map identity within 3e-12, all 27 finite-difference columns within
3e-10 using step 2e-6, normalized remainders at most 1+1e-11, and complete
51-column augmentation. Include exact fixed-domain zero caps and source mismatch
rejection in local tests. Reused Taylor bounds supply the domain argument;
finite probes are regression checks, not proof of arbitrary observational error.

Record all starts and reserve checks before calculation. Four workers use one
thread each with 90 cooperative seconds, zero native calls, zero native bounds,
no archive reads, fits, retries, signals or extensions. Passing the component
does not authorize native use or aircraft predictions.
