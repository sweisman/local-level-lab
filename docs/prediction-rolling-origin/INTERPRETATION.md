# Can earlier forecast error predict later error?

**A single multiplier does not describe these three development recordings.**
The frozen study completed all 48 planned fit starts. Thirty-four passed their
numerical stopping checks; fourteen did not. None was lost to an execution
error. After choosing each start by its **earlier training cost**, eight of
twelve clock/processing settings have a passing fit at both prediction cuts.
The other four abstain.

Each matched setting compares two forecasts of the same length from one
recording. One fit uses the first third of receiver positions and forecasts
the next third. A separate fit uses the first two thirds and forecasts the
final third. The scoring positions were opened only after the forecasts were
saved. The table gives the range of **later error divided by earlier error**
among matched settings; 1 means equal root-mean-square (RMS) error.

| Recording | Matched settings | North | East | Height |
|---|---:|---:|---:|---:|
| A: southern IMU8 survey | 2/4 | 1.49–2.60× | 0.64–0.71× | 0.97–0.99× |
| B: northern IMU21 survey | 4/4 | 0.44–0.53× | 0.26–0.83× | 2.40–2.43× |
| C: southern IMU21 survey | 2/4 | 2.23–4.09× | 0.33–0.69× | 2.58–2.67× |

The pooled medians—1.01× north, 0.67× east and 2.42× height—hide these
opposing patterns. In B, north error shrinks while height error grows; in C,
north and height both grow. The clock and processing settings reuse each
recording, so eight matched settings are not eight independent flights.
Three settings abstain because the later-cut fits fail numerical checks; one
abstains at both cuts. All 34 passing fits have three to five normalized
calibration parameters at their declared bounds. These are fit diagnostics,
not measured sensor limits or evidence of an instrument defect.

These three recordings do not calibrate a **single earlier-to-later RMS
multiplier** as an uncertainty limit for the archive. They do not rule out a richer
error law that accounts for time, direction, motion and fitted calibration.
The next gate is an error model estimated from earlier observations and
checked on independent flight groups, with physical-position and future
receiver-report coverage assessed separately. Fourteen nonpassing numerical
fits and active calibration bounds remain part of that assessment.

The study used only three previously selected NASA development recordings,
the specified-field globe candidate, and their prepared inertial and primary
receiver streams. It made no new globe/disc decision and read no reserved ESA
confirmation flight. The original 53-stretch model comparisons are unchanged.

[Verified study result](RESULT.md) · [All twelve settings](result.csv) ·
[All 48 fit starts](fit-audit.csv) ·
[Recording identities and selection](../ilvis0-prediction-pilot-preparation/selection.csv) ·
[Frozen plan](PLAN.md)
