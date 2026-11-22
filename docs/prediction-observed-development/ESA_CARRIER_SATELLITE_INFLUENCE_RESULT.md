# The carrier-phase comparison survives every single-satellite omission

On ESA development flight 187, the saved carrier path's shape score was
**−7.13**. Negative scores favor the zero-field globe over the zero-field
disc. A tie is zero. The estimates after omitting each of the 12 satellites
one at a time ranged from **−7.79 to −6.60**.

| Satellite omitted | Change in score | New score | RMS change in the later path |
| --- | ---: | ---: | ---: |
| GPS 03, largest shift toward a tie | +0.53 | −6.60 | 0.39 m |
| GPS 30, largest absolute shift | −0.65 | −7.79 | 0.54 m |

The calculation used the original 1,038 half-second steps, the same earlier
anchor and the same 120 later reports. It estimated each omission from the
range equations at the saved path, then accumulated those position changes.
This is a local estimate of the change, with the position and clock
geometry held fixed. All four tasks passed. Reconstructed range RMS agreed
with the archived value within 0.7 μm per step. The median RMS remaining
after fitting out position and clock was 3.0 mm per step.

A range error shared by several satellites can still mimic a position or
clock change. The controlled test verifies that this kind of error can
change the solution while leaving the omission residuals at zero. No
suitable nearby ground observation file was identified in the public
indexes checked. An independent accuracy estimate remains open.
[Ground reference search](ESA_GROUND_REFERENCE_AVAILABILITY.md)

The calculation ran in 12 seconds on two one-thread workers. Six focused
tests passed, including comparison with explicit fits of the reduced
linear systems. The evidence contains all satellite omissions and missed
supports, the frozen score and the checked source and input hashes.

[Frozen plan](ESA_CARRIER_SATELLITE_INFLUENCE_PLAN.md) ·
[Per-satellite results](esa-carrier-satellite-influence-result.json) ·
[Execution receipts](esa-carrier-satellite-influence-evidence/README.md) ·
[Reproduction bundle](esa-carrier-satellite-influence-evidence/bundle.zip)
