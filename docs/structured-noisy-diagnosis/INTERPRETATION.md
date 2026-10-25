# What the calibration check found

**The short forecasts are accurate, but their calibration is not uniquely
established.** All 24 generated fits reach calibration limits even though the
planted sensor settings lie inside the allowed ranges. These are software
examples, not measurements of an instrument's true errors.

The same five limits appear in every fit: vertical accelerometer offset,
sideways accelerometer gain, gravity adjustment, vertical gyro offset and
forward-axis gyro gain. The clock offset reaches a limit in 20 fits.

The saved position derivatives show a strong trade-off: the gravity adjustment
and vertical accelerometer offset have almost opposite effects, with column
cosines from −0.999958 to −0.999955. Vertical accelerometer gain and gravity
have almost aligned effects, from +0.999955 to +0.999958. Changing these
parameters together can leave nearly the same predicted track. These are
local derivative relationships, not posterior correlations or proof of a
globally unique solution. The vertical gyro bias/gain columns do not show
the same near alignment; their cosines are about 0.29–0.39.

The two starts give nearly identical costs: the largest difference is
0.0000000052. That supports numerical repeatability for these examples;
it does not establish correct sensor calibration. All settings share one
configured noise seed and cannot be counted as independent replications.

Four fits remain numerically unfinished. Each passes the stationarity and
physical position-change checks but misses the relative cost-change limit
of 0.00000001. Their values are about 1.1–5.8 times that threshold. They stop
after 51–53 evaluations out of 200, so this is not budget exhaustion.
Their original failure labels remain unchanged.

The next step is to test uncertainty calculations that retain the whole
permitted calibration region, including boundaries and weak directions.
The existing bounded-prediction library already supports such regions in
linear controls. Connecting it to the new accumulated-error operator needs
separate qualification. Applying it to nonlinear fits also requires a justified
approximation-error allowance; accurate point forecasts alone do not supply one.

This saved-data diagnosis used no new fits, noise draws, aircraft recordings
or protected confirmation data. The original twenty-minute noisy failure
and the 53-stretch findings are unchanged.

[Result tables](README.md) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
