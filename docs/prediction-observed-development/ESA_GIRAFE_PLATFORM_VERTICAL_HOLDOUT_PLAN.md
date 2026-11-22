# Check the proposed platform clock on new vertical force excerpts

Two [total-force comparisons](ESA_GIRAFE_PLATFORM_TIMING_RESULT.md)
pointed to the same candidate offset. The
[horizontal check](ESA_GIRAFE_PLATFORM_COMPONENT_TIMING_RESULT.md) did
not confirm it under the tested mapping. Freeze the existing candidate
of 38,474.26739992 seconds and check the magnitude of the candidate
vertical component on three new excerpts. Use the timed cold-atom
vertical channel as the reference. This tests synchronization at the
10 Hz scale and leaves fine timing and angular-rate units separate.

Use the [bounded transfer procedure](ESA_GIRAFE_PLATFORM_TRANSFER.md)
on the same authorized platform source. Allow one one-MiB read from each
of byte offsets 466,124,214, 931,200,441 and 1,396,276,591. Each starts
512 bytes before the end of a verified previous excerpt. Require that
the first 512 bytes match exactly. Keep the full bytes and time tags.
Use complete samples with the established 1,024 Hz clock phase, and
exclude the overlap and the first two seconds after its end. Record the
available support and reasons for any rejection.

Before scoring, freeze the checked local inputs, reference hash and code.
Use the original positive-correlation rule on first differences after
tenth-second averaging, with the platform candidate vertical value taken
in magnitude. Require at least 0.70 at the fixed offset and a separately
found peak within 0.2 seconds of it in each excerpt. Store alternative
peaks and amplitude estimates. No calibration, axis permutation or clock
drift is fitted. Preserve the previous timing failures and report any
new mismatch. The excerpts all come from one development recording.

Use one local worker, one thread and at most 45 seconds for the alignment.
Allow one verified reference read, three range reads and three complete
correlation searches over at most 234,193 reference epochs each. Keep
network operations as separate approved `curl` calls and scientific
analysis on the sealed local copies. No reserved group or model fit.

The acquisition receipt binds all three one-MiB files and all 512-byte
overlaps. Its SHA-256 is
`ba900265ae8f9830370585d7ccf17ff76237afab0f98d2456f3326e1cc33357e`.
One transfer returned a control-response timeout after delivering the exact
requested byte count. The receipt retains that status. All three local
files contain complete interior rows consistent with the established
recorder clock. The vertical timing comparison remains pending.
