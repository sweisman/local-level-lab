# Which parts of the saved forecasts distinguish the models?

Use all four settings from the opened ESA development flight. Select
passing starts by the already declared earlier training criterion.
Keep both incomplete settings visible. On the two complete settings,
compare the three sealed pairs of 120-report forecasts under both
drift laws and both receiver weightings. Read only earlier receiver
weights and the forecast paths saved before scoring.

For each pair, calculate the distance in the full conditional covariance
metric. Then project out separate constant, linear, quadratic and
cubic position changes in each model. Reuse the checked smooth-error
projection. This measures how much of the contrast would survive if
each model had those unknown mean discrepancies.

Report ideal one-sided Gaussian power at an illustrative 1% test size
and the largest common variance multiplier that could still yield
80% power. Both figures assume the stated covariance and exact candidate
means outside the declared nuisance subspace. They provide a benchmark
for the planned calibration, without estimating real-aircraft power or
choosing a confirmation cutoff.

Allow one thread, four structured covariance operators, 24 pair
comparisons and zero fits, later receiver observations or protected
flight reads.
