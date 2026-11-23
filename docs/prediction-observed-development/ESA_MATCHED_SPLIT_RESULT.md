# Both training lengths can use the same withheld times

On ESA development recording 187, the receiver reader prepared a
400-report input and an 800-report input. The shorter input reproduced
the last 400 rows of the longer one, down to their original file line
numbers. Both ended at receiver index 10,635 and supplied identical
timestamps for the following 120 queries. All indices start at zero.

The reader verified the complete receiver file on both passes. It
constructed both existing receiver weighting policies from each split's
earlier observations. The two fits would receive different training
blocks and the same withheld times. The later coordinates and covariance
values never reach the fitting input. A test supplied invalid text in
those later fields and reproduced the original fitting inputs exactly.

All 47 focused tests passed. The first frozen replay stopped because the
subset parser returned relative line numbers, causing the nested rows
to compare unequal. The corrected replay passed with the same source,
times and limits. Both attempts remain recorded. No new fits ran, no raw
inertial values were read, and no reserved group was opened. The choice of
training length and the aircraft error law remain open.

[Replay plan and commands](ESA_MATCHED_SPLIT_PLAN.md) ·
[Provenance correction](ESA_MATCHED_SPLIT_CORRECTION.md) ·
[Verified split hashes](esa-matched-split-v2-result.json) ·
[Corrected freeze](esa-matched-split-v2-freeze.json).
