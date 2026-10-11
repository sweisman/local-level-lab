# Stationary participant protocol

An **IMU (inertial measurement unit)** measures turning and acceleration.
This experiment records it resting in two opposite orientations to estimate a very
slow horizontal rotation component. You do not need an aircraft or a moving GPS track.
The target is a measured rotation field; the recording does not identify its physical cause.

## Prepare

1. Choose a solid, level surface away from vibration, moving furniture and direct sun.
   Secure cables so they cannot pull the IMU. Let its temperature settle.
2. Mark positions A and B exactly 180° apart in a holder or against repeatable stops.
   Keep the same face up throughout. Mark the positive X or Y sensor axis.
3. Align that axis approximately toward **true north** in A. A magnetic compass alone
   gives magnetic north; record your alignment method and uncertainty.
4. In Settings, choose the IMU and write and verify its settings. Automatic gyro zeroing
   must be off. Keep the phone charged and allow background recording.

Open **New stationary recording**. Enter the marked axis, location, approximate altitude,
alignment, device label and support details. Coordinates may be rounded; record unknowns
as unknown rather than inventing precision. Indoor GPS is unnecessary. Southern latitude
and western longitude are negative. Everything entered will be public if you upload.

## Record

The sequence is **A–B–B–A, then A–B–B–A again**. The initial development setting is
30 still minutes per block: about four hours, plus settling and turns. Settings permit
10–120 minutes per block; no duration is a validated guarantee of detection.

Start each block when instructed, then leave the IMU and support untouched. The app
saves raw data even when movement is detected. A notification announces a completed
block. Open the app before the next block: turn slowly to the other mark only when
the position changes. Consecutive B blocks or consecutive A blocks require no turn.

Do not turn the IMU upside down. The accelerometer checks the upward face; it cannot
verify true north or the precise reversal angle. The analysis trims the first and last
30 seconds from each block, preserving those measurements in the original.

Interrupted or short blocks remain saved. Repeat an incomplete block when prompted;
do not discard attempts based on the gyro value. Keep link failures and unexpected
movements. Long unattended still recordings are useful instrument controls, but the
reversal experiment needs someone to perform the prompted turns.

## Finish

Share the original archive for private analysis, or choose Upload and explicitly consent
to permanent public release. Location, device details, notes and linked random identifiers
can identify you; avoid private text and exact home coordinates if you do not want them
published. Read the [privacy policy](../PRIVACY.md).

The analysis estimates a signed reversal signal before checking latitude. A preliminary
number is not a validated detection. Instrument tests, repeatability and uncertainty
checks remain necessary. See [what the experiment measures](STATIONARY.md) and
[bench tests](BENCH.md). Earlier passenger-flight protocols are historical development
work, preserved in the technical records.
