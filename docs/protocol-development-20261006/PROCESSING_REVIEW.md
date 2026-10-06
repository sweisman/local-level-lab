# Why the revised procedure failed its checks

An **IMU (inertial measurement unit)** measures turning and acceleration. To interpret its
small level-flight signal, the analysis must know how its axes point relative to the aircraft.
This review used the saved 72-case results and small, independently constructed motion examples.
It ran no new flight simulations, nonlinear fits, bootstrap or calibration.

## Two separate losses of information

The analysis first removes signals that allowed IMU errors or wind could imitate. It then
keeps only sufficiently strong independent combinations of the remaining model signals.
That second step uses a fixed numerical cutoff. A comparison can lose useful information
at either step; changing the cutoff would change the method being validated.

| Procedure / wind description | Enough information before the cutoff | Enough after it |
|---|---:|---:|
| Original / dynamic crab | 18/18 | 18/18 |
| Original / explicit wind | 14/18 | 9/18 |
| Revised / dynamic crab | 18/18 | 0/18 |
| Revised / explicit wind | 0/18 | 0/18 |

Here, “enough” means that every required model comparison passes the same frozen retention
threshold at every model anchor. It is not a calibrated decision or a guarantee of useful power.
The revised dynamic-crab failures arise at the cutoff. Its explicit-wind failures already
have insufficient information before that cutoff. Lowering the cutoff alone cannot solve both.
No magnetic-watchdog segments were excluded in any of these 72 cases.

## Turning the IMU while the aircraft turns

The revised schedule places an IMU turn at minute 20, exactly when the simulator begins its
first aircraft turn. The aircraft-turn clock includes an initial five minutes and the time
spent making each previous turn; it does not follow the nominal leg boundaries alone.

The software integrates the gyroscope during a deliberate IMU turn to recover its new facing
direction. The gyroscope sees both the hand movement and aircraft motion. In an independent
example, a known 180° hand turn overlapping aircraft yaw of 3° per second produces about 15°
of mount-mapping error. No data-gap warning catches it because the measurements are complete.
Another example with overlapping bank motion produces about 7.5° of mapping error.

Without overlap, the same independently constructed examples recover the mount change and
forward direction accurately. The basic conversion between coordinate frames agrees with
independent rotations to numerical precision. These checks isolate a timing hazard, rather
than a general sign or axis error.

The revised campaign's estimated horizontal forward direction differs from the nominal mount
direction by 4.82–5.21°, compared with under 0.2° for the original procedure. Its reported
direction uncertainty is about 1.5°. This comparison is diagnostic: nominal mount geometry
does not capture every pitch, bank or accumulated reconstruction error. Saved summaries omit
the raw readings and mount matrices needed to reconstruct the historical error exactly.
The overlap has not been shown to cause every campaign failure.

## A concrete candidate for the next check

A timing-only revision moves the six IMU turns to minutes **5, 25, 40, 55, 70 and 80**,
while preserving the proposed 90-minute route. It meets the existing spacing rule and avoids
all known aircraft turns, including the integration padding. It has not been optimized or
tested through the complete recording and analysis process.

Small calculations using the aircraft-turn timeline and known IMU axes pass all model anchors
under both wind descriptions with that schedule. The worst retained fraction is about 0.327,
against a threshold of about 0.312: a narrow margin. Those calculations use approximate route
geometry and coarse exclusions, so the earlier lesson still applies: a promising simplified
calculation is insufficient to approve a flight protocol.

Before another flight campaign, define how overlapping turns will be detected and how uncertain
orientation will cause abstention. A later, separately budgeted comparison should retain raw
recordings, processed bins and mount matrices so the effect can be isolated directly. It should
compare timings using paired inputs without relaxing the wind model or information cutoff.
Fresh calibration remains premature until a usable protocol and its acceptance rules are fixed.

The reproducible audit tool is [audit_processing.py](../../analysis/tests/audit_processing.py).
Its saved technical output belongs to this campaign's separate research record. Eight focused
checks cover independent rotations, clean and overlapping maneuvers, schedule timing and the
two stages of information loss. Historical campaign results remain unchanged.
