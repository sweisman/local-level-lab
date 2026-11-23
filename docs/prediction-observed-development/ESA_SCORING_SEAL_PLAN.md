# Verify forecast selection before scoring access

Use the 24 sealed tasks from the existing ESA 400/120 development study.
Verify the complete task list, each saved disposition and its work charge.
For each passing forecast, check the original timestamp support, the
earlier-only data flags and the fitted parameter binding. Select the
converged start with the lowest earlier training loss, breaking ties
by start number. Keep a candidate unavailable when its selected start
has no verified forecast.

Open the previously published score summary only after this check returns
the selections. Compare its saved primary starts and forecast hashes with
the new training-only selections. This is a replay of archived choices.
It does not open actual withheld receiver values, repeat any fit, or
change the published summary.

Allow one closed archive, 24 sealed dispositions, one published score
summary, one thread and zero new fits. The known-answer tests check
that missing tasks, changed charges, later-data use, wrong times, and
a wrong fitted point stop the scoring callback before it is called.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_scoring_seal_check freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_scoring_seal_check check
```
