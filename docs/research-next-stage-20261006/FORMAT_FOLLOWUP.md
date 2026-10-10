# Resolving the airborne gyro format

**Current findings:** the completed 53-stretch study favors globe in 12 stretches and
flat in none; all 12 also favor rotation. Another 41 comparisons lack finished calculations.
See the [findings](../ilvis0-highspeed-segments-20261008/FINDINGS.md). The six-recording
pilot is complete, and a [matched solver trial](../ilvis0-solver-trial-20261010/README.md)
is running. The format investigation below preserves the development history.


The initial inspection preserved the supplied Applanix log with timing, GPS and an opaque
24-byte IMU8 payload. On 7 October 2026, a separate numerical validation reproduced its
interpretation as six signed little-endian int32 increments: velocity X/Y/Z and angle X/Y/Z.
Independently estimated scales support `2^-14 m/s/count` and `2^-18 rad/count`, with expected
axis order/signs and chronological holdout checks. Rates use actual adjacent timestamps;
gaps and configuration changes never become silently interpolated observations.

The [validation record](../ilvis0-physical-validation-20261007/README.md) reports the
comparisons against Group-1 fused navigation, including shared body-frame gravity for
accelerometer checks. Group 1 is a decoder reference, not an independent Earth observable.
No authoritative manufacturer scale table has been found. Calibration/corrections, exact
mounting, lever arms and physical latency remain unresolved.

A later [IMU6 installation/clock investigation](../ilvis0-installation-clock-20261007/README.md)
reproduces changed axes from logged legacy setting candidates. Its earlier vertical mismatch
largely disappears when increments are normalized by a fixed 200 Hz period rather than
fluctuating header intervals. All six acceleration checks pass under that explicit hypothesis;
one gyro holdout narrowly fails. This finding is specific to these IMU6 records and does not
replace the IMU8 timestamp convention above. Both rate normalizations and the original
failure reports are preserved. Integration-clock semantics and processing independence
remain unresolved; no automatic corpus conversion is enabled.

The subsequent [observation feasibility check](../ilvis0-observation-20261007/README.md)
preserves increment sums and both clock hypotheses independently of fused gyro/attitude.
All six source/timing audits pass, but none contains the separately documented direct-output
Group10002. That absence does not determine Group4 correction status. The next scientific
step is a joint raw-increment/GPS motion model with defensible calibration and bias bounds,
not substituting the fused navigation result for the independent observation.

The [forward-model preparation](../ilvis0-forward-20261007/README.md) now implements those
declared model equations and preserves finite-rotation/specific-force effects from the native
packets. It keeps both clock hypotheses, real receiver endpoint offsets, and prior failures.
The [bounded estimator](../ilvis0-estimator-20261007/README.md) subsequently passes analytic
recovery controls and exposes orientation/acceleration-bias ambiguity. It requires explicit
bounds, common receiver-coordinate covariance and timing support, and counts numerical
derivative calls against its budget. The local pairwise profiles are software diagnostics,
not calibrated empirical decisions. Recorded corrections and supported instrument constraints
remain open; no Earth fit ran.

A [receiver/processing follow-up](../ilvis0-processing-v2-20261007/README.md) then decoded
GSOF position/time/sigma records and reassembled RT17/RT27 survey envelopes inside Group10001.
The GPS products reproduce dated sentences and expose receiver-reported uncertainty; raw
satellite measurements were still opaque at that stage. ACK/NAK responses are explicitly recognized.
Two unfinished receiver tails remain rejected without repair, although all outer Applanix
frames are valid. Unknown legacy messages and correction semantics remain preserved rather
than assigned modern meanings. No new scientific eligibility or Earth result follows.

The subsequent [satellite decoder](../ilvis0-gnss-v2-20261007/README.md) independently
reproduces the complete receiver-record sequence while converting RT17/RT27 ranges,
phases, available Doppler, flags and GPS ephemerides. Dates and 2,968 shared GPS epochs
match prior reports. Of 29,567 coarse sky-angle comparisons, 29 flag zero-angle reports
for one satellite; no ranges are repaired or omitted. RT17 filtered-correction flags
are kept distinct from RT27 smoothing flags. GLONASS/ionosphere packets stayed opaque
at that stage. Both decoder passes remain separately frozen.

A separately frozen [positioning stage](../ilvis0-position-20261007/README.md) now decodes
the recorded ionosphere/UTC coefficient packets and reconstructs GPS-only code positions.
All 5,936 primary solves and 24 alternate-start checks converge at the same 2,968 selected
epochs. Satellite clocks, signal time and atmosphere are explicitly modeled. This does
not change the old decoder snapshots or add GLONASS orbit support. Same-receiver position
differences show temporal correlation and persistent method offsets; formal covariance
still lacks independent calibration. No observed Earth fit or gate change ran.

