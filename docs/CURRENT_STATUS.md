# Current airborne analysis status

**53 with the specified-field globe preferred, 0 flat-disc preferences, 0 without a consistent preference** among 53 selected stretches.

The selected stretches total **424.3 minutes**. The same preselected intervals and original measurements are retained through numerical recovery.

| Current disposition | Stretches |
|---|---:|
| Globe preferred | 53 |
| Specified flat disc preferred | 0 |
| Unresolved | 0 |
| Different preferences across assumptions | 0 |

Of the globe-preferred stretches, **53** also favor the specified background rotation field over zero field under both processing assumptions. That comparison does not identify the field's physical cause or distinguish a solar from a sidereal day.

The specified-field globe has the lowest cost in both cases on **53** stretches. Among the two zero-field fits, the disc costs less in both cases on **18** stretches.

These are fitted model preferences. Calibrated statistical confidence for aircraft remains open. The ledger value `scientific_decision = abstain` records that distinction. Overlapping recordings and shared instruments mean stretches cannot be counted as independent replications. An unresolved comparison has not passed its required calculations and checks; it supplies no opposing shape finding.

| Cohort | Completed comparisons | Saved repeat passes | Repeat unscheduled or not saved | Other repeat status |
|---|---:|---:|---:|---:|
| Original pass | 12 | 0 | 12 | 0 |
| Later numerical studies | 41 | 41 | 0 | 0 |

Repeat counts describe the latest saved status for each stretch. The later studies used stage-specific checks.

[Findings and source tracks](ilvis0-current-findings-20261015/FINDINGS.md) · [All selected stretches](ilvis0-current-findings-20261015/STRETCHES.md) · [Comprehensive metadata](ilvis0-current-findings-20261015/ANALYTICS.md) · [Next steps](NEXT_STEPS.md)

## Evidence and history

This snapshot is generated from published, hash-verified result ledgers and their qualified per-stretch comparisons. It excludes active workers and incomplete publications. The original [first-pass report](ilvis0-highspeed-segments-20261008/FINDINGS.md) and preserved trial reports describe their own historical stages; their earlier totals remain unchanged.

Snapshot receipt SHA-256: `8a2165c80a4a524b66dc75e86a171dfe5be9a525c41331381282e5a4edadade3`.

Reproduce with `~/venv/bin/python docs/build_current_status.py`; `--check` verifies the evidence and checks this page and the landing-page excerpts without writing. Only published metadata is read; no original IMU files, model refits or numerical predictions are needed.
