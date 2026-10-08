# GPS uncertainty and the recorded measurement chain

The six-file audit recovered **2,968 receiver positions with their own reported error
estimates**, without using Applanix's fused navigation as the observation. It also
reassembled **29,681 checksummed survey-record envelopes**. Six original source hashes
and full outer frame counts reproduce, and sixteen focused tests pass. No measured
Earth-model fit ran, no scientific rule changed, and all 232 originals remain preserved.

## What was hiding alongside the GPS sentences

The primary receiver stream contains binary Trimble messages as well as the familiar
GPS sentences. These are separate from the Applanix GPS/IMU navigation answer. The
[Applanix ICD](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
describes Group 10001 as receiver output, Group 4 as time-tagged IMU data, and Group
10002 as direct IMU output. It does not specify the IMU6 processing history. Its modern
clock fields identify validity time; they do not fully establish legacy sensor integration
timing or physical latency.

The two older receiver configurations carry GPS-only RT17 survey records. The other four
carry RT27 satellite-measurement and enhanced-position record envelopes. Each binary packet
has its own checksum, in addition to the enclosing Applanix checksum. Satellite records can
span several packets. The new decoder checks page order, reply identifiers, flags and
lengths before reassembling them. It preserves the measurement payload rather than claiming
to have decoded satellite ranges or carrier phases. The format is documented by
[Trimble](https://receiverhelp.trimble.com/oem-gnss/icd-pkt-response57h-rawdata.html).

The stream also contains GSOF position and uncertainty messages. The parser verifies their
pages, record lengths and big-endian engineering units. It retains GPS week, actual epoch,
coordinates, status flags, initialization counter and reported uncertainty. Unknown record
types remain unpromoted. [Trimble's position description](https://receiverhelp.trimble.com/oem-gnss/gsof-messages-llh.html)
specifies WGS-84 coordinates and ellipsoidal height; the
[uncertainty description](https://receiverhelp.trimble.com/oem-gnss/gsof-messages-sigma.html)
defines the reported sigma fields.

## What the receiver reports

These are median reported values over each recording, in metres. They are the receiver's
own error estimates, not independently measured errors or IMU performance specifications.

| Recording | GPS epochs | North sigma | East sigma | Vertical sigma |
| --- | ---: | ---: | ---: | ---: |
| 14 April 2009, LVIS | 489 | 0.549 | 0.380 | 1.377 |
| 16 September 2014, POS510 | 482 | 0.615 | 0.540 | 1.440 |
| 26 October 2010, LVIS | 486 | 0.521 | 0.534 | 1.110 |
| 20 November 2010, LVIS | 483 | 0.602 | 0.471 | 1.078 |
| 24 September 2015, LVISGH | 459 | 0.651 | 0.397 | 1.070 |
| 20 September 2017, B200T filename | 569 | 0.352 | 0.290 | 0.723 |

Every binary GPS week/date reproduces the embedded receiver date. Every decoded position
also matches a unique GPS sentence at the same epoch. Horizontal differences are at the
sentence's rounding scale, and height differences remain below about one millimetre after
adding the reported geoid separation. This verifies units, byte order, timing and product
association. Two products from the same receiver cannot independently verify its accuracy.

The east/north cross-field is preserved as reported. Its public table labels it as
dimensionless; the code does not silently interpret it as square metres or assemble a
complete covariance matrix from it. Cross-epoch correlation, filtering and the accuracy
of the reported sigmas still need support. No millimetre software-fixture uncertainty has
been substituted for these metre-scale receiver reports.

## Strict handling of incomplete and unfamiliar data

The [first audit](../ilvis0-processing-20261007/README.md) stopped at NAK response bytes in
four streams. The revision recognizes the documented ACK/NAK protocol responses explicitly.
They are counted, not discarded, and are not accepted scientific measurements. A NAK can
mean that a command is unsupported; it does not by itself show that subsequent satellite
observations are invalid. [Trimble protocol reference](https://receiverhelp.trimble.com/oem-gnss/api-data-collector-format-packets.html)

Four streams end on complete receiver boundaries. The October 2010 file ends inside a
receiver packet with 44 bytes remaining; the September 2017 file ends inside a packet
header with four bytes remaining. Both also have an unfinished final survey record. These
boundary failures remain recorded. No packet, sample or receiver page is repaired or
interpolated. Complete preceding packets and GPS products remain available for investigation.

All six Applanix streams are complete and checksum-valid. All accepted receiver binary
packets and NMEA sentences pass their checksums. Missing or duplicate survey pages are
rejected. There were no GSOF decoding failures. These are separate statements: valid
Applanix framing does not imply that the final embedded receiver item is complete.

## What is still unresolved for the IMU

All six representatives identify as POS AV 510, version 5, **IMU6**, spanning three
firmware/ICD combinations and separate installation epochs. Their Group-4 raw-frame and
IMU status fields are zero throughout. That establishes the recorded status values; it
does not establish the meaning of every proprietary status bit or absence of corrections.

Logged messages, including unknown internal messages, are inventoried with their complete
payload, hash, count and first/last packet offsets. Modern message numbers are not blindly
applied to legacy layouts. Existing inferred installation angles and the marginal
26 October 2010 gyro-scale failure remain unchanged.

Both IMU time tags carry nearly the same microsecond interval fluctuations, with no
reversals or clock-base changes. This corroborates the recorded time relationship; it does
not independently measure the physical integration period. Receiver packet timing differs
from receiver position epochs by tens to hundreds of milliseconds. Those differences
include serialization and packet association and are not estimates of IMU latency.

The Group-2 navigation uncertainties are preserved as internal fused estimates. They do
not provide independent attitude truth. The IMU6 sensor identity, intrinsic drift/noise,
factory calibration, coning/sculling, filtering, Earth/transport compensation and precise
latency remain unsupported. Published performance for the different IMU8 reference must
not be assigned to these IMU6 files.

## The next useful work

The GPS uncertainty problem is now more specific: receiver-reported uncertainty exists
and has been decoded, while its covariance and coverage need validation. The raw satellite
record envelopes provide a possible route to reconstructing a receiver-only solution and
checking uncertainty, subject to complete satellite/ephemeris decoding and available data.
That path uses the existing `.013` originals; it does not require obtaining other file types.

Separately, establish a defensible recorded-IMU processing and calibration envelope. Then
test whether the joint IMU/GPS model can separate a given pair under that envelope. Partial
globe-versus-disc evidence remains useful, but the present audit supplies no Earth winner
or calibrated significance. Measured Earth starts remain zero.

Code: `analysis/lll/trimble_receiver.py`, `ilvis0_processing.py`; launcher
`analysis/tests/ilvis0_processing_worker.py`. Completed output:
`data/ilvis0-processing-v2-20261007/`. This directory preserves the compressed full report,
CSV GPS uncertainty inventory, source/input/environment manifest and frozen source copies.
The first audit's separate evidence remains intact. Do not resume either completed audit
or combine revised sources under their manifests.
