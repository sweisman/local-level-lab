# Satellite measurements recovered from the airborne recordings

The six prepared recordings now have decoded satellite measurements, rather than only
GPS position reports. **19,699 observation epochs contain 603,603 signal measurements**.
All six original hashes, outer packet counts and complete receiver-record sequences
match the previous frozen inspection. Thirty-one focused tests pass. All 232 originals
remain preserved; no flight-position fit or Earth-model fit ran.

This is a useful step toward checking the flight trajectory independently of the
combined GPS/IMU navigation answer. It does not yet establish the accuracy of the
trajectory or resolve what corrections were applied to the IMU.

## What has been decoded

The two older receiver streams use concise RT17, with observations every tenth of a
second. The other four use RT27, with observations every fifth of a second. No missing
observation epoch was found between the complete first and last epochs using the
declared 1.5-times-median interval diagnostic. This does not make unfinished final
receiver packets complete.

| Recording | Observation epochs | Signal measurements | Observation rate | GPS ephemeris packets |
| --- | ---: | ---: | ---: | ---: |
| 14 April 2009, LVIS | 4,894 | 87,946 | 10 Hz | 18 |
| 16 September 2014, POS510 | 4,823 | 96,460 | 10 Hz | 20 |
| 26 October 2010, LVIS | 2,430 | 72,744 | 5 Hz | 79 |
| 20 November 2010, LVIS | 2,415 | 75,241 | 5 Hz | 65 |
| 24 September 2015, LVISGH | 2,293 | 106,260 | 5 Hz | 61 |
| 20 September 2017, B200T filename | 2,844 | 164,952 | 5 Hz | 83 |

An observation epoch is one receiver measurement time. A signal measurement is one
tracked signal from one satellite at that time. These counts are repeated measurements
within six recordings, not independent flights or independent statistical trials.

