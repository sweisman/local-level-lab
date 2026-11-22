# The aircraft and Reykjavík station share 61 raw GPS epochs

All **61** fixed-station times matched the aircraft's original GPS
times exactly. The two receivers shared **10–14 satellites** per
match with both code and carrier observations on `C1C`, `L1C`, `C2W`
and `L2W`. Ten satellites retained both signals throughout the stop
without a missing observation or a reported carrier lock flag.
[Reykjavík station excerpt](ESA_FIXED_REFERENCE_WINDOW_RESULT.md)

The aircraft excerpt contains **3,601 half-second records** from
ESA recording 187. Checking the intervening epochs matters because
a loss of lock can occur between the station's 30-second samples.
The result lists the satellites that carry across each interval and
preserves the reported lock flags. The transfer retained 30 verified
byte ranges under the frozen cap. Four focused software checks passed.

The data are ready for a controlled relative-motion check during the
Reykjavík stop. The comparison covers one aircraft and one ground
receiver. It gives no error estimate for the earlier Greenland flight.
No aircraft fits or reserved recordings were used.

The aircraft excerpt is kept locally. Its checksum, exact selected times,
source path, byte-range receipts and per-epoch results are recorded.
With authorized access to the same ESA archive, the reproducible
acquisition is `env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_fixed_reference_pair acquire`.
[Source selection and limits](ESA_FIXED_REFERENCE_PAIR_PLAN.md) ·
[Coverage and receipts](esa-fixed-reference-pair-result.json) ·
[AirQuantumGrav source collection](https://doi.org/10.57780/esa-58c58c5)
