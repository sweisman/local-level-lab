# Comparing accelerometers on the same flight

Test how much two recorders on the same aircraft agree about changes in the
size of the measured force per unit mass. Use the two flight groups already
selected for the [matched extension](MATCHED_EXTENSION_FORECAST_RESULT.md).
Their published common legs are `leg-13805a9a35c4` (IMU8 and IMU21) and
`leg-9c109162b404` (two IMU21 units). Freeze the four original files,
receiver-selected stretches and overlap table before processing.

Convert signed accelerometer counts with each stream's recorded conversion
hypothesis. Divide by packet duration, then take the vector magnitude. Compare
duration-weighted averages over common windows of 0.05, 0.25, 1, 10 and 30
seconds from the recorded overlap start. Use only whole packets in each window
and require at least 80% coverage from each recorder. Keep nominal 200 Hz and
packet-header timing separate. Apply no fitted alignment. Split at the overlap
midpoint and omit straddling windows. Learn a constant magnitude difference
from the earlier windows and report later correlation and discrepancy both
before and after removing that difference.

The shared study runner will execute two tasks with two single-thread workers,
at most two original reads and 300,000 decoded packets per task, and a 300-second
cooperative allowance. Each comparison covers five window sizes and two clocks.
There are zero Earth-model fits. Preserve verified partial work and use the
qualified technical recovery policy for unfinished tasks only.

Tests must cover whole-packet support, the split, and known paired differences.
Continue to abstain on aircraft calibration and Earth-model evidence. Shared
vibration and processing can agree on both instruments, and different mounting
locations or timing can create disagreement. The comparison cannot measure the
continuous force within a packet or yield an upper bound on its rate of change.