The subsequent [GPS sensitivity analysis](../ilvis0-gps-sensitivity-20261007/README.md)
retains cross-axis and temporal covariance under thirteen fixed error assumptions, including
constant offsets and drift. It evaluates all supported fixed 2/6/12/30/60-second windows
without interpolation or selecting a smoothing interval. Assumed scales are not measured
bounds. Short-motion controls demonstrate that a longer window can conceal brief corrections.
The subsequent [joint IMU/GPS covariance controls](../ilvis0-correlated-controls-20261007/README.md)
now test calibration/timing recovery and local precision with full assumed covariance.
Offset/drift controls preserve initial-state ambiguities. Supported IMU processing,
calibration and clock bounds remain open; neither these translation fixtures, receiver
agreement nor sensitivity calculations establish Group4 Earth-rate retention.

[Duration/rotation controls](../ilvis0-excitation-20261007/README.md) subsequently reproduce
independently calculated trajectories through a brief pitch correction and recover known
gyro-bias/timing offsets at20/60seconds. The joint calibration tangents retain unresolved
or weak directions, and their numerical rank changes with assumed covariance. The
[IMU6 evidence review](../ilvis0-excitation-20261007/INSTRUMENT_EVIDENCE.md) makes the
remaining processing/physical-clock uncertainties explicit. No decoded format, fitted
scale or software fixture is promoted to independent correction/calibration evidence.
The subsequent [information diagnostics](../ilvis0-information-20261007/README.md)
compare four central derivative steps and smooth bound-scaled reference information
on those same fixtures. Weak information and exact nulls remain visible without
interpreting a numerical rank flip as improved calibration. The reference penalty is
an artificial diagnostic; it supplies no instrument specification or Earth-rate
retention evidence.
The newer [instrument evidence review](../ilvis0-instrument-evidence-20261007/README.md)
supports an LN-200-family inference from a published POS AV510/IMU-6 association.
It distinguishes manufacturer descriptions of navigation corrections from the
unknown legacy Group4 logging tap. A documented LN-200 encoding used by another
receiver differs from the empirical Applanix scales, so it cannot replace them.
The six firmware/ICD identities and unresolved questions are packaged without
rescanning or modifying the frozen earlier evidence.
The [legacy-document search](../ilvis0-legacy-records-20261008/README.md) did not
obtain a manual matching those V5 revisions. Raw/unprocessed Level-0 describes
archive provenance, not the Group4 tap inside the instrument. A support request is
now sent; no modern or marine layout has replaced the legacy definitions. Separately,
[recorded-data modeling](../ilvis0-exploratory-20261008/README.md) proceeded on the six
recordings with stated processing cases while a reply was pending. Later completed
comparisons are linked above. Successful fitting does not, by itself, identify which
onboard corrections were applied; ordinary sensor filtering need not erase slow turning.

The [public Applanix interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
establishes the packet container and directs IMU data to POSPac processing. It does not
provide the needed physical payload definition. The inspected processing instructions describe
navigation processing; a smoothed trajectory export would not supply independent gyro data.

There is a documented format for preserving decoded IMU observations:
[Waypoint IMR](https://docs.novatel.com/Waypoint/Content/Data_Formats/IMR_File.htm).
Its header records byte order, rate/increment conventions, scale factors, sampling rate and
time basis. The [raw converter documentation](https://docs.novatel.com/Waypoint/Content/Inertial_Utilities/Raw_IMU_Data_Converter.htm)
does not establish that this exact Applanix log is supported. A compatible export would still
need its source conversions and corrections documented. No software purchase, installation,
conversion or invented IMR header has been performed.

Instrument type numbers belong to their respective manufacturers' formats. For example,
the [NovAtel type table](https://docs.novatel.com/OEM7/Content/SPAN_Commands/CONNECTIMU.htm)
assigns number 8 to LN200; that does not establish the identity or scaling of Applanix IMU8.
An unrelated type table must not determine this decoder.

The useful external step is now requesting processing, mounting and timing documentation.
The earlier request is preserved in
[AIRBORNE_DATA.md](AIRBORNE_DATA.md). The verified manufacturer
[support page](https://applanix.trimble.com/en/support) lists `techsupport@applanix.com`.
The dataset's [NSIDC page](https://nsidc.org/data/ilvis0/versions/1) is the archive contact
starting point. No inquiry has been sent. Sending one requires explicit user instruction.

Keep original measurements immutable. Additional `.013` logs now help check cross-file
compatibility and discover level-flight windows even while proprietary processing details
remain unknown. Every new configuration must pass its own checks; a result for IMU8 does
not establish another IMU type's scales. Existing fused navigation may describe maneuvers
but must not replace independent gyro evidence. The [acquisition guide](../ILVIS0.md)
describes the streaming decoder, catalog, safe downloader and geometry-only retention policy.
