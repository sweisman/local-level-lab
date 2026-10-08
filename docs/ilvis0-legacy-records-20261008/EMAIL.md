# Ready-to-send NSIDC request

**Draft only; not sent.** Recipient verified on the
[NSIDC contact page](https://nsidc.org/about/contact-us) on 8 October 2026.

To: nsidc@nsidc.org

Subject: ILVIS0 .013 legacy Applanix IMU6 recording documentation

Hello NSIDC User Services,

I am investigating airborne inertial measurements in IceBridge LVIS L0 Raw Ranges,
Version 1 (ILVIS0; DOI 10.5067/E6JPQ3QNW77R).

Six representative .013 files identify POS AV 510, VER5, IMU6. Their logged POS
system identifiers and firmware/ICD combinations are:

- S/N2720: SW04.50-Feb05/08, ICD14.00; 14 April 2009 and 16 September 2014.
- S/N3861: SW05.00-Dec16/09, ICD17.00; 26 October and 20 November 2010.
- S/N4126: SW05.20-Nov04/11, ICD18.00; 24 September 2015 and 20 September 2017.

The Level-0 guide describes unprocessed archival data. I would like to establish
what Applanix did before recording the Group-4 IMU increments:

1. Were they logged before or after navigation-estimated sensor corrections?
   Were Earth rotation or transport rate removed?
2. What were the IMU6 angle/velocity encoding, scale factors, integration interval,
   timestamp convention and IMU/GNSS synchronization or latency bounds?
3. Are firmware-matched manuals, acquisition/settings logs or installation and
   calibration records available for these configurations?

Could you provide relevant documentation or route this to the original acquisition
team? I can supply exact filenames and source hashes. I use fused navigation only
for decoder validation and motion context, and want to avoid mistaking navigation
corrections for independent IMU evidence.

Thank you,
Scott Weisman
