# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import numpy as np
from fastapi.testclient import TestClient
from lll.format import write_session
from lll.witmotion import spp_packets
from lll_server.app import create_app
from lll_server.cli import process, export


def test_stationary_upload_without_flight_or_gps_preserves_original_and_reports_kind(tmp_path):
    manifest=dict(schema_version=3,data_license='CC0-1.0',session_id='ground-test',install_id='test',
        device={},phases=[],clock={'elapsed_ns':0,'utc_ms':0},imu={'variant':'spp'},
        kind='stationary',stationary={'protocol':'stationary-reversal-v1','axis':'x','latitude_deg':-30.})
    chunk=spp_packets(0x51,[[0,0,2048,0]]).tobytes()+spp_packets(0x52,[[0,0,0,0]]).tobytes()
    path=tmp_path/'ground.zip'; write_session(path,manifest,{},imu=(np.array([1]),[chunk]))
    app=create_app(tmp_path/'store'); client=TestClient(app)
    response=client.post('/api/v1/sessions',files={'file':('ground.zip',path.read_bytes())})
    assert response.status_code==201,response.text
    ident=response.json()['id']; process(app.state.store)
    assert client.get('/api/v1/sessions').json()[0]['kind']=='stationary'
    result=client.get('/api/v1/sessions/'+ident).json()
    assert result['stationary_metadata']['latitude_deg']==-30.
    assert result['result']['stationary']['scientific_decision']=='abstain'
    assert client.get('/api/v1/sessions/'+ident+'/raw').content==path.read_bytes()
    exported=export(app.state.store,tmp_path/'export')
    assert json.loads((exported/'index.json').read_text())[0]['kind']=='stationary'
