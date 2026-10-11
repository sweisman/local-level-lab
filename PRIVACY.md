# Privacy

The app records an external **IMU (inertial measurement unit)** over Bluetooth.
New participant recordings are stationary ground experiments, not flights.

## Stored in a new stationary recording

- Original Bluetooth bytes, including the available gyro, acceleration, magnetic,
  temperature, voltage and instrument-clock messages.
- Recording times, still-block positions, setting readbacks, link changes, interruptions
  and quality flags. Phone wall-clock time is not certified UTC.
- The location, approximate altitude, axis, alignment method/uncertainty, device label,
  support details and notes you enter. Coordinates can be rounded or omitted.
- Phone model/software information and IMU model/settings.
- Random install and unit IDs linking related recordings. The Bluetooth address remains
  on the phone; the IDs are not derived from your identity.

The stationary flow does not request continuous GPS or airline, flight, airport,
aircraft or seat information. Location is entered manually. Instrument tests may retain
a coarse cached calibration latitude if that legacy setting and location permission
are enabled. Old flight archives remain readable and retain their original exact GPS
and flight metadata; they are not rewritten into ground recordings.

## Permissions and network

Bluetooth is used to connect to the selected IMU. Notifications show progress and
announce completed blocks. Background recording uses a foreground service and wake lock.

The app includes no analytics or advertising SDK. It does not collect contacts,
account details or a hardware-derived participant ID. Uploads occur only when you
request them, to the HTTPS server shown in Settings. New stationary collection does
not open a flight-history website.

## Sharing and public upload

Sharing exports the original archive to the destination you choose. Upload requires
explicit consent to publish it under CC0. Entered location, dates, serial labels, notes
and linked identifiers can identify people. **The data are not anonymous.** Avoid
precise home coordinates and private notes if you do not want them published.

The uploaded original remains unchanged. Contact the server operator with the session
ID to request removal; copies already downloaded cannot be recalled.
[Data licensing](DATA_LICENSE.md) explains third-party and historical data terms.

The server retains hashed client-IP keys for rate limiting for approximately an hour,
purged on later uploads. Hashing is not anonymization. Operator identities in the
curation registry remain private; public records use opaque instrument identifiers.
