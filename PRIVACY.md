# Privacy

Local Level Lab is open source, so every claim below can be checked in the code.

## What the app records (only while you're recording a phase)

- Raw motion sensors: gyroscope, accelerometer, magnetometer (calibrated and uncalibrated), barometric pressure, game rotation vector.
- GPS fixes: **only during the placement check and the flight recording.** Calibration and drift runs record no GPS. Optionally they save your latitude rounded to 0.5° (about 55 km), which you can turn off in Settings.
- Battery temperature, level and whether the phone is plugged in, about every 10 s.
- What you type in: airline, flight number, date, airports, aircraft type, seat, row, mount, notes.
- Phone manufacturer, model and Android version, plus sensor model names.
- A **random install ID** made on first launch. It links your own sessions together so the analysis can model your phone's sensor bias across flights. It isn't derived from any account or hardware ID.

## What it never records

No name, email, account, contacts, advertising ID, IP-based tracking, analytics, crash reporting, or location outside the phases above.

## Network

The only network request the app ever makes is the upload you start, to the server address shown in Settings. The address must be `https://`; the app refuses unencrypted servers. No third-party SDKs are included. See `android/app/build.gradle.kts` for the full dependency list.

## After upload

Uploaded sessions are published unmodified, with the install ID, as an open dataset under **CC0** (public domain). See [DATA_LICENSE.md](DATA_LICENSE.md). Don't put anything in the notes field that you wouldn't want public.

To have a session removed from the server, contact the server's operator with the session ID shown in the app. Copies already downloaded by others can't be recalled.
