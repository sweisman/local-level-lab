# Observed flight geometry — 2026-10-06

Scott supplied three historical position-track exports for development geometry screening.
The source files remain in his home directory; the importer opens only the three named files.
Their source labels identify FlightAware ADS-B. No IMU, aircraft heading, measured wind,
sensor calibration or mount-turn data accompany these tracks.

| Flight | Points | Recorded span | Latitude range | Missing speed / altitude |
|---|---:|---:|---:|---:|
| 2025-09-01 Etihad 10, ORD–AUH | 1,234 | 12h54m | 24.32–49.11°N | 131 / 131 |
| 2025-08-19 Etihad 9, AUH–ORD | 1,330 | 13h47m | 24.42–56.50°N | 91 / 91 |
| 2025-08-19 AA 1433, ORD–LAX | 449 | 3h38m | 33.94–41.97°N | 0 / 1 |

`normalized-tracks.json.gz` preserves positions, per-position source/estimate flags, displayed times, ground course, ground speed
and reported altitude, with SI conversions, elapsed seconds, original filenames and SHA256 hashes.
Missing measurements remain null. The displayed timezone is unconfirmed, so no absolute UTC
timestamps have been inferred. The reported altitude's barometric/geometric reference is unverified.

`summary.json` contains sampling/gap diagnostics and all 75-minute windows on a five-minute grid.
There are 67, 74 and 29 windows, respectively, with at least 95% reported position coverage when
intervals exceeding 90 seconds and provider-estimated endpoints do not count as observed coverage.
There are 131, 91 and zero provider-estimated positions, respectively. Maximum gaps are 184, 158 and
45 seconds. Windows overlap and are not independent samples. These counts do not certify cruise
qualification, heading diversity, identifiability, or candidate eligibility.

Importer: `analysis/tests/import_flight_tracks.py`; four focused parser/coverage tests passed.
It performs no scientific fits or simulations and does not change the active frozen pilot.
Use these tracks after that pilot finishes to define observed geometry stress cases. Any IMU,
mount-turn protocol, crab/wind and bias processes for such cases must be explicitly simulated
and preregistered; interpolation cannot recover actual aircraft dynamics between position samples.
Never bridge coverage gaps as if they were observations or relabel these tracks as sensor validation.

These three tracks are sufficient for the initial route workflow. Additional manual downloads
can target missing geometry: high latitude beyond 60°, near the equator, and a predominantly
north–south route. A few deliberately different routes are more useful than many similar ones.
