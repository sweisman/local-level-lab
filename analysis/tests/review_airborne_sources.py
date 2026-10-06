# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline identity and sample inventory for documented NASA metadata; no measurements decoded."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CORPUS=ROOT/'docs/research-next-stage-20261006/airborne-metadata'
QUERIES={
    'ilvis0-collections.json.gz':'https://cmr.earthdata.nasa.gov/search/collections.json?short_name=ILVIS0&page_size=10',
    'ilvis0-granules.json.gz':'https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C3162704221-NSIDC_CPRD&page_size=20&sort_key=start_date',
    'ilvis0-gps-granules.json.gz':'https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C3162704221-NSIDC_CPRD&page_size=40&producer_granule_id=ILVIS0_gps_54935_remote*&options%5Bproducer_granule_id%5D%5Bpattern%5D=true&sort_key=producer_granule_id',
    'iputi0-collection.json.gz':'https://cmr.earthdata.nasa.gov/search/concepts/C1386246599-NSIDCV0.umm_json',
}


def inventory(entry):
    links=[v['href'] for v in entry.get('links',[]) if not v.get('inherited')
           and v.get('rel','').endswith('/data#') and v.get('href','').startswith('https://')]
    return dict(concept_id=entry['id'],filename=entry['producer_granule_id'],
        catalog_size=entry.get('granule_size'),catalog_start=entry.get('time_start'),
        catalog_end=entry.get('time_end'),download_urls=links,
        measurement_columns_verified=False,actual_sample_times_verified=False)


def review():
    documents={}; provenance={}
    for filename,url in QUERIES.items():
        path=CORPUS/filename; raw=gzip.decompress(path.read_bytes())
        documents[filename]=json.loads(raw)
        provenance[str(path.relative_to(ROOT))]=dict(request_url=url,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            uncompressed_sha256=hashlib.sha256(raw).hexdigest())
    collection=documents['ilvis0-collections.json.gz']['feed']['entry']
    if len(collection)!=1 or collection[0]['short_name']!='ILVIS0': raise ValueError('unexpected LVIS collection')
    alternate=documents['iputi0-collection.json.gz']
    if alternate['ShortName']!='IPUTI0' or alternate['DOI']['DOI']!='10.5067/7K31MCH5XXZA':
        raise ValueError('alternative source identity changed')
    granules=documents['ilvis0-granules.json.gz']['feed']['entry']
    imu=[inventory(v) for v in granules if '_gyro_' in v['producer_granule_id']]
    gps=[inventory(v) for v in documents['ilvis0-gps-granules.json.gz']['feed']['entry']]
    return dict(state='public_metadata_inspected_authentication_and_payload_schema_pending',
        collections=[dict(short_name='ILVIS0',concept_id=collection[0]['id'],doi='10.5067/E6JPQ3QNW77R'),
                     dict(short_name=alternate['ShortName'],concept_id='C1386246599-NSIDCV0',doi=alternate['DOI']['DOI'])],
        alternative_is_same_dataset=False,imu_filename_candidates=imu,gps_filename_candidates=gps,
        input_provenance=provenance,helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        access_checks=[dict(source='ILVIS0',target='ILVIS0_gyro_54935_atm_applanix_14Apr09.013',
            requested_byte_range=[0,65535],http_status=302,redirect_host='urs.earthdata.nasa.gov',measurement_bytes_received=0),
            dict(source='IPUTI0',target='published directory',http_status=302,
                 redirect_host='urs.earthdata.nasa.gov',directory_listing_received=False)],
        decoded_measurement_files=0,empirical_discrimination_tested=False,
        format_sources=['https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf',
                        'https://nsidc.org/sites/default/files/ilvis0-v001-userguide_1.pdf'],
        limitations=['Catalog filename indicates a candidate only; no actual gyro payload or GPS columns inspected.',
            'Catalog intervals are day-wide; files sharing a date are not proven to share a flight or sample overlap.',
            '2014 POS AV V6 documentation is a format lead, not a verified specification for the 2009 sample.',
            'Group4 and10002 IMU payload details are not fully public in that document; do not guess scaling or decode navigation rates as raw gyro.',
            'IPUTI0 metadata lists text position/velocity/orientation; independent raw gyro channels remain unconfirmed.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); result=review()
    with args.output.open('x') as out: out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(collections=result['collections'],imu_candidates=len(result['imu_filename_candidates']),
                         gps_candidates=len(result['gps_filename_candidates']),decoded_files=0)))
