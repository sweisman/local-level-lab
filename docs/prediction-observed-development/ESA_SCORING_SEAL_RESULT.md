# Start selection reproduced before opening the score summary

The replay verified all 24 task dispositions and their recorded work
charges in the ESA development matrix. It checked each passing forecast
against its fitted parameters and exact query times. Training loss
selected the primary start for each candidate. The replay then opened
the published score summary and reproduced all **10 available primary
forecasts** and both unavailable slots, including the forecast hashes.

The scoring callback stays closed if a required disposition is missing
or if a verified fit's data-use flags, charge, fitted point or forecast
times change. A candidate stays unavailable if its selected start has
no usable forecast. Nine focused tests passed.

This checks the order of operations and reproduces past choices. The
replay read zero withheld receiver observations, ran zero fits and used
zero reserved data. Aircraft prediction adequacy still needs independent
validation.

[Plan and replay commands](ESA_SCORING_SEAL_PLAN.md) ·
[Original matched comparison](ESA_400_120_MODEL_MATRIX_INTERPRETATION.md) ·
[Verified selections](esa-scoring-seal-result.json) ·
[Source bindings](esa-scoring-seal-freeze.json).
