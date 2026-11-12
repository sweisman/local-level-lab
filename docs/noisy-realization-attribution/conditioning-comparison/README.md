# Receiver conditioning on the same noise model

This generated-data comparison used one fixed rotating-globe trajectory, known calibration, and one recorded-increment error operator. It did not use an aircraft recording or fit an Earth model.

The later 400 receiver epochs have an **unconditional** horizontal RMS error scale of 717.66 m and height scale of 30.93 m. After conditioning on 800 earlier receiver epochs, the corresponding scales are 33.77 m and 1.95 m.

Both scales are expected error sizes, not one realized forecast error. This resolves the information-footing mismatch with the earlier 33.77 m conditional benchmark. It does not establish a calibrated prediction interval or an Earth-model decision.

The saved operator, charge record and variance curves were checked against the sealed study result. See [the finite plan](PLAN.md) for the exact input and limits.
