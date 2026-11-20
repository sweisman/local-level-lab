# Does the opened-flight forecast ranking depend on the PPP export?

Use the already sealed 400-training/120-later ESA development matrix. The
model fits and primary starts remain chosen from `air1` training observations
alone. Reuse only its two complete, previously reported settings. Read no
IMU original, perform no fit or native forecast, and leave the two incomplete
settings unresolved.

Hash-check the saved model artifacts, the parent `air1` 520-report cut, and
the completed full-flight PPP comparison. Match those 120 later `air1`
reports exactly to the raw `air1` export. Strictly parse the `mosaic03` and
`pwrpak7` PPP exports with the previously verified single printed-counter
rollover, match within 2 ms and apply the existing first-order velocity/time
correction. Use only epochs common to all three exports so every physical
candidate and PPP source is scored on the **same** withheld times. Require
at least 100 common reports; otherwise preserve a failed diagnostic.

Report north/east/up, horizontal and total RMS for each selected forecast
against each PPP export, then the lower-error globe/flat family and the
specified/zero-field ordering conditional on globe. Preserve the original
`air1` score and all source/artifact hashes. The fixed physical accuracy
screen remains a separate descriptive flag; no statistical threshold is
introduced.

This tests robustness to PPP processing choice on one already opened flight.
The exports share an antenna and geodetic coordinate convention, so their
agreement cannot establish absolute geometry or scientific independence.
The 120-report horizon was originally chosen after earlier development
results; this is not confirmation or calibrated detection. One local thread,
no protected ESA group reads.
