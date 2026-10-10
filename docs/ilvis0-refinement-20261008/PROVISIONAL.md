# Provisional findings from six NASA recordings

**Two recordings consistently favored the globe models over the specified flat disc;
four remained unresolved.** In the two resolved recordings, the rotating globe also
fit better than the still globe under every tested assumption.

**The available pilot comparisons point toward globe, rather than equal support for
globe and flat.** Two further recordings have globe-favoring partial comparisons,
and the remaining two have no completed shape comparison. None has a resolved preference
for flat. The [completed selected-stretch study](../ilvis0-highspeed-segments-20261008/FINDINGS.md)
subsequently found 12 complete globe comparisons, zero complete flat comparisons and
41 unfinished comparisons. All 12 globe results also favor rotation.

The pilot used the same saved IMU and receiver observations for all three models. Each
recording had four matched cases: constant gyro-offset allowances of ±0.1 or ±1 degree/hour,
with Earth-rate removal either absent or fitted. There were 72 model fits in total.

## Model comparisons and unfinished calculations

**40 fits converged; 32 did not.** No fit returned a numerical or framing error.
There were 73 charged starts, including one interrupted attempt; every completed fit
was retained. A fit adjusts the permitted instrument and motion parameters to match the
recording. Convergence means those adjustments passed the numerical stopping checks.
**It does not mean the model describes the recording well.** A converged flat-disc fit
can still have much larger errors than a converged globe fit. The model comparison uses
the quality of the matched fits, rather than counting how many calculations finished.
Convergence also does not establish a global optimum or validate the error assumptions.

| Recording | Calculations passing stopping checks | Shape comparison | Rotation comparison |
|---|---:|---|---|
| 14 April 2009, LVIS POS AV | 1/12 | Unknown | Withheld |
| 16 September 2014, POS 510 | 9/12 | Unknown | Withheld |
| 26 October 2010, LVIS POS 510 | 12/12 | Globe in all four cases | Rotating globe in all four cases |
| 20 November 2010, LVIS POS 510 | 2/12 | Unknown | Withheld |
| 24 September 2015, LVISGH POS 510 | 12/12 | Globe in all four cases | Rotating globe in all four cases |
| 20 September 2017, B200T 510i | 4/12 | Unknown | Withheld |

The [audited results](RESULTS.md) identify the exact original filenames.
No recording had a resolved preference for the flat disc. The four unknown results
are not votes for either shape: at least one required optimization remained unfinished.
Rotation is withheld for them rather than interpreted from incomplete comparisons.

### What do the partial results lean toward?

| Indeterminate recording | Available comparisons between converged fits |
|---|---|
| 16 September 2014 | Still globe fits better than flat in all four cases. The rotating-globe comparison also favors globe in the one case where that fit converged. |
| 20 November 2010 | Rotating globe fits better than flat in the ±0.1°/hour, no-removal case. The other cases have no converged shape pair. |
| 14 April 2009 | Only one flat fit converged; no matched shape comparison is available. |
| 20 September 2017 | Each case has only one converged globe fit; no matched shape comparison is available. |

Thus the available shape pairs in two indeterminate recordings lean toward globe.
The other two cannot supply a defensible lean. These partial comparisons retain useful
diagnostic information, but do not override the requirement for all necessary fits or
turn an unfinished optimization into evidence against a model. Rotation remains withheld.

## Numerical completion under different assumptions

The counts below describe solver completion, **not support for an Earth model**.

| Constant gyro-offset allowance | Assumed Earth-rate removal | Converged fits |
|---|---|---:|
| ±0.1°/hour | None | 12/18 |
| ±0.1°/hour | Unknown amount fitted | 9/18 |
| ±1°/hour | None | 10/18 |
| ±1°/hour | Unknown amount fitted | 9/18 |

Each model had 24 attempted calculations. Twelve rotating-globe calculations, 14 still-globe
calculations and 14 flat-disc calculations passed the stopping checks. Those similar counts
do not mean the models fit equally well: both recordings with complete comparisons favored
globe, and then rotating globe, in every case. They retained the same shape and rotation
preferences when the assumed gyro-offset allowance changed or possible Earth-rate removal
was introduced. Neither smaller bounds nor additional processing freedom solved the
other recordings' convergence problems.

Converged fits used a median of 124 evaluations; unresolved fits used a median of 200.
Twenty-three of the 32 unresolved fits used the full 200-evaluation allowance.
These differences describe solver behavior, not instrument quality or evidence against
an unfinished model. They do not justify dropping the unresolved recordings.

## What limits the finding?

Every fit in the two fully converged recordings touched at least one assumed parameter
limit. Their preferences therefore need further checks of those limits and model adequacy.
The rotating-globe fit's position residuals also differed substantially between recordings:
roughly 0.2–4.9 metres horizontally on 26 October 2010, versus 6.7–19.8 metres on
24 September 2015, across the tested cases and horizontal axes. A relative winner can still fit
the observations inadequately.

The IMUs are professional survey instruments with published performance information.
The outstanding checks concern the remaining calibration offset, exact onboard corrections,
integration clock and receiver errors. A raw increment stream can include ordinary sensor
filtering without losing slow turning; passing the fit does not prove an absence of onboard
corrections. Fit differences have not been converted into validated significance levels.
These are six recordings with repeated fits of the same observations, not 72 independent trials.

The larger analysis uses permanently selected high-speed stretches and two wider-offset
processing cases. Its [findings](../ilvis0-highspeed-segments-20261008/FINDINGS.md) compare
fully completed and unfinished stretches, including duration, speed and IMU record type.
Both studies' complete comparisons favor globe and rotation. Their unfinished calculations
do not supply equal support for flat Earth.

Full numerical evidence is preserved in [fit diagnostics](fits.csv),
[shape comparisons](shape.csv) and [rotation comparisons](rotation.csv).
