# Where the two remaining ESA misses occur

The steady forecast had more error than the model expected throughout its
120 reports. The turn had less error than expected during and after the
main maneuver. Neither miss is explained by a handful of bad reports.

The table shows squared standardized errors using the point input. A
well-scaled forecast would average 120 per third and 120 per axis. Those
values are descriptive references for these components.

| Window | First third | Middle third | Last third | North | East | Vertical |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 21856, steady | 164.2 | 144.8 | 182.8 | 197.2 | 117.8 | 176.9 |
| 33796, turn | 118.4 | 88.8 | 69.4 | 109.5 | 86.9 | 80.2 |

The steady window had no recorded motion exposure above the working
threshold. Its five largest reports account for 14% of its error. For the
turn, all above-threshold exposure occurs in the middle third, and the model
still assigns some additional uncertainty in the final third. The five
largest reports account for 17% of its error. A different turn with a similar
motion weight in the middle third passed the full-window reference despite a
similarly low last third. Conversely, all three other zero-exposure windows
passed the full-window reference. These comparisons give no basis for a
uniform change to the quiet or turn settings.

The axes give contributions in the fixed north–east–vertical conditioning
order. They are parts of a joint score and depend on that order. The
increment input gives the same pattern. All 16 replays match the saved scores
within 5 × 10⁻¹². The runner completed eight of eight tasks in 3.3 seconds,
with 32 charged calls and zero new fits. The original pass counts stand, and
the independent ESA flight groups remain closed.

- [Frozen diagnostic plan](ESA_PERSISTENCE_WINDOW_DIAGNOSTIC_PLAN.md)
- [Error contributions for every window](esa-persistence-window-diagnostic-result.json)
- [Verified epoch-by-epoch evidence](esa-persistence-window-diagnostic-evidence/README.md)
