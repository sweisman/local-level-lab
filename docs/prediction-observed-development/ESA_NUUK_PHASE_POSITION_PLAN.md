# Project the later ground-corrected range residual into position

Use the [three withheld permanent Nuuk intervals](ESA_NUUK_PHASE_TRANSFER_RESULT.md),
their eleven satellites and the correction multiplier learned on the
earlier intervals. Keep the continuous aircraft path, navigation and signal
time conventions fixed. Compare the range residuals with no correction,
full ground subtraction and the earlier multiplier.

At each later endpoint, form the local satellite range derivatives. Project
each signed residual vector onto the three position directions and one free
clock. Report the equivalent north, east and up corrections, the range RMS
left over, the geometry condition and the operator norm from a uniform
per-satellite range bound to each position coordinate. Accumulate equivalent
position increments relative to the first later observation. Report these as
diagnostics of the range residuals on the saved path. They cannot measure
absolute position truth. The operator norm can translate a supported range
bound into a coordinate bound at the same geometry. This study provides no
such independent range bound.

Use one task with one setup and three later interval operations, one worker,
one thread and a 90-second cap. Use the qualified finite technical recovery
policy. Read only sealed development inputs. No new trajectory fit, new
ground file or reserved flight enters the calculation.
