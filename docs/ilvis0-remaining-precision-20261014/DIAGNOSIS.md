# Saved failure diagnosis

All twelve current unfinished stretches remain selected by the original motion and receiver criteria. This audit reads saved stopping probes and histories; it runs no native prediction or fit.

| Stretch | Stage | Failed primary model/case | Remaining gate |
|---|---|---|---|
| `2a56eb8fa7d4e10c9a867bb0` | budget | sphere_rotating / bias1_unsubtracted | endpoint_stationarity |
| `7df21c836bec5751f83c0cce` | budget | flat_still / bias1_unsubtracted | relative_cost |
| `fd7b81e48a4122b149c4925b` | budget | sphere_still / bias1_profiled_removal | relative_cost, position_rms_east, position_rms_down |
| `013fdb894ff28509889a8896` | remaining | sphere_rotating / bias1_unsubtracted | endpoint_stationarity |
| `013fdb894ff28509889a8896` | remaining | sphere_rotating / bias1_profiled_removal | endpoint_stationarity |
| `0e73879f98c3b701fd7c42df` | remaining | sphere_still / bias1_unsubtracted | endpoint_stationarity |
| `0e73879f98c3b701fd7c42df` | remaining | sphere_still / bias1_profiled_removal | endpoint_stationarity |
| `370cec66878c4c1cf84b4ceb` | remaining | flat_still / bias1_unsubtracted | position_rms_east |
| `370cec66878c4c1cf84b4ceb` | remaining | sphere_rotating / bias1_profiled_removal | endpoint_stationarity |
| `50f24131843071ae9312c082` | remaining | sphere_still / bias1_unsubtracted | endpoint_stationarity |
| `50f24131843071ae9312c082` | remaining | sphere_rotating / bias1_profiled_removal | relative_cost |
| `9f4d888995ab94bb8eff4df6` | remaining | flat_still / bias1_profiled_removal | position_rms_down |
| `b4e44ddc0f130ecd45674c78` | remaining | sphere_rotating / bias1_profiled_removal | endpoint_stationarity |
| `bb8061a43b4f14b6262ceda1` | remaining | sphere_rotating / bias1_unsubtracted | relative_cost |
| `bb8061a43b4f14b6262ceda1` | remaining | sphere_still / bias1_unsubtracted | endpoint_stationarity |
| `bb8061a43b4f14b6262ceda1` | remaining | sphere_rotating / bias1_profiled_removal | relative_cost |
| `bb8061a43b4f14b6262ceda1` | remaining | sphere_still / bias1_profiled_removal | relative_cost |
| `da346f70a6661ee42cecea19` | remaining | sphere_rotating / bias1_unsubtracted | endpoint_stationarity |
| `e6629f14d2e03e471a446e06` | remaining | flat_still / bias1_profiled_removal | position_rms_down |

The nine earlier exclusions combine nonstationary endpoints and unstable receiver predictions. Wider arithmetic with a separately finite allowance is a tested numerical alternative, not a guarantee of recovery. Calibration bounds and physical models stay fixed; failures do not favor either geometry. The saved vertical RMS gate uses a legacy `down` label for unsigned receiver-local vertical changes.
