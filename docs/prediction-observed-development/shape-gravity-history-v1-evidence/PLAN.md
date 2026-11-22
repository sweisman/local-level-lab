# How the height-aware bounds grow with history

Check whether the shared-prefix interval calculation is a practical way to
test the [4.03 cm position-error target](SHAPE_REMAINDER_METRES_RESULT.md).
Use generated motion for the zero-field globe and zero-field disc. Use
160 packets per model and grid, with report times near packets 20, 40,
80 and 160. The 5 ms grid tests packet-rate arithmetic. The 250 ms grid
is a deliberately coarse test of longer elapsed time.

Use a fixed normalized calibration box of ±0.1 around the reference.
Compare the four reference positions with the compiled height-aware
integrator and check the reported remainder at three prescribed settings.
Preserve the 27 physical and 24 auxiliary columns in the comparison.
Report the largest position remainder in each direction at each time.
Flag where the bound exceeds the four-centimetre target, even when the
reference and trial comparisons pass.

Allow one worker and one thread, one bound and four native calls per task,
and at most 640 packet steps per bound. The runner has a two-minute wall
allowance and each bound has a 25-second cooperative allowance. Retain
sealed failures and the work charged before them. The run reads no aircraft
recordings or reserved groups and performs no fits.

A useful bound here would justify testing a longer generated history.
A wide bound identifies where to improve the calculation. The generated
box and coarse packets do not establish a bound over the training-feasible
calibration region of any recording.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.shape_gravity_history
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/shape-gravity-history-v1-20261119 --reserved-threads 0
```
