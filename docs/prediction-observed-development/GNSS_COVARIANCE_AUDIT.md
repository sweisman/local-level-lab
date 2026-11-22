# GNSS covariance and time-dependence audit

The original GNSS-only PPP export was hash-verified and matched to all 400 sealed earlier receiver reports. Parsing stopped before the withheld reports. Its printed north/east/up covariance fields were assembled as matrices without changing the sealed fit input.

Position matrices with a negative eigenvalue: 0/400. Velocity matrices: 0/400. A valid matrix is not proof that its reported uncertainty covers actual receiver error.

| Axis | Position-derivative minus velocity RMS (m/s) | Median reported position SD (m) | Median reported velocity SD (m/s) | Lag 1 | Lag 10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| north | 0.0161 | 0.0327 | 0.8571 | 0.154 | -0.048 |
| east | 0.0071 | 0.0202 | 0.5502 | 0.199 | -0.014 |
| up | 0.0358 | 0.0449 | 1.1935 | -0.380 | -0.022 |

The export header labels position covariance in m² and velocity covariance in m²/s², so the printed square roots have m and m/s units respectively. Their empirical coverage is unverified. The position and velocity come from the same PPP solution. A small difference between them does not establish that either reported uncertainty is conservative. Their missing cross-time and cross-field covariance prevents a valid normalized significance test or an aircraft motion-error bound. This check does not qualify forecast coverage or an Earth-model decision.

[Fixed method](GNSS_COVARIANCE_AUDIT_PLAN.md) · [Detailed result](GNSS_COVARIANCE_AUDIT.json).
