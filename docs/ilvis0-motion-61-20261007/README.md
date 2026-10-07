# Why the remaining 61 recordings fail the strict motion check

This separate local investigation examines the 61 kept files that did not contain a minute
passing the instantaneous fused-navigation motion limits. It changes neither storage nor
scientific eligibility and performs no Earth-model fits.

The audit is complete: all 61 source hashes and strict packet checks passed, with no errors.
The earlier instantaneous-motion results reproduced exactly. All files stay kept, and the
archive still holds 232 originals. None of these diagnostic comparisons establishes an
accepted scientific window.

| Finding | Files | Meaning |
|---|---:|---|
| Course-rate result depends on measurement timescale | 53 | At least a minute passes when course rate is measured over one of the tested longer intervals, with the original roll, climb and speed checks retained. |
| Roll or climb also breaks the minute | 3 | Even omitting the course limit leaves less than a minute. |
| Navigation and receiver comparison disagree | 1 | Receiver track permits a minute at 12-second resolution, while the navigation-based motion check does not. This is not proof of which estimate is correct. |
| No minute at any tested resolution | 4 | Neither comparison produces a minute; persistent motion and limited support remain possible explanations. |

Course-change limits are especially sensitive to short excursions. Of 43,721 excursions,
43,055 lasted less than a second (98.5%); in 43 files every excursion was that short.
At 2-second resolution, 39 files recover a diagnostic minute; at 6 seconds, 46 do;
at 12 seconds, 53 do. These are comparisons of the same files, not independent trials.
Receiver course alone permits a minute in 45, 49 and 57 files respectively, but that
comparison does not check the aircraft's bank angle or climb.

The three additional motion blockers are the 13 April 2010 LVIS 510 recording (climb),
31 October 2013 POS510 recording (repeated roll excursions) and 4 November 2013 POS510
recording (a roll excursion splitting the available stretch). The disagreement occurs in
the 16 April 2011 POSAV recording. The four remaining files are the 21 September 2014
LVIS610 recording and the 4, 5 and 20 September 2017 510i recordings.

The practical result is to keep these recordings for decoder and motion research, rather
than discard them as empty or promote them to scientific evidence. In particular, 53 merit
investigation of the course-rate measurement timescale. Before adopting a revised rule, it
must be tested against known real motion; averaging can hide aircraft corrections. Units,
mounting and recorded corrections also remain unresolved for most of this subset, which
contains 59 IMU6 and two IMU21 files.

All 61 exceed the course-change limit somewhere in the selected GPS stretches. In 54,
the recorded roll and climb stay within their limits throughout those stretches. Three also
exceed the climb limit and four exceed the roll limit. Small course excursions can repeatedly
restart the required uninterrupted minute even when most of a stretch looks nearly level.

The investigation counts excursions, measures their approximate duration, and computes how
long a stretch would last if each criterion were omitted in turn. It then compares course-rate
regressions over 2, 6 and 12 seconds, retaining the original limits for reference. These are
sensitivity diagnostics: averaging can suppress real small course corrections as well as
estimation noise. It does not prove that excursions are artifacts or create scientific windows.
Missing epochs and gaps remain unsupported; no IMU measurement is interpolated or altered.

An additional comparison uses checksummed VTG sentences from the primary receiver stream.
VTG reports [ground track and speed](https://receiverhelp.trimble.com/oem-gnss/nmea0183-messages-vtg.html),
not aircraft heading. It lacks a time field, so each sentence must have a unique nearby dated
GGA fix within half a second. The association error is preserved. Invalid, estimated, manual
and simulated modes are rejected; older missing mode fields remain explicitly marked.
Receiver ground track is not a second independent GPS experiment and cannot validate
subsecond navigation behavior or IMU orientation.

The resumable worker freezes sources, inputs and environment in
`data/ilvis0-motion-61-20261007/`. Per-file reports preserve all classifications and comparisons.
No completed older study is rewritten. Eight new focused tests passed, including persistent
turn detection, missing data, north crossing and ambiguous receiver timestamps.
Together with seven retention tests, 15 tests passed. The worker has finished and released
its lock; do not resume the completed audit. The evidence directory preserves a source
snapshot, source/input/environment manifest, complete compressed report and per-file CSV
inventory. All 61 files provided associated receiver-track observations (29,994 sentences).
