# Accept the archive's one-digit UTC hours

After correcting the work accounting, five of eight exports screened
successfully. The other three stopped on their UTC text field. An inventory
of the text formats found that `178a`, `180` and `182` write hours 0–9 without
a leading zero. Both forms are accepted and retained verbatim. Numerical
GPS week and second fields continue to set order, gaps and durations.
[Version-2 result](esa-confirmation-receiver-inventory-v2-result.json)

Freeze only these three files in version 3. Reuse the five completed screens
from version 2. Keep the original receiver rules, hashes, one-thread
allocation, per-file work limits and recovery policy. Keep all starts and
failures from the earlier studies. This changes no selection threshold,
processes no protected inertial data and performs no Earth-model fits.
