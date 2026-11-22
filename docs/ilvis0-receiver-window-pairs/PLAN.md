# Paired-receiver window repeatability

## Fixed question

When two primary GPS receiver streams cover the same survey leg, do they give
the same result under the already fixed receiver-only 5/10/15-second window
rule? This is a relative repeatability check for the window selector, not a
measurement of either receiver's absolute error.

## Inputs and method

Use exactly the eleven passing, sealed receiver-overlap pairs and their
hash-checked enhanced-position tables. Preserve the twelfth pair's prior strict
decoder failure as an exclusion. Match receiver rows only at identical GPS
week/millisecond tags. Use the common exact-epoch range, starting 15 seconds
after its first tag and ending 15 seconds before its last, with targets every
10 seconds. Run the existing fixed support policy separately on each stream at
the same targets. Report whether both accept, both reject, or disagree, and
whether chosen widths match. Also report paired vertical-velocity differences
at the exactly matched epochs, including their median and spread after a
constant pair offset is removed. Do not interpolate, alter the policy or choose
targets from model fit outcomes.

This comparison may reflect different antennas, lever arms, receiver
processing and shared satellite errors. Agreement cannot establish absolute
receiver accuracy, and disagreement does not by itself identify which receiver
is wrong. No IMU, fused navigation or Earth-model fit enters.

## Finite execution

Freeze the parent completion, all eleven pair identities, both table hashes per
pair, the policy, source/environment hashes and one initial start per task.
Use one worker and one numerical thread, zero native calls and a five-minute
cooperative wall ceiling. An interrupted charged task may receive at most one
separately charged technical recovery under the already qualified generic
task-resume procedure, with unchanged scientific inputs and method. Never
rerun a completed failure or a sealed success. Publish per-pair counts,
aggregate counts, source/input hashes and explicit limits of interpretation.
The seven ESA confirmation groups stay untouched.
