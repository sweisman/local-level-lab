# Ready to check the Nuuk Museum observation times

The [station-day comparison](ESA_NKAR_GROUND_SCORE_RESULT.md) matched all
520 aircraft timestamps and all 120 one-second scoring intervals. For
the closed study, use the report command below to verify the saved result.

The intake reads RINEX 2.10 and 2.11 on the GPS clock and pairs recorded
ground seconds with the original half-second aircraft observations. It
preserves gaps and checks the intervening aircraft reports for loss of
lock. It retains the original legacy signal labels because `L1` and `L2`
alone do not identify the tracking codes used. Records with an alternate
wavelength factor cannot support an arc through that epoch. The legacy
anti-spoofing bit remains in the receipt without being counted as a loss
of lock. [IGS RINEX 2.11 specification](https://files.igs.org/pub/data/format/rinex211.txt)

Seventeen focused tests passed. A public RINEX 2.11 control day from the
Geospatial Information Authority of Japan passed all 2,880 epoch framing
checks after GSI `crx2rnx` 4.2.0 expansion. The control declared a
30-second cadence. Among valid two-band GPS observations it had 51,138
phase flags with the anti-spoofing bit set and two clear flags. This checks
the format and flag handling. Aircraft and ground coverage on the target
flight will be verified from the Nuuk Museum file itself.
[SONEL archive access](https://www.sonel.org/Data-access) ·
[Control file](ftp://ftp.sonel.org/gps/data/2023/187/01941870.23d.Z) ·
[GSI converter](https://terras.gsi.go.jp/ja/crx2rnx.html)

The compressed control SHA-256 is
`69bd8e29dc27f1fc19245ac5c6a54140570409a2d1f7786e447ba4c63b3894d6`.
The expanded SHA-256 is
`f392bd62d6bb3f111d4a6b8de08a10b22331a9df663cce7036cdfd56941a5bb5`.
The single-step intake reproduced both hashes from the original archive.

Once the original archive is available, retain it and run the coverage
check from the repository root with the sealed AIR1 study available. The
intake decodes the UNIX compression and compact RINEX in temporary files.
It requires both tools to exit successfully and records the compressed,
intermediate and expanded hashes along with the decoder executable hashes.
The coverage check still leaves GPS tracking-code compatibility to the
subsequent carrier analysis.
[Download catalogue](ESA_GROUND_REFERENCE_AVAILABILITY.md)

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.esa_nkar_ground_intake \
  /path/to/nkar1870.23d.Z --converter /path/to/crx2rnx \
  --output /path/to/nkar-coverage.json
```

## Compare the matched phases

The [one-second score plan](ESA_NKAR_GROUND_SCORE_PLAN.md) adds the signed
ground and aircraft range comparison after intake. Eleven software checks
passed. They cover legacy phase values and flags, clock and range signs,
missing intervals and projection of the score onto the actual satellite
matches. The completed study verifies coverage for the target station day.
Independent aircraft accuracy remains open.

With the original station day and converter available, prepare the fixed study
from the repository root. The first command verifies the test evidence and
the archived aircraft inputs before it freezes the exact ground interval.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_nkar_score_study prepare \
  --original /path/to/nkar1870.23d.Z --converter /path/to/crx2rnx
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-nkar-ground-score-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_nkar_score_study report
```

The run command shown assumes no other active numerical jobs. Check allocation
with the [status command](../../analysis/STATUS.md) first. After a technical
interruption, use the same module's `recover` command to verify charges and
resume only unfinished work.
