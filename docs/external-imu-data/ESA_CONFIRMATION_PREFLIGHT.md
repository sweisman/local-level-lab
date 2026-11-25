# Check the ESA confirmation plan before opening the recordings

Seven reserved ESA flight groups have verified timestamps. Each group
has two possible training lengths, 400 and 800 receiver reports. Both
predict the same 120 later reports. The preflight combines the group
identities, receiver and inertial slice hashes, and exact timestamp
hashes into one reproducible cohort binding.
[Timing and profiles](ESA_CONFIRMATION_TRAINING_PROFILE_RESULT.md)

From the repository root, reproduce that binding from public metadata:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_preflight
```

When the scientific rules are ready to freeze, use a JSON plan under
`docs/` with these fields:

| Field | Value |
| --- | --- |
| `version` | `esa-confirmation-preflight-v1` |
| `groups`, `cohort_sha256` | The exact values printed above |
| `training_reports` | The previously chosen training lengths, in increasing order |
| `references` | One repository-relative `path` and exact `sha256` for each of `forecast_method`, `aircraft_error_model`, `physical_adequacy`, and `decision_rule` |

Pass the path as `--plan docs/...json` to check the plan. The command
verifies file contents and group identities and reports the exact plan
hash. It reads no protected outcomes. The hash binds the proposed rules,
while scientific qualification still depends on independently supported
aircraft errors, adequate forecasts, and validation of the decision rule.
The preflight grants no permission to fit or score reserved data.
[Aircraft error evidence](ESA_INSTRUMENT_PROVENANCE.md) ·
[Decision requirements](../PREDICTION_GROUP_DECISION.md)
