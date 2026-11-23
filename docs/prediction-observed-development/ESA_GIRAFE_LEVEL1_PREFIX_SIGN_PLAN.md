# Check the vertical sign in the saved GIRAFE prefix

The [original comparison](ESA_GIRAFE_LEVEL1_PREFIX_PLAN.md) applied the
recorded signs. On both blocks the time tags coincided at zero lag, but
every tested lag gave about 19.64 m/s² RMS of vertical force disagreement.
The size of that disagreement motivates a test of opposite vertical axes.

Use the same exact original file, processed prefix and two blocks. Before
opening the force values, fix the test as original acceleration against
the negative of processed `z-acc`. Keep the same 41 shifts, one-to-one
timestamp checks, sign-independent time support and RMS threshold from
the first plan. Estimate neither a gain nor an offset. Report the result
as a follow-up prompted by the signed comparison on the same records.

Allow one local task on one thread, one scan of at most 240,000 records
and 82 comparisons, with a 30-second limit. There are no model fits or
new recording reads. A match would identify the export convention for
these samples and leave airborne timing, attitude and horizontal forces
unqualified.
