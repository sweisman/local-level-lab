# What changes with a second GPS receiver?

Four saved forecasts could be scored against both GPS receivers on part of
their later paths. After removing the receiver offset measured earlier, the
second receiver changed horizontal RMS error by at most **0.12 m** and height
RMS error by at most **0.32 m**. These are the same specified-field globe
forecasts already scored in the [20-group transfer study](REMAINING_GROUPS_PREDICTION_RESULT.md).

| Flight group | Shared later epochs | Last shared second / full forecast | Horizontal RMS, onboard / second adjusted | Height RMS, onboard / second adjusted |
|---|---:|---:|---:|---:|
| `ilvis0-2476b9083406f038` | 167 | 167 / 182 | 3.18 / 3.23 m | 3.48 / 3.79 m |
| `ilvis0-6f070af93fb0534d` | 150 | 150 / 183 | 1.49 / 1.48 m | 6.76 / 6.74 m |
| `ilvis0-80a514772c83aedc` | 141 | 141 / 181 | 1.68 / 1.72 m | 3.23 / 3.29 m |
| `ilvis0-b0c65cb8ca1686d40980` | 42 | 42 / 187 | 0.037 / 0.149 m | 1.33 / 1.55 m |

All four comparisons start one second after the training cut. Together they
cover 500 of the 733 forecast epochs. The largest changes before adjustment
were about 0.32 m horizontally and 0.61 m in height. In the shortest overlap, receiver
choice moves the horizontal result from centimetres to decimetres even after
adjustment. Metre-scale height error persists with both receivers.

The inventory retains all twenty groups. Eleven had no verified companion
receiver, four had a companion but no passing later forecast, and one had a
passing forecast and companion but no shared later epochs. None of the four
scored companions reached the original forecast end. Both receivers can share
positioning errors. The partial comparison leaves full-horizon accuracy,
absolute error and other model rankings open.

The replay reads frozen receiver tables and forecasts and uses zero new fits,
original-file decodes or position solves. Run it from the repository root in
the frozen Python environment.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_group_companion_receiver replay
```

[Method](COMPANION_RECEIVER_PLAN.md) · [Input and source hashes](companion-receiver-freeze.json) ·
[All 20 dispositions and receiver scores](companion-receiver-receipt.json)
