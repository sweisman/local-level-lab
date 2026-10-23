# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest


def test_report_series_preserves_a_verified_prefix_after_a_caller_failure(tmp_path):
    from lll.studies.series import ReportStream,read_reports,read_report_bytes
    path=tmp_path/'reports.jsonl'
    with pytest.raises(RuntimeError):
        with ReportStream(path,binding='frozen',maximum_records=3,maximum_record_bytes=4096) as stream:
            stream.append(0,{'time_s':2.,'metric':(1.,-0.,3.)})
            stream.append(1,{'time_s':3.,'metric':[4.,5.,6.]})
            raise RuntimeError('later computation failed')
    values=read_reports(path,binding='frozen',maximum_records=3,maximum_record_bytes=4096)
    assert len(values)==2 and values[0]['metric']==[1.,-0.,3.] and values[1]['time_s']==3.
    assert '-0.0' in path.read_text()
    assert read_report_bytes(path.read_bytes(),binding='frozen',maximum_records=3,maximum_record_bytes=4096)==values
    with pytest.raises(FileExistsError):ReportStream(path,binding='frozen',maximum_records=3,maximum_record_bytes=4096)


def test_report_series_checks_limits_order_hashes_and_truncation(tmp_path):
    from lll.studies.series import ReportStream,read_reports
    path=tmp_path/'reports.jsonl'
    with ReportStream(path,binding='fixed',maximum_records=1,maximum_record_bytes=4096) as stream:
        with pytest.raises(ValueError):stream.append(1,{'time_s':2.})
        with pytest.raises(ValueError):stream.append(0,{'bad':float('nan')})
        stream.append(0,{'time_s':2.})
        with pytest.raises(ValueError):stream.append(1,{'time_s':3.})
    with pytest.raises(ValueError):read_reports(path,binding='other',maximum_records=1,maximum_record_bytes=4096)
    raw=path.read_bytes();path.write_bytes(raw[:-1])
    with pytest.raises(ValueError,match='truncated'):read_reports(path,binding='fixed',maximum_records=1,maximum_record_bytes=4096)
    lines=raw.splitlines(keepends=True);value=json.loads(lines[1]);value['value']['time_s']=99.
    lines[1]=(json.dumps(value)+'\n').encode();path.write_bytes(b''.join(lines))
    with pytest.raises(ValueError,match='hash'):read_reports(path,binding='fixed',maximum_records=1,maximum_record_bytes=4096)
