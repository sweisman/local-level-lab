# Local calibration-profile check on one sealed generated path

The saved full-range joint profile moved some normalized calibration
coordinates from one existing bound to the opposite and gave large nonlinear
tangent errors. This new, separate generated-data control asks whether a
**small** correction behaves locally. Use the same sealed `straight-level`
source case and three saved fitted calibrations. Do not fit the training data
again.

Fix an exploratory trust radius of **0.1 normalized calibration units** in
every coordinate, intersected with the unchanged physical bounds. For each
physical candidate, replay the original forecast and fixed receiver error
operator, whiten the complete training/later path, save the bounded
whole-future linear profile, then evaluate the native path at that correction.
Report profile cost, correction, bound contacts and native-versus-tangent
RMS. Use the same generated later observations for all candidates, opened
only after every original forecast matches its sealed artifact. An exact
boundary adjustment under `5e-13` is permitted as in the v2 control.

One task, one worker/thread, one-hour wall ceiling, finite native-call and
packet limits, no new model-fit starts, no observed/protected flight reads.
Freeze sources, numerical environment and recovery evidence first. A local
profile that tracks the nonlinear path is only a technical diagnostic. Its
radius is not a calibrated confidence region, and future observations choose
the correction. No Earth-model decision follows from this one case.
