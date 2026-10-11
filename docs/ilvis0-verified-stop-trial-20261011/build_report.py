# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render verified-stopping evidence with the existing metadata-only comparator."""
import importlib.util
import json
from pathlib import Path

from lll.ilvis0 import sha256

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'ilvis0-unit-scale-trial-20261011/build_report.py'
spec=importlib.util.spec_from_file_location('isolated_verified_stop_report',SOURCE)
_report=importlib.util.module_from_spec(spec)
spec.loader.exec_module(_report)
_report.VERSION='ilvis0-verified-stop-prediction-trial-v1'


def build(directory=HERE,baseline=_report.BASELINE):
    directory=Path(directory)
    rows=_report.build(directory,baseline)
    text=(directory/'RESULTS.md').read_text().replace(
        '# Fixed solver scaling: matched prediction comparison',
        '# Verified stopping: matched prediction comparison').replace(
        'docs/ilvis0-unit-scale-trial-20261011/build_report.py',
        'docs/ilvis0-verified-stop-trial-20261011/build_report.py')
    (directory/'RESULTS.md').write_text(text)
    # The reused renderer already verified and recorded the evidence inputs.
    path=directory/'report-receipt.json'
    receipt=json.loads(path.read_text())
    receipt['sources'][str(Path(__file__).resolve())]=sha256(Path(__file__))
    receipt['artifacts']['RESULTS.md']=sha256(directory/'RESULTS.md')
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    return rows


if __name__=='__main__':
    build()
    print('Verified-stopping report published from metadata; zero new evaluations.')
