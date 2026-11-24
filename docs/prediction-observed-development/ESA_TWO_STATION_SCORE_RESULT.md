# How much shared GPS error could two ground stations hide?

On the same 120 seconds of ESA development flight 187, a shared GPS correction large enough to close the saved model score gap would require at least one ground station to have **5.43 mm RMS** of local residual error. This applies if the two stations observe the same shared component. Their observed disagreement already requires at least **3.64 mm RMS** at one station under that assumption, even with no constraint on the score. The data alone do not establish an upper limit on either station's error.

| Required common score change | Smallest possible error at the worse of the two stations |
| --- | ---: |
| Any score change | 3.64 mm RMS |
| One full gap in the negative direction | 5.43 mm RMS |
| One full gap in the positive direction | 5.44 mm RMS |

The signed projections of the Nuuk Museum and Qaqortoq residuals were −2.38% and +1.80% of the gap. Their midpoint was −0.29%. These percentages describe the same clock-centered range direction on 1,236 matched satellite rows. A small projected residual from either receiver alone cannot rule out a larger shared component if enough local error offsets it.

The shared-component calculation does not bound how satellite errors differ between the ground and aircraft. It also leaves the aircraft antenna, position and motion errors open. The ground RMS values here concern station-local error, while the separate 2.10 mm example concerns the aircraft's covered range error. [Aircraft requirements](ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md)

The saved result includes the three common-component vectors that attain the limits. All three planned checks completed. The study used no new model fits, downloads or reserved flights. [Frozen plan](ESA_TWO_STATION_SCORE_PLAN.md) · [Signed ranges and completion receipt](esa-two-station-score-result.json)
