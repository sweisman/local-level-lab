# Averaging the paired gyroscope differences

The selected NASA archive has twelve pairs of simultaneously recorded, closely matching flight stretches. This saved-data diagnostic asks whether their **between-recorder gyro-rate differences** shrink when complete common UTC-second bins are averaged into longer windows. It does not refit an Earth model or read the original recordings.

Inputs are the already published twelve-pair CSV and the 24 per-stretch cache files from the verified position-stability snapshot. Verify every cache hash against its frozen receipt before calculation. Use only the selected common complete UTC seconds inside each pair's published overlap. Convert the saved aircraft-axis rates from radians/second to degrees/hour, subtract right from left and average nonoverlapping windows of exactly 1, 10, 30 and 60 seconds, anchored at the first common complete second. Do not interpolate gaps or choose window boundaries from gyro values. Preserve all twelve pairs and the three premarked priority pairs.

Report per axis and window length: number of complete windows, signed mean difference, RMS difference, and the original pair type. The one-second output must reproduce the published paired CSV within rounding tolerance. Longer windows describe time-scale behavior; they do **not** identify intrinsic sensor noise because mounting, timing, processing and real aircraft motion can differ between recorders. Same-track candidates are not verified independent flights.

This is a read-only report from frozen descriptive caches, with zero fits and zero native calls. It can identify whether a more detailed paired-calibration study is promising. It cannot set the ESA instrument's error law or calibrate Earth-model significance.
