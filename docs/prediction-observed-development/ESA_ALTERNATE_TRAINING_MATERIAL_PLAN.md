# Freeze alternate receiver positions for training-only sensitivity

Use ESA development recording 187 only. Bind the same sealed 800-report
parent cut and the already hash-checked `air1`, `mosaic03` and `pwrpak7`
GNSS-only PPP exports. Read only the first 400 receiver epochs needed by
the matched ESA model matrix. Verify the original `air1` coordinates match
the sealed parent exactly. Time-match each alternate export within the
existing 2 ms rule, apply its reported velocity to align to `air1` time,
and change **only** latitude, longitude and height in a copy of each
training row. Keep `air1` velocity, quality fields and covariance unchanged
to isolate the effect of receiver-coordinate choice. Do not read or stage
later receiver positions for fitting.

Save both 400-row training alternatives with source and code hashes and
per-axis displacement summaries. This is input preparation, not a refit or
scientific result. Before any future fit, separately freeze the model,
settings, start/evaluation limits, technical recovery and the exact staged
training-input hashes. The seven reserved ESA groups remain closed.
