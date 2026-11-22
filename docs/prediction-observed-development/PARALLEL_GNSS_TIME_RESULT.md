# Parallel receiver positions at one common time

This exploratory comparison removes the position shift expected from each submillisecond timestamp difference using that export’s reported velocity. It uses only the 400 earlier training epochs of the opened ESA flight. No later reports, protected flights or IMU samples were examined.

| Other export | Matched times | Raw north/east/up RMS (m) | Time-adjusted north/east/up RMS (m) |
| --- | ---: | ---: | ---: |
| mosaic03 | 400 | 0.011/0.022/0.027 | 0.012/0.016/0.028 |
| pwrpak7 | 400 | 0.008/0.021/0.035 | 0.007/0.007/0.035 |

The adjustment is a local first-order approximation. The receivers share an antenna and may share PPP processing errors. The adjusted differences also persist across seconds: their per-axis lag-one correlations range from 0.70 to 0.86. The remaining differences measure relative agreement; they cannot prove absolute accuracy, qualify the full prediction-error law or decide an Earth model.

[Fixed method](PARALLEL_GNSS_TIME_PLAN.md) · [Detailed result](PARALLEL_GNSS_TIME_RESULT.json).
