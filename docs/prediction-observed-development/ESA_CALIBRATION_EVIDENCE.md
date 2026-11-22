# ESA calibration checks and their evidence

These checks use one development flight. They compare how much sensor
calibration could change the difference between two forecasts while
still fitting earlier GPS positions. The latest replay checks four
points. A bound over the full allowed calibration range remains open.

| Check | Saved evidence |
| --- | --- |
| [Joint earlier-loss bound](ESA_LINKED_TRAINING_SUPPORT_RESULT.md) | [ZIP](esa-linked-training-support-evidence/replay.zip) |
| [Joint force map](ESA_JOINT_FORCE_SUPPORT_RESULT.md) | [ZIP](esa-joint-force-support-evidence/replay.zip) |
| [Calibration examples](ESA_CALIBRATION_WITNESS_RESULT.md) | [ZIP](esa-calibration-witness-evidence/replay.zip) |
| [Static calibration bounds](ESA_COUPLED_TRAINING_SCORE_RESULT.md) | [ZIP](esa-coupled-training-score-evidence/replay.zip) |
| [Direct score bound](ESA_DIRECT_TRAINING_SCORE_RESULT.md) | [ZIP](esa-direct-training-score-evidence/replay.zip) |
| [Bias and acceleration products](ESA_ACCELERATION_PRODUCT_SCORE_RESULT.md) | [ZIP](esa-acceleration-product-evidence/replay.zip) |
| [Eight alignment ranges](ESA_ATTITUDE_COVER_SCORE_RESULT.md) | [ZIP](esa-attitude-cover-score-evidence/replay.zip) |
| [32 smaller ranges](ESA_ATTITUDE_REFINEMENT_SCORE_RESULT.md) | [ZIP](esa-attitude-refinement-score-evidence/replay.zip) |
| [Range rejection using earlier GPS](ESA_ATTITUDE_FEASIBILITY_RESULT.md) | [ZIP](esa-attitude-feasibility-evidence/replay.zip) |
| [Remaining high-bound ranges](ESA_ATTITUDE_SURVIVOR_SCORE_RESULT.md) | [ZIP](esa-attitude-survivor-score-evidence/replay.zip) |
| [Search with one calibration per point](ESA_LINKED_PHYSICAL_SCORE_RESULT.md) | [ZIP](esa-linked-physical-score-evidence/replay.zip) |
| [Full integrating-model replay](ESA_LINKED_PHYSICAL_REPLAY_RESULT.md) | [ZIP](esa-linked-physical-replay-evidence/replay.zip) |
| [Earlier residual projection check](ESA_LINKED_FULL_LOSS_RESULT.md) | [Evidence archive](esa-linked-full-loss-evidence/README.md) |

Each ZIP contains the frozen plan, inputs, source and outcomes with
their original evidence receipt. Verify a downloaded ZIP from the
repository root using its path.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.portable verify \
  docs/prediction-observed-development/esa-linked-physical-replay-evidence/replay.zip
```
