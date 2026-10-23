# Recover exact report comparisons across JSON

All six cases finished, retaining eight exactly matching report pairs. The fresh reports contain
Python tuples; restoring JSON produces lists. Comparing those Python objects
can fail without any difference in the recorded scientific values.

The parent freeze is closed. Its outcomes, source, logs and charges remain
preserved; it will not be restarted.

## Correct the comparison and preserve evidence

Use the shared canonical report encoder for exact equality. This changes no
value, bound or tolerance: a one-ULP difference, signed-zero difference or
integer/float representation difference must still fail. Test both original
references after a real JSON round trip, using the actual immutable writer.

Save every returned query report and the work accounting before checking any
comparison. The current worker stops after its first mismatch, so later reports
from an already completed batch may be absent from the saved evidence.

## Completed saved-output audit

The full audit has checked all six cases against these requirements:

1. Verify its sealed reports, inputs, code, environment, point-oracle records
   and charges. Keep its original failure labels.
2. Compare all available original/cached report pairs as exact canonical bytes.
   Reconstruct all 51 coefficient columns from the saved oracle Jacobians and
   report blocks; retain the unchanged center tolerance and resource limits.
3. Reuse complete evidence wherever it suffices. Never recalculate a verified
   original reference or point-oracle result merely for this repair.
4. A separate finite freeze may calculate only cached reports that were not
   retained after the false comparison. Admit that work only when the original
   batch returned within its limits and every available comparison agrees.
   An incomplete calculation or genuine numerical discrepancy is not silently
   retried as a formatting repair.

The audit fixes four missing later reports, all in globe histories. A
[separately frozen recovery](../ilvis0-native-prefix-format-recovery/README.md)
completed four two-query cached batches, reusing all original and point-oracle
records. All six histories now have complete verified comparisons. The two disc
histories needed no new calculation. Its allowance was independent of the
closed parent; neither study permitted retries.

The shared saved-output audit is `lll.ilvis0_native_prefix_audit`. Its 21
deterministic checks reject changed reports, invalid saved point checks,
incomplete batches and resource overruns. They also check that an equal earlier
query cannot stand in for a missing later query. These are bookkeeping checks;
the completed audit confirms eight exact report comparisons and twelve saved
point checks. The four missing later outputs have now been recovered in the
separate study; all six history comparisons are complete.

A source preflight confirms that all 136 other frozen dependencies still match.
The long-comparison change is confined to its comparison function; the storage
change adds the serialized equality helper while preserving the encoder and
other storage functions. This preflight does not qualify a missing report.

The regression passed all 45 checks, including actual JSON-roundtrip numerical
comparisons, recovery without new original/point calls, and the dense-error
lineage interface. It ran automatically after a worker completed and released
its lock, using one numerical thread with three reserved. Its 131 source hashes
remain verified. The separate bounded recovery launched after the parent
closed and passed its saved-data audit.

No numerical equivalence, physical bounds, calibration assumptions or prediction
target is relaxed. This remains software qualification; the 53-stretch findings
and protected confirmation data are unchanged.

[Current run](README.md) · [Frozen scope](../ilvis0-native-prefix-long/V2_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
