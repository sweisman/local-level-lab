# Legacy POS AV 510 / IMU6 recording questions

Prepared for a future request to the instrument provider or acquisition team.
**Not sent.** No purchase, authenticated document request or external action has occurred.

We are decoding NASA/NSIDC ILVIS0 `.013` airborne recordings. The six representative
files identify AV-510, VER5, IMU6, at approximately 200 Hz. Their logged POS system
identifiers and firmware/ICD combinations are:

- S/N2720: HW3.1-7, SW04.50-Feb05/08, ICD14.00, OS425B14.
- S/N3861: HW4.0-7, SW05.00-Dec16/09, ICD17.00, OS425B142.
- S/N4126: HW4.0-7, SW05.20-Nov04/11, ICD18.00, OS425B142.

The [inventory](inventory.csv) supplies exact filenames, embedded dates and uncompressed
source hashes. These identifiers belong to the logged POS system; please identify the
actual IMU part/variant and serials separately where records permit.

1. For these exact firmware/ICD revisions, is Group 4 recorded before or after the
   navigation filter's estimated gyro/accelerometer bias and gain corrections?
   Is Earth rotation or transport rate removed from either its angle or velocity
   increments? Is the logging path different in Navigate and Standby modes?
2. What does legacy IMU type 6 identify? Is its sensor an LN-200/LN200ROM or another
   variant? What gyro/accelerometer calibration, noise, drift and scale-error
   limits apply to these installations, and over what temperature/time conditions?
3. Is its 24-byte Group-4 data six signed little-endian int32 increments? What are
   the exact velocity and angle scales, axis/sign definitions, clipping and overflow
   conventions? Our empirical hypotheses are 0.4 arcsecond/count and
   3.38e-5 m/s/count; these are not assumed manufacturer definitions.
4. Does each packet represent a fixed 5 ms sensor integration interval or the
   difference between adjacent packet timestamps? Are tags at interval beginning,
   midpoint or end? How is synchronization performed, and what sensor-to-GNSS
   latency, jitter or oscillator-error bounds are supported?
5. Which factory or runtime corrections precede the recorded Group-4 tap:
   temperature, bias, gain, axis nonorthogonality, coning, sculling, filtering,
   automatic zeroing and lever-arm compensation? Are coefficients or processing
   flags logged, and can these functions be enabled independently?
6. Can you supply the legacy Message-1 installation/settings layout and rotation
   conventions, including reference/vehicle/IMU frames and lever-arm origins?
   Are there surveyed mounting/lever-arm records for the listed epochs? Logged
   settings reproduce mappings, but an authoritative layout remains needed.
7. Which receiver-only GNSS processing modes and uncertainty conventions applied
   during acquisition? Were common-mode position errors or IMU feedback present
   in the primary receiver output? Are independent position/covariance validation
   or calibration records available?

We use fused Group 1 only for decoder validation and motion context. We seek the
processing history of Group 4 so that navigation-derived corrections are not mistaken
for independent inertial evidence. Firmware-matched manuals, acquisition logs and
calibration records would be more useful than a current integrated-navigation
accuracy specification.
