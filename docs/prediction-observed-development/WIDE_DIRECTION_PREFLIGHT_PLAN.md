# Check a wider forecast test on separate route controls

Use the twelve saved generated histories as donors. Use the separately
archived straight and turning level routes as targets. Those two target
routes share one seed, which is absent from every donor. Do not fit again
or read their later receiver observations.

For each of the four working covariance assumptions, construct unit
directions from each donor's two forecast differences from the
specified-field globe. Learn spaces of at most 2, 4, 8, 12 and 24
directions by taking the leading singular vectors of those donors.
Work in the target covariance metric and check both the full paths and
paths allowing a separate cubic error for each model. Keep every width.

For each target model pair, report the squared distance retained in the
donor space and the ideal Gaussian power of an upper-tail squared-error
test. Use an illustrative 1% test size and 80% power requirement for all
pairs across routes and covariance assumptions. Also report the oracle
one-direction power with the exact pair of means, to distinguish poor
transfer from inherently weak fixed-path separation. These figures
assume a known correctly specified covariance and exact target
forecast means. They do not select a confirmation policy.

Allow one thread, 56 covariance operators and 80 width comparisons.
Allow no fits, native calls, new draws, later observations or protected
flight reads.
