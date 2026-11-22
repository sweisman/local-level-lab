# All four ESA turn windows have complete timing support

The four receiver-selected turn windows each have a continuous IMU
record, 400 earlier receiver observations and 120 later timestamps.
The longest IMU interval is **3.334 ms**, below the 5 ms limit. The
first and last queries have at least **47.5 ms** of raw support beyond
them, enough for the established ±10 ms latency allowance.

| First original receiver index | Training intervals above angular trigger | Later intervals above trigger | Later triggered intervals within the planned turn block |
| --- | ---: | ---: | ---: |
| 22,936 | 10 | 2 | 2 |
| 33,796 | 0 | 9 | 9 |
| 37,516 | 0 | 10 | 10 |
| 41,116 | 1 | 14 | 14 |

The same 1°/s trigger used in the archived error check detects motion
in every selected turn. Each training slice ends before the first
scoring epoch. Two slices have no training trigger, so a separate
maneuver-error scale for each of those windows would have no training
support. A comparison should use a scale declared before scoring or
require a separate source of training information. The trigger counts
describe observed IMU motion. Consecutive intervals often belong to
the same turn.

The preflight bound **622,919** original samples and **622,915**
constructed intervals with the archived linear point-rate convention.
It also bound four training receiver weight configurations. The later
receiver positions were not decoded and no trajectory fits were run.
These receipts support a separately qualified execution with both
archived IMU error descriptions and fixed limits for forecast and
scoring work. The preflight establishes completeness and separation
of inputs. Aircraft forecast accuracy remains open.

[Selection](ESA_REPEAT_TURN_RESULT.md) · [Plan and reproduction](ESA_REPEAT_TURN_INPUT_PLAN.md) ·
[Frozen inputs](esa-repeat-turn-input-freeze.json) ·
[Exact layouts and input hashes](esa-repeat-turn-input-result.json)
