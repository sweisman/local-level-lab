# Offline airline directory

`airlines.json` is derived from the worldwide OpenFlights airline database, not a handpicked
list of major carriers. It includes all 6,136 named entries with syntactically valid IATA or
ICAO codes. Distinct record IDs preserve shared codes. The source's activity flag only affects
search ordering: OpenFlights explicitly says it is unreliable. Historical airlines remain
available for historical recordings. This snapshot cannot guarantee every current carrier.

Source and license: https://openflights.org/data.php (ODbL-1.0).
The exact upstream revision, download SHA-256 and pinned source URL are in the JSON.
`airlines-LICENSE.txt` contains the upstream database license. This separately licensed dataset
is not covered by the recording archive's CC0 license or the app source's AGPL license.

To refresh, download `data/airlines.dat` at an exact OpenFlights revision, then run:

```sh
/home/sweisman/venv/bin/python analysis/tests/build_airline_directory.py /tmp/airlines.dat --revision UPSTREAM_COMMIT --output android/app/src/main/assets/airlines.json
```

Update the upstream license if needed and run `FlightIdentityTest`. Selection remains offline;
valid carrier/number/date syntax is not historical flight verification. A later dated provider
record must match the operating carrier, route and recording time before scientific use.
