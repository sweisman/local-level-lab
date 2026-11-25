# Study index

Every study on this site, grouped by the question it answers. Each group opens with what it found.

**New here?** Read these four first:

1. [Verified findings](CURRENT_STATUS.md): the counts behind the headline result.
2. [How the measurement works](METHODOLOGY.md): the instruments, the models compared and how to read a result.
3. [Review of the saved fits](red-team-20261125/README.md): an attempt to break the result, and what it left open.
4. [What comes next](NEXT_STEPS.md): the checks that are running and what is still needed.

## On this page

- [The main comparison on NASA flight recordings](#the-main-comparison-on-nasa-flight-recordings). All 53 selected stretches favor the globe over the tested flat disc.
- [What the gyro record shows on its own](#what-the-gyro-record-shows-on-its-own). The recorded pitch motion, apart from the full fit.
- [Review of the result and the checks that followed](#review-of-the-result-and-the-checks-that-followed). No error found in the equations or decoding. Two of the checks it called for are still running.
- [Predicting GPS positions left out of the fit](#predicting-gps-positions-left-out-of-the-fit). Globe forecasts had lower position error than disc forecasts in four NASA flight groups and on one ESA flight. Some comparisons remain unresolved.
- [Outside records of how the NASA aircraft moved](#outside-records-of-how-the-nasa-aircraft-moved). The aircraft's own one-second records agree closely with the instrument's track and turning on 32 stretches.
- [GPS and motion error on the ESA development flight](#gps-and-motion-error-on-the-esa-development-flight). Limits on the aircraft's own GPS error are still open.
- [ESA flights held back for confirmation](#esa-flights-held-back-for-confirmation). Seven flight groups, not yet scored.
- [Testing the decision method on simulated flights](#testing-the-decision-method-on-simulated-flights). The method passed its test on simulated data. Calibration for real aircraft is open.
- [Software checks](#software-checks). Checks on the numerical solvers themselves.
- [Evidence and reproducibility](#evidence-and-reproducibility). How to verify the published results from the saved evidence.

Two terms used throughout. An **IMU (inertial measurement unit)** contains gyroscopes and accelerometers. **RMS** (root mean square) is the typical size of an error or difference. The **ESA** flights are a separate European Space Agency survey program, flown with a different aircraft and IMU from the NASA archive. [Data sources](external-imu-data/README.md)

The [detailed study record](STUDY_RECORD.md) keeps the full sequence, including failed tests, numerical recovery, and links to the original reports.

## The main comparison on NASA flight recordings

Fifty-three flight stretches from NASA's Operation IceBridge surveys were fitted under a globe and under a flat disc. All 53 favor the globe. [Findings](CURRENT_STATUS.md) · [All 53 stretches](ilvis0-current-findings-20261015/STRETCHES.md)

| Study | What it found |
| --- | --- |
| [Reading the NASA flight files (Applanix decoding)](ILVIS0.md) | Recovered the recorded gyro and accelerometer readings and the main GPS stream from NASA's files. The instrument's own combined navigation output is used only to check the decoding and to screen for steady flight. |
| [Choosing the 53 flight stretches](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md) | Selected 53 stretches totalling 424.3 minutes, using data quality, length and ground speed. All 232 files were checked. |
| [Globe or flat disc: the fitted result](CURRENT_STATUS.md) | Fitted every stretch under each model: 12 in the first pass and 41 in later reruns that repaired numerical failures. All 53 favor the globe with the specified background field under both processing assumptions. |
| [Counting related recordings once, and the comparison with no background field](analysis-provenance/NASA_ZERO_FIELD_BY_GROUP.md) | Grouped the 53 stretches into 27 sets of related recordings. With the background field switched off for both shapes, the globe fits better on 35 stretches and the disc on 18, and neither fits well. |
| [Which measurements drive the result](ilvis0-measurement-contribution/README.md) | Tested how much the gyro, accelerometer, GPS position and height readings each contribute. Force readings alone do not settle the shape. |

## What the gyro record shows on its own

These look at the recorded turning directly, apart from the full fit.

| Study | What it found |
| --- | --- |
| [The raw pitch-gyro record, plotted](ilvis0-gyro-overview/README.md) | Plots the recorded pitch turning for each stretch, with nothing fitted and no GPS added. All 53 end nose-down. |
| [Recorded pitch rates against each model's prediction](ilvis0-gyro-companion-v2/INTERPRETATION.md) | Compared the measured pitch rates with what each model predicts from GPS position alone, with nothing fitted. The globe with the specified field was closest by the median measure. |
| [The same pitch-rate check with both shapes given the same field](ilvis0-gyro-companion-v2/MATCHED_GROUP_RESULT.md) | Counted each recording group once. With the same specified field for both shapes, the globe prediction was closer across the tested assumptions. With no field, the ranking could change. |

## Review of the result and the checks that followed

A review tried to break the fitted result, then ran the checks it called for. Two more, larger gyro offsets and a disc with the background field, are [running](NEXT_STEPS.md#running-now). Its comparison with the aircraft's own flight records is listed under [outside records](#outside-records-of-how-the-nasa-aircraft-moved).

| Study | What it found |
| --- | --- |
| [Adversarial review of the saved fits](red-team-20261125/README.md) | Found no error in the equations or the file decoding, and identified three weaknesses with the checks that would address them. Ran no new fits. |
| [Selection without the navigation-status flag](ilvis0-highspeed-alignment-ablation/RESULT.md) | Repeated the published selection on all 232 files without the instrument's own alignment report. Reproduced all 53 stretches and found 16 more short intervals from a second recorder. Ran no fits. |
| [GPS-only motion of the 16 recovered intervals](ilvis0-highspeed-alignment-ablation/RECEIVER_MOTION_RESULT.md) | Fourteen of the 16 were flown as steadily as the published stretches, and two are just outside on one measure. None is fitted. |

## Predicting GPS positions left out of the fit

A model is fitted to the earlier part of a flight and must then predict GPS positions it was not shown. These are development tests. Confirmation on separate flights has not been run.

### NASA flights

| Study | What it found |
| --- | --- |
| [Forecasting later positions on four NASA flight groups](ilvis0-measurement-contribution/MATCHED_FOUR_GROUP_AUDIT_RESULT.md) | Fitted each model to the early part of a flight and predicted the rest. 15 of 16 forecasts could be scored. With the same field for both shapes, the globe had lower 3D position error in all four groups, and three globe forecasts met every position limit. |
| [The same forecast test on 20 flight groups](prediction-group-transfer/REMAINING_GROUPS_PREDICTION_RESULT.md) | 9 of 20 groups gave usable later forecasts within the earlier reference limits. The other 11 could not be scored because a fit failed its numerical check. All failures are kept. |
| [How much extra GPS error the NASA forecasts could absorb](ilvis0-measurement-contribution/MATCHED_COMMON_ERROR_MARGIN_RESULT.md) | On the three flights with complete forecasts, 1.7 to 8.2 m of added shared GPS error would bring the best forecast to its 10 m limit. Changing which model ranks first would take 39 to 63 m. |

### ESA development flight

| Study | What it found |
| --- | --- |
| [Preparing the ESA recordings](esa-development-selection-v2/README.md) | Built and checked the software for the ESA file format. Chose two test runs (393 minutes) on one development flight from GPS data alone, before looking at any gyro values. |
| [Forecasting later positions on the ESA development flight](prediction-observed-development/ESA_400_120_MODEL_MATRIX_INTERPRETATION.md) | Fitted each model to 400 GPS reports and predicted the next 120. The globe was closer in the two settings where every fit completed. Two other settings are unresolved because the disc fits did not converge. |
| [Keeping the withheld positions out of the fit](prediction-observed-development/ESA_MATCHED_SPLIT_RESULT.md) | Confirmed that fits of two different lengths end at the same moment and predict the same 120 times, with the later positions never shown to the fit. |
| [Choosing forecasts before seeing the scores](prediction-observed-development/ESA_SCORING_SEAL_RESULT.md) | Replayed all 24 development tasks and confirmed that each forecast was chosen from its fit to the earlier data, before the score summary was opened. |

## Outside records of how the NASA aircraft moved

The fits rely on the instrument's own gyros. These studies compare them with records made by other equipment on the same aircraft.

### The aircraft's own flight records

| Study | What it found |
| --- | --- |
| [Aircraft records for 2011 and 2015](ncar-aircraft-records/MOTION_MATCH_RESULT.md) | Compared the aircraft's own one-second GPS and orientation record with the instrument on 32 selected stretches. The two GPS tracks agree to about a metre across the direction of flight and sit about 0.4 s apart along it. Ran no fits. |
| [Turning at the measured time difference](ncar-aircraft-records/MOTION_LAG_RESULT.md) | Allowing for that 0.4 s, the two systems' one-second turning agrees to a median of 0.014° across the 32 stretches. Ran no fits. |

### Flight RF04 in detail

One selected stretch, on research flight RF04, was studied first and in more detail.

| Study | What it found |
| --- | --- |
| [The aircraft's own record for flight RF04](ilvis0-measurement-contribution/NCAR_RF04_INTAKE.md) | Checked in the aircraft's flight file for 12 October 2011: 443 one-second reports of orientation, GPS and air pressure covering the selected stretch. |
| [Turning: the aircraft record against the instrument](ilvis0-measurement-contribution/RF04_MOTION_MATCH_RESULT.md) | Over whole seconds, the two records of the aircraft's turning differ by 0.048° RMS. The two GPS receivers sit a steady 89 m apart along the track. |
| [Why the two GPS tracks sit 89 m apart](ilvis0-measurement-contribution/RF04_RECEIVER_OFFSET_RESULT.md) | A timing-like adjustment learned from the earlier part of the stretch cut the later difference between the two GPS tracks from 89 m to 0.49 m RMS. |
| [Direction of measured force, with outside orientation supplied](ilvis0-measurement-contribution/RF04_FORCE_DIRECTION_RESULT.md) | Using the aircraft's own orientation record, both globe settings predicted the direction of measured force more closely than both disc settings. The errors were larger than the gap between the models. |
| [The same force check, averaged over longer windows](ilvis0-measurement-contribution/RF04_FORCE_AVERAGE_RESULT.md) | Globe errors were about 0.17° RMS and disc errors about 0.30° RMS on the same 118 later windows, under both timing assumptions and both averaging lengths. |
| [Do the two GPS receivers agree on acceleration?](ilvis0-measurement-contribution/RF04_REFERENCE_ACCELERATION_RESULT.md) | They disagree mainly in the east direction: 0.075 m/s² RMS over two seconds, falling to 0.020 m/s² RMS over ten seconds. |
| [Is rounding in the aircraft file the cause?](ilvis0-measurement-contribution/RF04_VELOCITY_RESOLUTION_RESULT.md) | Rounding of the reported course is large enough to explain the east disagreement. Some of the north disagreement is larger than rounding allows. |
| [Is the distance between the two antennas the cause?](ilvis0-measurement-contribution/RF04_ANTENNA_MOTION_RESULT.md) | All six fits ran to the 42 m length of the airframe, so they give no usable correction. Part of the north disagreement remains unexplained. |
| [Checking the RF04 results from saved evidence](analysis-provenance/RF04_EVIDENCE.md) | Confirms that all seven checks use the same stretch and verifies their archived inputs, results and operation counts. They are repeated looks at one recording, not seven independent results. |

### Other sources

| Study | What it found |
| --- | --- |
| [Two flights that carried two recorders](ilvis0-measurement-contribution/MOTION_FALLBACK_RESULT.md) | Compared two recorders on the same aircraft on two more flights. All eight comparisons could be scored. A separate camera source was noted for follow-up. |
| [Averaged force readings on a two-recorder flight](ilvis0-measurement-contribution/PAIRED_GYRO_AVERAGED_FORCE_RESULT.md) | Single force readings implied more turning than the two gyros allowed in 73–78% of intervals. After averaging, none did, for all four model settings. |
| [Looking for landmarks in survey camera images](ilvis0-measurement-contribution/CAMERA_CATALOG_SCREEN.md) | Found timed images for 17 of the 53 stretches. The previews showed no fixed features that could give a separate measure of aircraft motion. |

## GPS and motion error on the ESA development flight

One two-minute comparison on the ESA development flight uses very fine satellite-range measurements. These studies ask how much GPS or aircraft-motion error could be hiding in it. "The gap" below means the difference between the two shapes' scores in that comparison. Limits on the aircraft's own error are still open.

### Ground stations near Nuuk

| Study | What it found |
| --- | --- |
| [Overview: three ground GPS stations as a reference](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Three ground stations recorded the same satellites during the ESA development flight. Comparing them with the aircraft checks some errors shared by its receivers. The aircraft's own shared errors remain open. |
| [The Nuuk Museum station, second by second](prediction-observed-development/ESA_NKAR_GROUND_SCORE_RESULT.md) | Matched all 120 one-second steps of the scored two minutes to this ground station. The difference, carried into the score, came to 2.88% of the gap. |
| [A second Nuuk station checked in](prediction-observed-development/ESA_NUUK_HIGHRATE_INTAKE_RESULT.md) | A second nearby station matched all 520 aircraft times, with at least 11 GPS satellites tracked continuously in every scored interval. |
| [How well the two Nuuk stations agree](prediction-observed-development/ESA_NUUK_NEAR_STATIONS_RESULT.md) | Two stations about 1 km apart differed by 6.49 mm RMS in second-to-second satellite range, on the 100 seconds that passed the quality checks. That leaves each station's own error, and the aircraft's, open. |
| [Why 20 seconds were dropped at the second station (carrier screen)](prediction-observed-development/ESA_NUUK_CARRIER_SCREEN_RESULT.md) | All 20 excluded seconds failed one signal check, by the same amount across satellites (the L1 Doppler check). The original comparison is left as it was. |
| [Recovering those 20 seconds (Doppler offset check)](prediction-observed-development/ESA_NUUK_CLOCK_AWARE_RESULT.md) | A separate check that allows for that common offset recovered all 20 seconds. The two stations then differed by 6.54 mm RMS over the full 120 seconds. |
| [Does a ground-station correction help the aircraft?](prediction-observed-development/ESA_NKAR_PHASE_TRANSFER_RESULT.md) | Corrections learned from each ground station in the earlier part barely changed the aircraft's later errors: less than 0.4% of the gap. |
| [How accurate would the aircraft's GPS ranges need to be?](prediction-observed-development/ESA_NKAR_ERROR_BUDGET_RESULT.md) | The nearby station covers 99.98% of what matters to the score. Under the example assumptions, that raises the allowable aircraft error from 0.62 to 0.96 mm RMS. The aircraft's actual error is not yet known. |
| [Could one shared GPS error explain the gap?](prediction-observed-development/ESA_TWO_STATION_SCORE_RESULT.md) | A shared error big enough to close the gap would require at least one ground station to carry 5.43 mm RMS of error of its own. |

### The parked aircraft at Nuuk

| Study | What it found |
| --- | --- |
| [The aircraft's GPS while parked at Nuuk](prediction-observed-development/ESA_APRON_CARRIER_RESULT.md) | With the aircraft standing still, its GPS ranges disagreed with a fixed position by about 7 mm RMS over an 18.5-second excerpt. |
| [The parked aircraft against the Nuuk Museum station](prediction-observed-development/ESA_APRON_NKAR_RESULT.md) | On 216 matched satellite range changes, the errors of the two receivers were almost unrelated (correlation 0.014). That is little sign of one shared error on this short excerpt. |
| [A longer parked interval that also has gyro data](prediction-observed-development/ESA_APRON_IMU_OVERLAP_ACQUISITION_RESULT.md) | Obtained a two-minute window at the same stop, with 241 GPS records, that overlaps the aircraft's IMU recording. |
| [The two-minute parked comparison](prediction-observed-development/ESA_APRON_IMU_OVERLAP_RESULT.md) | The aircraft and the museum station tracked the same 12 satellites. Their errors were weakly related (correlation −0.09). The aircraft's one-second gyro rates varied substantially. |
| [Checking the Nuuk results from saved evidence](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Reproduces the range and gyro summaries from the published observations and links them to one development flight. |

### The aircraft's GPS antenna

| Study | What it found |
| --- | --- |
| [Published antenna corrections](prediction-observed-development/ESA_NKAR_ANTENNA_RESULT.md) | Applying the published corrections for the satellite and ground antennas changed the two-minute score by 0.0012% of the gap. |
| [Which antenna is on the aircraft?](prediction-observed-development/ESA_AIRCRAFT_ANTENNA_INVENTORY.md) | None of the three receiver files names it. All three receivers share one roof antenna, so an error at the antenna would be common to all of them. |
| [Effect of the antenna tilting (phase wind-up)](prediction-observed-development/ESA_PHASE_WINDUP_RESULT.md) | In an ideal antenna model, each degree of tilt can change the score by at most 1.03% of the gap. The part common to all satellites cancels. |
| [Effect of the satellites' own motion (phase wind-up)](prediction-observed-development/ESA_NKAR_PHASE_WINDUP_RESULT.md) | The ideal correction changed the score by about 0.0002% of the gap or less. |
| [Could a mis-measured antenna position explain it? (lever-arm sensitivity)](prediction-observed-development/ESA_CARRIER_LEVER_SENSITIVITY_RESULT.md) | The antenna's recorded position relative to the IMU would have to be wrong by at least 40 cm to close the gap. |
| [Antenna effects through the aircraft's actual turns](prediction-observed-development/ESA_GYRO_PHASE_TILT_RESULT.md) | Using the recorded turns, an ideal antenna correction could reach 10.7% to 22.8% of the gap, depending on the starting tilt assumed. The real antenna's response has not been measured. |
| [How uneven would the antenna have to be?](prediction-observed-development/ESA_INSTALLED_PATTERN_RESULT.md) | To explain the whole gap by itself, the antenna's response would have to change by at least 5.94 mm per degree between some directions. |
| [Using only satellites above the antenna's own horizon](prediction-observed-development/ESA_CARRIER_ELEVATION_SCREEN_RESULT.md) | At least four satellites remain throughout the two minutes. With fewer satellites, the allowable range error tightens from 1.97 mm to 0.16–0.29 mm RMS. |

### Errors in the estimated flight path

| Study | What it found |
| --- | --- |
| [Using both GPS frequencies](prediction-observed-development/ESA_CARRIER_BAND_RESULT.md) | Switching from one GPS frequency to both moved the score by −4.75% of the gap on the aircraft and +1.58% at a distant ground station. The two corrections agreed weakly. |
| [Balancing GPS error against flight-path error](prediction-observed-development/ESA_CARRIER_WEIGHT_TRADEOFF_RESULT.md) | A model of smooth flight-path error raised the allowable range error from 0.16–0.29 mm to 1.35–1.71 mm RMS on the reduced satellite sets, assuming exact reference positions. |
| [The same balance with uncertain reference positions](prediction-observed-development/ESA_CARRIER_REWEIGHTED_BUDGET_RESULT.md) | Allowing one metre of error in each reference position leaves no room for extra range error in any reduced-satellite case, under the published example. |
| [Can a smooth path error reproduce the gap?](prediction-observed-development/ESA_CARRIER_MOTION_WITNESS_RESULT.md) | Paths within the example limits reproduce 47.7% to 64.9% of the gap. The search reached its step limit each time, so whether a path could span the whole gap is open. |
| [Testing the tool that bounds path error](ESA_ERROR_POLICY.md) | Verified its lower and upper bounds against cases with known answers, including when the search stops early. |
| [Upper limit on what path error can explain](prediction-observed-development/ESA_CARRIER_CONTINUOUS_BOUND_RESULT.md) | With all satellites, path error within the tested limits explains at most 50.2% of the gap. With the three reduced satellite sets, the limits still straddle the full gap. |
| [What an outside measurement would need to show](prediction-observed-development/ESA_CARRIER_ERROR_REQUIREMENTS_RESULT.md) | With all satellites, the modeled errors cannot close the gap if range error in the directions covered by the ground station stays below about 2.10 mm RMS and the other example limits hold. |

### A second satellite system

| Study | What it found |
| --- | --- |
| [Does Europe's Galileo system agree? (north displacement check)](prediction-observed-development/ESA_GALILEO_NORTH_WITNESS_RESULT.md) | The 17.6 cm north–south shift that would close the GPS gap makes the fit to Galileo satellites about 50% worse, on both aircraft receivers. |
| [GPS and Galileo limits combined](prediction-observed-development/ESA_GALILEO_JOINT_BOUND_RESULT.md) | Across the wider set of possible path errors, adding the Galileo limit changes little. Two reduced GPS satellite sets remain open under the example limits. |
| [Checking these results from saved evidence](prediction-observed-development/ESA_GROUND_REFERENCE_EVIDENCE.md) | Recomputes the two-station, Galileo and combined-limit results from the saved evidence. |

### A separate force recording on the same flight

| Study | What it found |
| --- | --- |
| [Lining up the second instrument's horizontal sensors (quartz alignment)](prediction-observed-development/ESA_GIRAFE_DIRECTION_TRANSFER_RESULT.md) | An alignment learned on the first 240 seconds left 17–18 mm/s² RMS of north–south disagreement on the next 144 seconds. That is about nine times the size of the path error in question, though the two are averaged differently. |
| [A north–south position error alone could span the gap](prediction-observed-development/ESA_MOTION_AXIS_SUPPORT_RESULT.md) | A constructed north–south error peaking at 17.6 cm spans the whole gap. The second instrument's force recording covers the same two minutes. |
| [Testing that error against the force recording](prediction-observed-development/ESA_GIRAFE_HORIZONTAL_WITNESS_RESULT.md) | The constructed error would change horizontal force by 0.37–0.71 mm/s² RMS. The force recording disagrees by at least 2.72 mm/s² RMS, and a 0.1 s timing change moves the comparison by more than the effect. Both exceed what is being looked for. |
| [Timing of the second instrument (GIRAFE clock check)](prediction-observed-development/ESA_GIRAFE_LEVEL1_AIRBORNE_RESULT.md) | Its original and processed vertical readings match exactly at the same GPS times in both airborne intervals, with the vertical sign reversed. |
| [Could a small tilt hide the difference? (tilt check)](prediction-observed-development/ESA_GIRAFE_TILT_IDENTIFIABILITY_RESULT.md) | A tilt of at most 0.0104° would make the two predicted force directions coincide. This measures how little orientation uncertainty could hide a horizontal force difference. |

### Instrument records

| Study | What it found |
| --- | --- |
| [Which IMU flew on the ESA flights](external-imu-data/ESA_INSTRUMENT_PROVENANCE.md) | All nine archived file labels point to one iMAR unit. Its original installation measurements could be used to check the fitted antenna offsets. |

## ESA flights held back for confirmation

Seven flight groups are set aside to test a fixed method later. Their timing and GPS conditions have been checked. No comparison outcome has been opened.

| Study | What it found |
| --- | --- |
| [The reserved ESA flights](external-imu-data/ESA_CONFIRMATION_RECEIVER_INVENTORY_RESULT.md) | Found ten provisional windows across the seven reserved groups, from GPS data alone. Later checks verified [IMU continuity](external-imu-data/ESA_CONFIRMATION_TIMING_RESULT.md) and [prediction times at the development cadence](external-imu-data/ESA_CONFIRMATION_CADENCE_RESULT.md) in one 20-minute slice per group. |
| [GPS conditions on the reserved flights](external-imu-data/ESA_CONFIRMATION_TRAINING_PROFILE_RESULT.md) | Compared GPS conditions in the seven reserved slices with the development window. All seven have weaker satellite geometry, and most have more change of course. |

## Testing the decision method on simulated flights

Before a decision rule is used on real flights, it is run on simulated ones where the right answer is known.

| Study | What it found |
| --- | --- |
| [Does the stated uncertainty hold on simulated flights?](prediction-validation-continuation/README.md) | Completed all 4,344 fits and passed a fixed coverage test across 181 simulated cases. The result applies to the simulated conditions only. |
| [Reference scores from saved simulated forecasts](prediction-receiver-replay/REFERENCE_RESULT.md) | Recovered 286 scores per scenario from saved forecasts, and verified how far the 13 unavailable runs limit the rankings. |
| [Re-scoring saved simulated forecasts](prediction-receiver-replay/RESULT.md) | Rebuilt the simulated GPS readings for 24 saved predictions and scored them again without rerunning any fit. |
| [How a result will be counted across flights](FLIGHT_GROUP_DECISION.md) | One result per flight group, shape first. Tested the rule, and when unfinished fits can no longer change the outcome. [Both reference methods](PREDICTION_GROUP_DECISION.md) support the stopping check. Calibration for real aircraft remains open. |
| [When remaining runs cannot change a decision](FLIGHT_GROUP_DECISION.md#when-all-queries-share-the-same-reference-draws) | Verified, on simulated scores, the point at which the remaining runs can no longer change a two-stage decision. |

## Software checks

Checks on the numerical solvers themselves.

| Study | What it found |
| --- | --- |
| [Two solvers, same answer](mixed-tangent-hybrid/ESA_DISPATCH_SCOPE_RESULT.md) | Changing solver or starting point changed none of the 384 accuracy checks on one ESA development recording. [A leaner calculation](prediction-observed-development/STRUCTURED_RECEIVER_LIKELIHOOD_RESULT.md) handles long tracks without a very large table in memory. |
| [A direct solving method on known answers](prediction-group-transfer/QR_SOLVER_REPLAY_RESULT.md) | Two direct methods each recovered all seven known targets, where the two step-by-step solvers had recovered none (direct and QR-reduced bounded least squares). |
| [A solver adjustment that did not help](prediction-group-transfer/GEODESIC_STEP_RESULT.md) | Passed 4 of 8 known-answer cases, the same four as the existing solver. |

## Evidence and reproducibility

How to verify the published results from the saved evidence.

| Study | What it found |
| --- | --- |
| [The evidence dataset](PAPER_DATASET.md) | Links every fitted and forecast result to its recording group, with checks that the saved sources and reports are unchanged. |
| [Checking the aircraft-motion results from saved evidence](analysis-provenance/AIRCRAFT_MOTION_EVIDENCE.md) | Verifies the saved timing, tilt and two-recorder results on one ESA and two NASA flights, including two attempts that were stopped. |

[The current plan](NEXT_STEPS.md) explains what is left. The [stationary ground experiment](STATIONARY.md) is a separate consumer-IMU project in development.
