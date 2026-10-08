# Finding the missing legacy acquisition records

The targeted public search did not obtain a manual or calibration record matching
the six recordings' V5 firmware/ICD combinations: 04.50/14.00, 05.00/17.00 and
05.20/18.00. This is a bounded search result, not proof that records do not exist.

The NASA-hosted [Applanix directory](https://asapdata.arc.nasa.gov/share/ASF_Applanix/)
lists only a V6 manual and V6 ICD. Other hits concerned marine systems, newer
firmware or bibliographic references without the actual legacy manual. None was
substituted into the decoder or calibration assumptions. The search log preserves
the 19 queries and main access-route outcomes for a future session.

The current [ILVIS0 user guide](https://nsidc.org/sites/default/files/ilvis0-v001-userguide_1.pdf)
describes the Level-0 archive as raw, unprocessed data, with no product derivation
algorithms or processing steps. It includes IMU/GPS supporting measurements and
was updated in August 2025. This supports **archive-level provenance**. It does
not specify calibration, filtering or Earth-rate compensation inside Applanix
before logging, nor the legacy Group-4 encoding, integration period or latency.

NSIDC lists **nsidc@nsidc.org** for user services. The
[ready-to-send request](EMAIL.md) names the DOI and exact firmware combinations,
asks three essential questions and requests routing to the acquisition team if
needed. [Official contact page](https://nsidc.org/about/contact-us)

The [six-file inventory](../ilvis0-instrument-evidence-20261007/inventory.csv) and
[full questions](../ilvis0-instrument-evidence-20261007/QUESTIONS.md) provide follow-up
detail. No original data or credentials need to accompany the initial request.
**No message was sent.** This workspace has no email-sending tool configured.

Useful responses would establish the firmware-matched Group-4 logging tap relative
to navigation corrections, encoding/clock conventions, and installation/calibration
bounds. Responses must be checked against the listed configurations. General
navigation accuracy alone would leave those questions open.

All 232 originals and earlier frozen studies remain intact. No empirical Earth
fit/start or scientific gate change occurred. Obtaining the matched records is the
next step; repeated public searches or noiseless controls cannot supply them.
