# Check the recorded receiver clock in the Reykjavík reconstruction

The [carrier-band check](ESA_FIXED_REFERENCE_BAND_RESULT.md) finds the
same disagreement on both bands. The aircraft record contains per-epoch
offsets with a magnitude up to 0.49 ms. Its header omits the field that
should indicate whether they were applied. The fixed station supplies
that field and does not supply per-epoch offset values.
[RINEX 3.04, sections 3.3 and 6.9](https://files.igs.org/pub/data/format/rinex304.pdf)

Keep the raw timestamps, matched satellite set, initial aircraft
coordinate and satellite product. Reproduce the existing relative phase
result. Then subtract the logged offset from the aircraft epoch, from
its code measurements after converting to metres, and from each carrier
phase after converting to cycles. Verify before propagation that this
consistent transformation leaves the uncorrected signal-transmit time
unchanged to floating-point precision. Keep the original measured
matching times and compare only the computed relative displacements.

As a separately labelled sensitivity check, keep the logged epoch fixed
while removing the offset from code and phase. This represents the
possibility that the timestamps were already adjusted and the
observations were not. It is a test of an incomplete correction
convention, with no authority to choose a preferred interpretation by
agreement with the aircraft's GPS path. Report both effects and preserve
the full ten-satellite result. Use only the sealed excerpts and source
receipts. No reserved flight or independent relationship between the
two receiver error processes is assumed.

Use one task and one numerical thread. Charge one input check, 2,440
satellite states over 61 matched epochs, and 180 linear solves over 60
epochs. The 122 charge groups account for 2,621 work steps. Use the
180-second cooperative limit and one separately charged recovery attempt
with the same inputs.
