# Saved calibration-fit audit

Question: Do the completed generated fits recover the known sensor settings,
or do their nuisance estimates repeatedly approach permitted limits?

Read only the 36 sealed fits from the matched-candidate study. For each fit,
record all 26 normalized parameters, local singular values and near-bound
flags. For the twelve fits whose candidate matches the generating model,
compare the seventeen known sensor, lever-arm, gravity-adjustment and timing
settings with the generator's declared values, each divided by its existing
parameter half-range. Summarize boundary frequency and recovery error by
parameter. Keep mismatched candidates separate because their fitted nuisance
values may compensate for the wrong physical model.

This audit does not determine which parameter causes the wide forecast range,
validate the assumed bounds, narrow them, rerun a fit or make a scientific
Earth-model decision. It uses no observed or reserved aircraft data.
