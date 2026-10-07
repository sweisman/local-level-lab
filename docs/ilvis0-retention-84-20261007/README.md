# Keep/discard review of the 84 GPS-promising files

This local review addresses storage usefulness. It does not make an Earth-model claim or
require unresolved files to satisfy a scientific orientation gate before they can be kept.
Of the 84 files, 82 use IMU6, whose physical conversion needs separate investigation; two
use IMU21 and pass the earlier physical checks as fine-alignment decoder diagnostics.

## Final decisions

**Keep 83 files; discard one redundant copy.** Every kept file has at least 60 seconds of
uninterrupted raw IMU measurements inside a GPS-selected stretch. Hash and framing checks
passed for all 84. The kept files represent about 7.02 hours of GPS-selected geometry across
potentially overlapping streams; this is not independently confirmed level-flight time.

Twenty-two kept files also have at least a minute compatible with the stricter fused-navigation
motion limits when the alignment label is omitted. These are descriptive spans, without a new
buffer around every internal bank boundary; they are not accepted scientific windows. The
other 61 still contain complete measurements and useful trajectory context, so missing
orientation/decoding knowledge is insufficient grounds to discard them. Keeping them does
not establish that a usable level-flight interval can ultimately be recovered.

The remaining 83 comprise 81 IMU6 files and two IMU21 files. Their reported median heading
uncertainties within the GPS stretches range from about 0.050 to 0.755 degrees. Those are
internal fused estimates using an inferred older layout, not demonstrated accuracy. None
gains scientific eligibility. Units/axes for IMU6 and independent orientation/correction
behavior still need work before an Earth-shape test.

The review verifies each original's hash and packet checksums, checks for at least 60 seconds
of uninterrupted raw IMU measurements inside GPS-selected stretches, and reports the
navigation solution's roll, motion and internal uncertainty. Those navigation quantities
are fused context, not independent orientation evidence. Unknown scales and fine-alignment
flags do not by themselves justify throwing away useful measurements.

An initial IMU6 sample has much stronger gyro agreement after a 90-degree horizontal-axis
remapping. This is diagnostic evidence that an assumed axis convention can cause failed
comparisons. It is not a validated scale table or a completed decoder.

The catalog's 21 and 22 April 2010 LVIS510 files contain identical original bytes and both
embed 21 April timestamps. The correctly dated entry was retained. The redundant owned
compressed original was removed after verifying both hashes and writing durable
prepared/removed disposition records. This reclaimed 6,984,885 bytes (about 6.66 MiB).
Other useful or uncertain measurements stay intact. The corpus now holds 232 originals:
80 earlier candidates and 152 alignment-blocked files. There are 93 historical no-level
rejections and one later duplicate removal; previous reports retain their original counts.

The audit uses [Applanix's interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
for framing/status structure. Full-navigation status incorporates user accuracy requirements;
it is not a universal accuracy threshold for this experiment. The manufacturer's
[operation guide](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_USER_MANUAL.pdf)
also describes user-selected accuracy indicators. Neither status nor internal RMS estimates
independently establish actual orientation accuracy.

The separate manifest, atomic reports and process lock live in
`data/ilvis0-retention-84-20261007/`. No prior ledger or frozen study is rewritten. Scientific
eligibility remains unchanged; no downloads, synthetic campaigns or Earth-model fits run.
The worker has completed and released its lock. `inventory.csv` lists each filename, decision
and reason; `completion.json`, `summary.json.gz` and `cleanup.jsonl` preserve the evidence.
The manifest and source snapshots preserve the implementation. Seven focused retention tests
passed, including protection against a changed canonical original and interrupted deletion.

Any future selection must honor the cleanup journal: the removed 22 April catalog entry maps
to the preserved 21 April entry. Do not restart older completed workers that expect both copies.
