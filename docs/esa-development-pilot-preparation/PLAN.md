# Preparing one ESA development interval

## Fixed selection and purpose

Prepare the first nominal twenty minutes of the earliest eligible run in the
verified full-motion inventory for development recording 187. This executes
only the preparation part of the [pilot plan](../esa-development-pilot/PLAN.md).
There are no Earth-model fits, native propagations or protected-data reads.

The fixed receiver support is the first 2,401 epochs of that run. Keep actual
timestamps and report their elapsed duration; require it to be within half a
second of twenty minutes. Query indices are offsets 1, 3, …, 2,399. That gives
1,200 queries, of which the earlier 800 are training observations and the later
400 are prediction observations. Do not shift indices to obtain better motion
or model agreement. Reject gaps, changed sequences or unsupported timing.

Keep the original IMU point preceding the receiver support minus 0.05 seconds,
all following points, and the first point at or after its end plus 0.05 seconds.
This exceeds the later ±0.01-second latency sensitivity. Store original GPS
times, accelerations, angular rates, temperature and source line numbers.
Construct increments with the qualified linear-point method and actual adjacent
timestamps. Never call those constructed intervals logged increments.

## Source and error restrictions

Freeze original-file path, size, SHA-256 and established record count. Validate
current development membership against the reservation ledger before opening
either source. Read each complete file exactly once, checking its hash while
strictly decoding. Preserve original sources. Do not copy complete producer
files into publication packs; record their acquisition references instead.

Reuse the original v2 selection and its source hash. Do not rerun selection.
Use only receiver observations and gyro-independent chronology for this choice.
Unknown membership, checksum/hash disagreement, invalid layout, nonpositive
time, unsupported gap or record/count disagreement is a failure without repair.

Build both fixed working receiver-error descriptors from the earlier 800 rows
only. Keep full covariance and actual times. Do not derive uncertainty or starts
from model residuals or later positions. Store training rows separately from
post-forecast scoring rows. This preparation does not calibrate the error model.

## Finite allowance

One identity, one worker, one numerical thread, a cooperative 1,200-second ceiling
and no retries. Allow one complete receiver pass with at most 100,000 records,
one complete IMU pass with at most 10,000,000 records, and one EOF decoder call
beyond each ceiling. Reserve before decoding in blocks of at most 1,024 receiver
or 65,536 IMU calls. Unused reserved slots remain charged.

Retain at most 360,100 IMU points, construct at most 360,099 intervals once, and
build exactly two working error descriptions. Charge file passes, decoder calls,
retained sample slots, constructed intervals and error descriptions before their
work. No optimizer start or native call is authorized. Do not reuse unused
allowance from the inventory or any completed study.

## Qualification and saved evidence

Before launch, bind source/environment hashes to passing deterministic checks of
complete-stream hashing, charge ordering, finite caps, chronological indices,
support bracketing, unmodified channels, gap failures, earlier/later separation,
working covariance and explicit preparation scope. The decoder and interval
constructor must be the existing shared implementations.

Save a compact raw/constructed interval archive, original references, exact
query times and source indices, earlier training rows, separate scoring rows,
working error descriptors, source validation receipts and the charged journal.
Reports verify these saved artifacts without reopening originals or recomputing
selection. Successful preparation qualifies no model comparison by itself.

The first observed pilot still needs matched software checks and a separate
finite fitting definition. Seven confirmation groups remain protected.

[Pilot plan](../esa-development-pilot/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
