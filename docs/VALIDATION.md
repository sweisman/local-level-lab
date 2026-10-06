# What still needs validation?

An **IMU (inertial measurement unit)** measures turning and acceleration. This experiment aims
to use its slow turning measurements during level flight to distinguish a rotating globe,
a stationary globe and a stationary flat disc. Different predictions alone are not enough:
the actual recordings must separate them despite IMU errors and aircraft motion.

The app and analysis tools are implemented. The project is still developing and checking the
scientific method. Successful software tests and simulated recordings do not establish that
a real IMU can deliver the required measurements or that the final decisions are reliable.

## What has been checked?

The software can decode recordings, retain interruptions and instrument settings, guide
calibration and compare measurements with model predictions. Automated checks cover the model
calculations, timing, uncertainty calculations, recording integrity and analysis rules.

Two development campaigns of 1,000 simulated flights each are complete. The first included
one accepted case that wrongly rejected its generating model under the provisional rule.
The second included none among its accepted cases. Their settings differ, and these findings
cannot be combined into a claim about a final error rate. The runs helped identify problems
and choose further tests; they were not independent validation of a finished method.

Later work asked whether the flight route and IMU-turn schedule actually leave enough
separating information. A 300-case study found no geometry that passed every required comparison
under both ways of allowing for wind. The subsequent audit found a numerical dependence on
parameter units and corrected it. It also found that short legs can lose their qualifying
cruise, slowly changing IMU errors can absorb model signals, and protective mount checks can
remove otherwise useful data.

A fresh 72-case comparison finished in about nine minutes. Every case returned a fit, but
neither the original schedule nor a proposed 90-minute schedule passed all comparisons.
The original schedule worked consistently under one description of wind-related uncertainty,
while the other description remained unreliable. The longer schedule failed its required
separation checks despite looking promising in a simplified calculation. One planned IMU turn
also overlapped an aircraft turn. Independent motion examples show that such an overlap can
corrupt the recovered IMU orientation, but its contribution to the campaign failures remains
unisolated. Saved diagnostics show separate losses to allowed measurement effects and the
numerical cutoff; moving the turns alone is not an established solution.

This leaves experimental design and reconstructed orientation as immediate research questions.
A longer flight or a more elaborate correction cannot be assumed to improve the result.
See [Evidence so far](EVIDENCE.md) for a readable account of the completed work.

## What must happen before strong claims are made?

First, the project needs a practical route and IMU-turn procedure that remains informative
after the full recording and analysis process. All required model comparisons must survive
the allowed IMU and aircraft uncertainties, rather than only the simplest calculation.
The [processing review](protocol-development-20261006/PROCESSING_REVIEW.md) identifies a timing
correction to test. Aircraft-motion checks during deliberate IMU turns are now implemented;
a new campaign must assess their effect on useful data and orientation errors.

An experimental wind correction now uses a slowly changing wind vector and speed through
the air, constrained to agree with GPS ground motion. Controlled checks cover its fitting,
uncertainty calculations and refusal to decide near its parameter limits. These checks do
not yet show that it preserves the Earth-model differences better than the earlier correction.
A comparison using the same simulated recordings for both corrections is needed next.

Real IMUs must pass the [bench tests](BENCH.md). These include preserving a separately imposed
slow rotation, repeatability on different days, drift, temperature and Bluetooth behavior.
The current project work has no completed real-IMU validation evidence.

Then the final analysis and its acceptance rules must be fixed in advance, including the
software and numerical environment. Fresh simulations will set the decision thresholds.
A separate, previously unused campaign must test those thresholds and measure wrong decisions.
If the method is changed after those results are examined, another independent check is needed.

The intended wrong-rejection limit is roughly three cases in a thousand. Demonstrating such
a small rate needs far more evidence than a few hundred accepted simulations. Earlier restricted
plans required hundreds of thousands of simulated attempts in total; those cost estimates must
be refreshed after changes to the method and its usable flight domain. The full campaign has
not run, and no final empirical decision thresholds have been established.

## External flight tracks and missing GNSS

The app can keep recording the IMU when phone GPS is unavailable. Airline, flight number,
scheduled origin-local departure date and route help locate a public track afterwards.
This preserves useful collection options but does not yet provide a validated GPS replacement.

Before an external track can support analysis, its flight identity, recording overlap, clock
alignment and position uncertainty must be checked. Coarse samples can miss turns; estimated
positions and long gaps cannot be treated as measured fixes. Reported altitude also needs a
known reference or explicit uncertainty. The original recording remains unchanged and the
external track remains a separate source with its own terms.

Seven public or supplied position tracks have been reviewed for development. Five have prepared
windows; two remain blocked by coverage. Replaying their geometry with simulated IMU behavior
is implemented and checked with controlled examples. It has not yet run on those actual routes.
The sparse-fix replay preserves the original observations. A second replay explicitly assumes
a path between nearby fixes and simulates frequent GPS; neither supplies real IMU evidence
or enables operational use of an external track.

## Combining flights and partial evidence

A flight may separate two models while being unable to separate another pair. Experimental
code preserves that distinction and can abstain where information is missing. Combining such
comparisons needs its own decision rules and validation. Repeated use of the same physical
IMU must not be counted as independent instruments.

The newer experimental comparison fits each model pair directly, so usefulness for that pair
does not depend on a numerical choice about the complete three-model fit. It has its own
convergence, uncertainty and calibration rules. It cannot reuse thresholds for the older
comparison or supply a validated winner without fresh calibration and independent checking.

## Detailed research record

The [technical validation record](VALIDATION_TECHNICAL.md) preserves exact policies, historical
results, statistical plans and reproducibility details. [Research-record eligibility](PRIMARY_CORPUS.md)
explains which recordings can enter the provisional main result. Current confidence statements
remain provisional until instrument and independent statistical validation are complete.