The decoder preserves code pseudoranges in metres, carrier phase in the receiver's
original cycle/sign convention, signal strength, available Doppler, constellation,
antenna, frequency-band/track identifiers, validity flags and slip information. RT27
signed three-byte clock offsets and six-byte phases, absolute/differential ranges,
overflow extensions and variable-length flag/block boundaries are checked. Unknown
layouts fail rather than being skipped to improve the usable count. The entire encoded
survey payload accompanies each exported epoch. Raw RT27 integers remain available.
The [RT17 concise](https://receiverhelp.trimble.com/oem-gnss/icd-subtype0-realtime-survey-data-17-concise.html)
and [RT27](https://receiverhelp.trimble.com/oem-gnss/icd-subtype6-realtime-gnss-survey-data-27.html)
tables provide the structural and engineering-unit references.

GPS week comes from the recorded receiver products, never the computer's current date.
All decoded observation dates agree with the previously established embedded dates.
There are 2,968 exact-millisecond observation epochs shared with the receiver's earlier
position/error-estimate reports. Millisecond association is explicit; no GPS fix is
interpolated into a missing observation epoch. Receiver clock fields are preserved, not
silently applied as a guessed correction to IMU latency or observation validity time.

## What the orbit and angle checks establish

The streams contain **326 GPS ephemeris packets**. These describe satellite orbits and
clocks. The GPS decoder retains the transmitted values, converts angular semicircles to
radians, and records health, issue identifiers and source offsets. Other satellite
information, including GLONASS ephemerides and ionosphere/UTC packets, remains preserved
opaque for subsequent decoding. [Trimble's GPS ephemeris table](https://receiverhelp.trimble.com/oem-gnss/icd-pkt-response55h-gps-eph.html)
and the [GPS interface specification](https://www.navcen.uscg.gov/sites/default/files/pdf/gps/IS-GPS-200N.pdf)
support this interpretation; RTKLIB's original receiver implementation supplies an
additional angular-unit cross-check.

At recorded position epochs, healthy GPS ephemerides within two hours of their stated
reference time predict satellite directions. These directions are compared with the
receiver's coarse azimuth/elevation fields. This checks orbit units, timing and association
under the usual WGS84/GPS navigation assumptions. It supplies no independent Earth-shape
evidence and is not a high-precision orbit or positioning result. Signal travel time and
atmospheric delays are not part of this coarse sky-angle check.

Of **29,567 comparisons**, 29 exceed the diagnostic limits. Every one is GPS satellite 10
in the April 2009 recording, where the receiver reports both angles as zero from
12:06:59 through 12:07:27 UTC. The propagated elevation is roughly 8 degrees and azimuth
roughly 224 degrees. Recorded code/phase observations still exist. The discrepancy is
preserved with epoch, flags, measurements, packet offsets and payload hashes; it is not
repaired, treated as proof of corrupt ranges, or used to discard the flight. The other
comparisons lie within the documented diagnostic allowance for coarse angle fields.

The equal-weight geometry calculation has full local rank at all decoded epochs. Median
horizontal dilution factors range approximately 0.55–0.93 and vertical factors 0.92–1.84.
It gives each constellation a separate clock parameter. These are geometry factors
under assumed independent unit range errors, not metre-valued accuracy estimates or a
validated covariance matrix. The zero-angle observations remain in this diagnostic;
future positioning must use supported ephemeris geometry rather than trust every coarse
angle field.

RT17 phase differences agree much better with one Doppler sign convention than its
opposite: median absolute rate-minus-Doppler discrepancies are about 0.07–0.08 Hz after
flagged slips/unsupported adjacent intervals are excluded from this labeled check. Both
sign hypotheses and all original measurements remain reported. RT27 in these files has
no loaded Doppler for this comparison; none is manufactured by differentiating phase.
This consistency check is not a carrier-phase position solution or sensor noise bound.

## Processing flags and incomplete tails

RT27's recorded code/phase smoothing flags are clear in these four streams. That does
not establish the absence of all receiver processing. RT17's flag instead concerns
filtered pseudorange corrections; it cannot establish code smoothing. The initial
[v1 audit](../ilvis0-gnss-20261007/README.md) mislabeled this distinction. Its original
outputs/source freeze remain intact; this separate v2 audit uses an explicit unknown
smoothing state for RT17 and a separate filtered-correction field. Those correction
flags are clear in both RT17 streams.

The two previously identified receiver tails reproduce: October 2010 ends with an
unfinished receiver item and survey record, as does September 2017. Their complete
prefixes remain decoded. No resynchronization, range repair, interpolation or original
deletion occurred. All outer Applanix framing/checksums remain valid.

## What comes next

Reconstruct a bounded receiver-only trajectory from the decoded measurements and GPS
ephemerides, with explicit satellite-clock, signal-time and atmospheric corrections.
The existing ionosphere/UTC packets and multi-frequency observations can support that
work. Compare its residuals and stability with the receiver-reported positions/sigmas,
preserving uncertainty from satellite geometry, common errors, filtering and temporal
correlation. Comparing two solutions from the same receiver is a consistency check,
not independent coverage validation. Carrier-phase ambiguities and slip handling need
their own support before a precision claim.

In parallel, the IMU6 processing, physical clock, calibration and mounting uncertainties
remain scientific prerequisites. No GPS-only result automatically resolves them, makes
Applanix fused attitude independent, transfers a passenger-campaign threshold, or
establishes a three-model winner. Measured Earth optimizer starts remain zero.

Code: `analysis/lll/trimble_observations.py`, `ilvis0_gnss.py`; worker:
`analysis/tests/ilvis0_gnss_worker.py`. Completed data:
`data/ilvis0-gnss-v2-20261007/`. Each file has deterministic gzip CSV/JSONL measurement
exports, a hash-bound report/receipt, and a frozen source/input/environment manifest.
This evidence directory preserves the compact reports, per-file inventory, flagged
angle inventory and source snapshots. It does not duplicate the larger measurement
exports. Both completed audits are frozen and must not be resumed with revised sources.
