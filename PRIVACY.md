# Privacy

Local Level Lab is open source, so every claim below can be checked in the code.

## What the app stores

- **The IMU's data stream**, byte for byte as the IMU sends it over Bluetooth: gyroscope, accelerometer, magnetometer, chip temperature, battery voltage and the IMU's own clock.
- **GPS fixes, only during the placement check and the flight recording.** Calibration, drift runs and bench recordings record no GPS. Calibrations can save your latitude rounded to 0.5° (about 55 km); you can turn that off in Settings.
- **Session details:** the operating airline you select, its directory ID and IATA/ICAO codes, directory revision, operating flight number, scheduled departure date at the origin and airport codes. Aircraft type, seat position (window/middle/aisle; default unspecified) and notes are optional; mount and orientation note are also stored. These details are saved when you create the session, before recording starts. Historical flight verification remains pending; opening a history link does not verify the flight.
- **Recording times and events:** monotonic timestamps, phone-clock anchors at session creation and flight start/resume, GNSS availability at flight start/resume, instrument configuration, link changes and mount-turn confirmations. Clock anchors are phone wall-clock readings, not certified UTC measurements. Missing GPS does not prevent IMU recording after acknowledgment.
- **Phone manufacturer, model and Android version**, because the phone's GPS receiver is part of the measurement. Also the IMU variant and its settings.
- **A random install ID**, made on first launch. It links your own sessions together. It isn't derived from any account or hardware ID.
- **A random unit ID for each IMU you pair.** It links sessions made with the same IMU, so its quirks can be modelled across flights. The IMU's Bluetooth address stays on your phone and is never written to a session.

## What it never records

No name, email, account, contacts, advertising ID, IP-based tracking, analytics, crash reporting, or location outside the phases above.

## Bluetooth

The app uses Bluetooth only to talk to the IMU you choose in Settings. Scanning is only used to find that IMU, never to infer location.

## Network

The only network request the app ever makes is the upload you start, to the server address shown in Settings. The address must be `https://`; the app refuses unencrypted servers. No third-party SDKs are included. See `android/app/build.gradle.kts` for the full dependency list.

Airline selection uses a bundled offline directory and does not contact a provider. **Open flight
history** explicitly launches your external browser with a FlightAware URL containing the selected
carrier/flight identifier. That website receives the browser request under its own privacy policy
and browser settings, including cookies and the network address visible to it. The link does not
send your IMU stream, phone GPS, session ID or complete manifest. This is separate from upload
consent. There is no automatic flight-history lookup or external-track download in the app.

## After upload

Uploaded sessions are published unmodified, with the install ID and unit ID, as an open dataset under **CC0** (public domain). See [DATA_LICENSE.md](DATA_LICENSE.md). Don't put anything in the notes field that you wouldn't want public.

To have a session removed from the server, contact the server's operator with the session ID shown in the app. Legacy archives may still contain exact seat numbers. Precise paths, flight metadata and linked identifiers can identify people; these data are not anonymous. The upload dialog requires explicit public-release consent.

Copies already downloaded by others can't be recalled.

An external track supplied for GPS checking or recovery is a separate artifact with its own
source and terms. It does not replace the original recording or automatically qualify a flight
for scientific use. See [the protocol](docs/PROTOCOL.md).

The server stores hashed client IP keys for admission and rate limiting for approximately one hour (purged on subsequent uploads). Hashing is not anonymization. Curator operator identities stay in the private registry; public approvals identify instruments with opaque IDs.
