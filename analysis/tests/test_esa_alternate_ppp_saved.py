# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cross-check the alternate-PPP result against the original 120-epoch scores."""

import json
from pathlib import Path

from lll.esa_alternate_ppp_scoring import rank_setting
from lll.esa_full_parallel_gnss import _sha


ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/prediction-observed-development'


def test_same_120_epochs_reproduce_every_saved_air1_primary_score():
    result=json.loads((BASE/'esa-alternate-ppp-scoring-result.json').read_bytes())
    original=json.loads((BASE/'ESA_400_120_MODEL_MATRIX_RESULT.json').read_bytes())
    assert result['code_sha256']==_sha(ROOT/'analysis/lll/esa_alternate_ppp_scoring.py')
    assert result['plan_sha256']==_sha(BASE/'ESA_ALTERNATE_PPP_SCORING_PLAN.md')
    assert result['common_withheld_epochs']==120
    rows={row['identity']:row for row in original['rows']}
    for setting in result['settings']:
        air1=setting['by_receiver']['air1']
        assert air1['ranking']==rank_setting(air1['scores'])
        for model,start in setting['primary_start'].items():
            identity=f'{model}-{int(setting["profile"])}-{setting["law"]}-{start}'
            assert air1['scores'][model]['total_rms_m']==rows[identity]['prediction_total_rms_m']
        assert all(item['ranking']['shape_lower_error_family']=='globe'
                   and item['ranking']['field_lower_error_model']=='specified_field'
                   for item in setting['by_receiver'].values())
