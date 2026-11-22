# The four repeat-turn forecast inputs are ready to bind to execution

All 12 staged files passed a saved-only hash check. Together they hold
1,600 training receiver positions, 480 later query times and 622,915
constructed inertial intervals. The prepared files total **26.9 MiB**.
They can be regenerated from the verified originals using the bounded
preparation command. Later receiver positions are absent from the inputs.

Each window has exactly three files. One holds the earlier receiver rows,
one holds the query times, and one holds the inertial increments. The
preparer verified the full inertial arrays and the training packet prefix
against the earlier timing receipt. Both IMU error descriptions can use
the same input files.

Twenty focused checks passed across the material preparation, common
forecast engine and shared recovery code. The recovery tests verify that
resumed tasks skip sealed results, retain charged work and reject changed
source or inputs. This is verification of the shared infrastructure.
The repeat-turn forecast adapter and its end-to-end interruption check
still need their own execution qualification.

The planned development comparison uses the reference model from the
earlier covariance study and two fixed starts per IMU description in
each window. It tests errors through a turn without attempting a new
Earth-model decision. The execution manifest must bind the fit and
recovery allowances and seal forecasts before the later positions can
be decoded for scoring.

[Plan and reproduction](ESA_REPEAT_TURN_MATERIAL_PLAN.md) ·
[Preparation freeze](esa-repeat-turn-material-freeze.json) ·
[Prepared input hashes](esa-repeat-turn-material-result.json) ·
[Scoring qualification](ESA_REPEAT_TURN_SCORING_RESULT.md)
