# Receiver differences are mostly persistent within two-minute windows

The [saved-only decomposition](PARALLEL_GNSS_WINDOW_DECOMPOSITION_PLAN.md)
uses the 195 fast-flight windows in the earlier
[receiver comparison](PARALLEL_GNSS_120S_RESULT.md). Every window passes the
mean-square identity check; two known-answer tests pass. No original receiver
file, IMU, model fit or reserved flight group was read. The
[complete result](parallel-gnss-window-decomposition-result.json) binds the
source and code hashes.

| Export against `air1` | Share of relative mean-square difference due to window mean, N/E/U | 95th percentile absolute window mean, N/E/U | 95th percentile variation around mean, N/E/U |
|---|---:|---:|---:|
| `mosaic03` | 99.3% / 98.8% / 97.7% | 9.0 / 2.7 / 7.5 cm | 0.54 / 0.43 / 1.13 cm |
| `pwrpak7` | 90.2% / 99.2% / 97.2% | 1.6 / 4.9 / 7.1 cm | 0.51 / 0.39 / 1.05 cm |

These are differences among three exports from a shared antenna, weighted
by the number of matched positions in each fixed window. A constant offset
within a window can still change between windows. The pattern supports
testing a persistent or slowly changing **receiver discrepancy** in the
aircraft error model; treating every position difference as independent
scatter would miss most of what these exports disagree about.

The decomposition does not identify which export is correct or measure an
error common to all exports. It cannot, by itself, qualify an absolute
aircraft error law, prediction coverage or an Earth-model decision.
