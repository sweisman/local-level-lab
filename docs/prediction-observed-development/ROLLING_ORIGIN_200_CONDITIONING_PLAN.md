# Receiver conditioning for the 200/120 development cut

The 200/120 fit study is running. Once **both** of its outcomes are sealed,
condition each passing forecast on only receiver reports 0–199. Construct the
same fixed-law covariance operator used for the earlier 400/120 check. Keep
the fitted physical and calibration parameters fixed; do not optimize again.

Each passing law (`increment` or `point`) receives its own task with at most
450,000 native calls and 1,000,000,000 packet visits. The study reserves at
most two workers at one numerical thread each and has a two-hour original wall
ceiling. Freeze source, environment, inputs, finite recovery and a generated
replay check before launch. Any failed fit stays failed and receives no
conditioning task.

The conditioning workers receive the 200 earlier positions, all 320 report
times, sealed fit artifacts and IMU increments through the forecast horizon.
They do **not** receive positions 200–319. After all permitted conditioning
tasks seal, compare their predictions with those separately held positions.
Publish raw and conditioned horizontal/height errors, signed axis errors,
nominal interval coverage and temporal correlation. Do not select a law from
the withheld outcome or call marginal report counts independent trials.

This remains a same-flight temporal-transfer development test. It does not
qualify the aircraft prediction-error law, independent-flight coverage or an
Earth-model detection. The seven reserved ESA groups remain closed.
