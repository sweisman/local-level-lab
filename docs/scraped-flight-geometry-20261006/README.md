# Directly scraped flight geometry — 2026-10-06

Scott authorized direct scraping of complete public track pages and requested Europe/Middle East
to South Africa as additional north–south cases. Four FlightAware track tables were retrieved,
without an account or browser session. Each flight departed on **2026-10-02 UTC**.

| Flight | Geometry | Coordinate rows | Provider-estimated rows | Recorded span |
|---|---|---:|---:|---:|
| Icelandair FI680, SEA–KEF | High latitude; reported positions reach 67.97°N | 560 | 70 | 7h00m |
| Singapore Airlines SQ938, SIN–DPS | Equatorial, 1.50°N to 8.81°S | 270 | 5 | 2h27m |
| Lufthansa LH572, FRA–JNB | Europe–South Africa, 50.00°N to 26.13°S | 602 | 262 | 9h38m |
| Emirates EK761, DXB–JNB | Middle East–South Africa, 25.24°N to 26.15°S | 518 | 174 | 7h36m |

Source track pages:

- [FI680](https://www.flightaware.com/live/flight/ICE680/history/20261002/2250Z/KSEA/BIKF/tracklog)
- [SQ938](https://www.flightaware.com/live/flight/SIA938/history/20261002/0125Z/WSSS/WADD/tracklog)
- [LH572](https://www.flightaware.com/live/flight/DLH572/history/20261002/2015Z/EDDF/FAOR/tracklog)
- [EK761](https://www.flightaware.com/live/flight/UAE761/history/20261002/0015Z/OMDB/FAOR/tracklog)

The CSV filenames follow Scott's `yyyy-mm-dd airline number origin destination` convention.
Each has a matching `.provenance.json` with the source URL, retrieved HTML/export hashes,
retrieval time, extractor hash, page timezone and UTC observation bounds. All coordinate rows
in the public tables were extracted; event annotations and duplicate rounded mobile-display
values were omitted. "Complete table" does not mean uninterrupted measured coverage.

The pages explicitly display **EDT**. The extractor reconstructs the dated New York clock from
each actual history link, verifies the dated timezone against the page label, and exports UTC.
`normalized-tracks.json.gz` preserves source labels and estimate flags for each position, elapsed
time and SI units. `summary.json` reports gaps, missing values and position-coverage windows.

Estimated/approximate points are kept for broad path inspection but **excluded from observed
coverage**. They often lack speed and altitude. In particular, the African routes have large
estimated portions and cannot establish continuously observed motion through those portions.
Maximum sampling gaps are 430, 148, 148 and 174 seconds. With a 90-second gap limit, the tracks
have 10, 0, 12 and 0 overlapping 75-minute windows with >=95% reported-position coverage.
This screening threshold is provisional; zero qualifying windows does not erase the route's
usefulness for coarse geometry. It does preclude pretending that the public track is dense
receiver data. Windows are not independent flight samples or accepted scientific flights.

The raw HTML downloads remain temporary inputs. The factual CSVs and provenance are the durable
source artifacts for later geometry work. Public-history links can expire or change.
These tracks have no IMU, measured wind or mount-turn schedule. Sensor/nuisance processes must
be simulated explicitly in any later trajectory study. The active 1,000-flight pilot is unchanged.

Extraction: `analysis/tests/extract_flightaware_track.py`; normalization:
`analysis/tests/import_flight_tracks.py`. Seven lightweight checks cover table annotations,
full coordinate precision, UTC day crossing, gaps, missing values and provider estimates.
