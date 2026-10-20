# Common reference-acceleration component controls

Freeze **18 generated identities**: three reference-force samples, three
nonzero/zero calibration centers and two full physical domains (original yaw
range or one original yaw sector). All 27 physical calibration directions and
their original limits remain. This component is not a native propagator.

Each identity checks 64 fixed corner/interior parameter points against an
independent Rodrigues rotation/engineering-unit force formula. Compare all 27
analytic tangent columns with 54 two-sided point evaluations. Check the three
common-error vectors against their declared radii and the exact acceleration
polynomial decomposition at four clock center/slope choices, including zero,
negative and doubled slopes. Preserve every physical and all 15 auxiliary
columns in the expanded 42-column interface. Nonzero rotation, gain, bias,
gravity and time centers must use the full formula.

Acceptance: independent acceleration values within 3e-13 m/s², tangent
differences within 2e-8 m/s² per normalized parameter, polynomial identity within
3e-12 m, and normalized common vectors within 1+1e-11. These finite numerical
checks do not establish a complete floating-point enclosure. Save full vectors,
radii, derivatives, bindings and discrepancies; no failed identity may be retried.

Limits: **1,152 probe points / 972 derivative point evaluations / 4,608 polynomial
checks**, **60 cooperative seconds**, one worker with four numerical threads;
zero native evaluations, archive reads, observed fits or protected ESA outcomes.
Charge identities and reserve operations before execution. No expansions or
signals. Freeze sources/environment and deterministic point-generation seeds.
Passing permits separately frozen native construction/qualification, not
observational use or a longer fitted prediction campaign.

[Derivation](../ilvis0-reference-acceleration/PLAN.md) ·
[Duration diagnosis](../ilvis0-shared-duration-growth/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
