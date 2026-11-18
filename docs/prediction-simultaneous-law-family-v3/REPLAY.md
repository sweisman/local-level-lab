# Replay the 96-recording simulation report

The [verified result](RESULT.md) was reproduced exactly in an isolated
directory from the original study, its finite continuation and 251 frozen
sources. The replay recovered all 96 recording outcomes and all charges.
The evidence package contains 4,143 files in 22 ZIP parts totaling about
180 MiB. This is a saved-results check with zero new fit starts.

The original run and the continuation retain their own plans, source copies,
fit artifacts, failed attempts, journals and completion receipts. The
package also includes the exact source tree needed by the replay. It has no
dependency on the repository-wide archive catalog.

The package is indexed by the [part list](replay-parts/index.json) and
[evidence receipt](replay-parts/evidence-receipt.json). From the repository
root, extract the collection to a fresh directory:

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.portable extract-parts \
  docs/prediction-simultaneous-law-family-v3/replay-parts /tmp/lll-v3-report-replay
```

Extraction verifies every part and reconstructed file. Keep the repository
root path for the thread guard, then enter the extracted directory:

```sh
lll_repo="$PWD"
cd /tmp/lll-v3-report-replay
~/venv/bin/python "$lll_repo/analysis/tests/run_numerical.py" --workers 1 --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -c '
import json
from pathlib import Path
from lll import prediction_simultaneous_study_v3 as definition
from lll.prediction_simultaneous_report import build

saved = Path("docs/prediction-simultaneous-law-family-v3/verified-report.json")
replayed = build(".", study_id="data/" + definition.IDENTITY, definition=definition)
if replayed != json.loads(saved.read_bytes()):
    raise SystemExit("Replay differs from the sealed report")
print("Exact replay of all", len(replayed["rows"]), "recording outcomes")
'
```

The historical lineage verifier checks the exact original Python, package
and platform record in the extracted study manifest. A machine with a
different environment can verify and extract every package file. Replaying
the calculation also requires the original environment. The simulated gate
does not qualify aircraft uncertainty.
