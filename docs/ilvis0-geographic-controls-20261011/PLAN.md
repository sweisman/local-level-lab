# Geographic fitter controls

This is a bounded software qualification, using no NASA measurements or observed fit
starts. Existing studies, calibration bounds and production evidence rules stay frozen.

Generate six independent 12-second controls at 200 Hz: rotating globe, still globe
and stationary disc, each with either constant periods and interior calibration or
known variable periods and near-boundary calibration. All tracks move east at 220 m/s
at the equator, at 1,000 m altitude. Prescribed body yaw and pitch vary continuously.
Integrate analytic body angular rate and specific force with eight-point Gaussian
quadrature. Generate receiver positions directly from the analytic trajectory at
24 independently specified epochs, including latency. Do not generate observations
with either production predictor. Finite-interval integration error remains explicit.

Release six parameters: initial pitch, initial east velocity, Z gyro offset and gain,
gravity correction and receiver latency. Fix the remaining calibration and upstream
processing parameters at their known synthetic values. These are injected software
controls, not claims about NASA instrument specifications or all 27 archival parameters.

For each fixture check the native value predictor, automatic derivatives and separate
finite differences and a whitened tangent check (15 native sweeps). Compare the original shape solver and the
verified-stop candidate from zero and opposed starts. There are exactly 24 fit
identities, no retries, at most 200 sweeps per identity including two final value
checks: at most 4,800 fit sweeps plus 90 fixture checks. Use two numerical threads.

Record convergence, objective, prediction error, returned parameters, boundaries,
conditioning and every start. Interrupted identities remain charged. Preserve failed
results. Never rerun a completed report to improve its success count; packaging uses
saved results only. Source, native builds, environment and this plan are hashed before
the first fit. No new observed-data budget is created.

Each fit must converge, predict the independent track within 2 mm, and reach a
whitened objective no more than 0.01 above the known-parameter reference. The covariance
uses a common 1 cm synthetic position scale, with no added random noise. This is a
numerical control tolerance, not a calibrated scientific detection. Parameter error
is reported separately; satisfactory predictions do not establish unique calibration.

Passing qualifies only this six-parameter, equatorial, short-record observation path.
Long-record conditioning, all nuisance directions, joint gain–bias profiles and
held-out independent flights remain separate work. It does not choose the real NASA
increment clock or resolve the unfinished observed stopping-rule trial.
