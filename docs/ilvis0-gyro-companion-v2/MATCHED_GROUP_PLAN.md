# Compare raw pitch rates at the same background field

Use only the 12,879 scenarios already published for the 53 selected
stretches. Verify the source receipt and complete scenario grid. Keep all
27 conservative recording groups. Use zero fits, zero original-file reads,
zero fused measurements and zero protected data reads.

The stored predictions subtract a fixed standard geographic field multiplied
by the declared removal fraction, even for the disc. For the same disc
course and assumed attitude, subtracting the full field changes the
predicted pitch rate by exactly the negative of adding the field. To
construct the disc with the specified field at each removal fraction, add
the difference between the zero-removal and full-removal disc predictions
to the original prediction. Verify the half-removal midpoint for all
three original models and check that the full-removal specified-field
globe gives the same rate as the zero-removal zero-field globe.

Compare the globe and disc at zero field and again at the specified field.
Within each pair use the same removal, roll, pitch and crab settings.
Also compare the two field choices on the globe as a separate diagnostic.
Take the difference in absolute pitch-rate errors on the same stretch.
Positive differences favor globe for shape or a specified field within
globe. Show the level, zero-crab, zero-removal case first.

Take a median over the stretches in each recording group and give every
group equal weight in the overall median. Report the range of the group
median if every group shares the same one of the 81 assumptions, then
allow assumptions to differ by group. For the latter, take the median
of the group minima and the median of the group maxima. This is exact
because the median is increasing in each argument and the groups have
separate choices on the grid. Count each group's sign at the level
reference and report how many individual group signs are fixed across
the grid. Do not pick nuisance settings for any recording.

These ranges describe this finite grid. Changing aircraft attitude,
mount error, other processing and imperfect receiver paths can lie
outside it. No values constitute calibrated confidence, independent
replications or a causal test of the field. Preserve the original
comparison and keep these rates separate from the withheld-position
forecasts and the full-position fits.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_gyro_group_replay freeze
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_gyro_group_replay check
```
