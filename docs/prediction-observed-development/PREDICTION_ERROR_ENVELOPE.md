# A conditional forecast-error bound

An aircraft forecast can miss for several reasons: its starting position or
speed may be wrong, its IMU may misread rotation or force, and the movement
model may omit some acceleration. The receiver position used to check the
forecast has error too.

The [bound calculator](../../analysis/lll/prediction_error_envelope.py) keeps
these limits separate for a local Cartesian inertial calculation. It assumes
the two paths share gravity and transport dynamics; any difference there must
fit within the declared unmodeled-acceleration limit. Given a maximum for
**every** source over the entire forecast, it computes a position-discrepancy
bound under those assumptions. A rotation-rate error matters increasingly
with time because it
gradually points the measured force in the wrong direction. A changing
rotation-rate error grows faster still.

Six [known-answer checks](../../analysis/tests/test_prediction_error_envelope.py)
pass. They cover exact constant and changing-error terms, an independently
integrated rotating force, and a generated aircraft with recorded sensor
errors. The aircraft check supplies the **realized maximum errors** from the
generator. It verifies the calculation; it does not predict those maxima
from earlier observations.

A further check uses the repository's **synthetic** Gaussian IMU settings,
300 samples per second and a 120-second forecast. Giving a 5% total tail
allowance to the maximum of four sensor-error components across all samples
produces a **3.16 km** position bound, even with exact initial state, no
receiver error and no omitted aircraft motion. This is a valid but very loose
samplewise worst-case construction under those synthetic assumptions. It is
not a measurement of the ESA device. It shows why a useful 120-second range
will need a qualified time-correlated stochastic calculation or independently
stronger physical limits, rather than treating each white-noise sample at its
worst possible value throughout the forecast.

**Status:** The calculator cannot yet supply an error range for the ESA
recording or replace the complete globe/disc propagation. The allowed changes
in IMU error, initial calibration, model dynamics and unmodeled aircraft
motion have not been independently bounded over a future flight. Entering
assumed numbers would give a result conditional on those numbers, not
verified coverage. The seven reserved flight groups remain closed.

The next qualification must establish defensible limits or a tested
stochastic alternative using earlier-only data and independent generated
controls. If that cannot be done, the prediction method abstains.
