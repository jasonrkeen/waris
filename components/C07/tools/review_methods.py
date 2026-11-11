"""Scoped retained-probe and synthetic comparison methods; no network or scoring."""
from pathlib import Path,PurePosixPath
from collections import Counter
from urllib.parse import urlsplit
from typing import Any
import csv,json,hashlib,math,re
from decimal import Decimal

PROBES=['availability_discovery','confirmed_series_probe','data_endpoint_discovery','dsd_endpoint_probe','endpoint_probe','oblast_baseline_probe','observation_matrix_probe','observation_probe']
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path:Path)->list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path:Path,records:list[dict[str,Any]])->None:
    with path.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
def retained_path(base:Path,locator:str)->Path:
    text=re.sub('/+','/',locator.replace('\\','/'));prefix='<project-root>/'
    if not text.startswith(prefix):raise ValueError('Expected retained project-root locator')
    relative=PurePosixPath(text[len(prefix):])
    if relative.is_absolute() or '..' in relative.parts or ':' in str(relative):raise ValueError('Unsafe retained locator')
    path=(base/Path(*relative.parts)).resolve()
    if not path.is_relative_to(base.resolve()):raise ValueError('Locator outside retained source')
    return path
def preview_matches(preview:str,body:str)->bool:
    if not preview or len(preview)<30:return False
    normalized=body.replace('\n',' ').replace('\r',' ')
    return normalized.startswith(preview)
def gap_band(value:float)->str:
    if not math.isfinite(value) or value<0:raise ValueError('Finite nonnegative absolute gap required')
    return next(label for bound,label in [(75,'very_large_gap'),(50,'large_gap'),(25,'moderate_gap'),(10,'small_gap'),(0,'minimal_gap')] if value>=bound)
def ratio_band(value:float)->str:
    if not math.isfinite(value) or value<=0:raise ValueError('Finite positive ratio required')
    if value>=2:return 'official_share_much_higher'
    if value>=1.25:return 'official_share_higher'
    if value<=.5:return 'official_share_much_lower'
    if value<=.8:return 'official_share_lower'
    return 'roughly_aligned'
def gap_projection(benchmark:list[dict[str,str]])->list[dict[str,Any]]:
    if len(benchmark)!=25 or len({r['waris_oblast'] for r in benchmark})!=25:raise ValueError('Expected 25 unique reviewed regions')
    result=[]
    for row in benchmark:
        numeric={name:float(row[name]) for name in ['official_grp_million_uah','official_grp_share_of_waris_total','synthetic_prewar_share_of_total','official_grp_index_0_100','synthetic_prewar_index_0_100','official_vs_synthetic_index_gap','official_to_synthetic_share_ratio']}
        if not all(math.isfinite(v) for v in numeric.values()) or numeric['official_grp_million_uah']<=0:raise ValueError('Invalid reviewed numeric input')
        if any(not 0<numeric[k]<=1 for k in ('official_grp_share_of_waris_total','synthetic_prewar_share_of_total')):raise ValueError('Invalid distribution share')
        # Preserve reviewed floats; tolerate representation error without clipping values.
        if any(not -1e-10<=numeric[k]<=100+1e-10 for k in ('official_grp_index_0_100','synthetic_prewar_index_0_100')):raise ValueError('Invalid scaled index')
        gap=numeric['official_grp_index_0_100']-numeric['synthetic_prewar_index_0_100'];ratio=numeric['official_grp_share_of_waris_total']/numeric['synthetic_prewar_share_of_total']
        if not math.isclose(gap,numeric['official_vs_synthetic_index_gap'],abs_tol=1e-10) or not math.isclose(ratio,numeric['official_to_synthetic_share_ratio'],abs_tol=1e-10):raise ValueError('Reviewed gap/ratio inconsistent')
        result.append(dict(waris_oblast=row['waris_oblast'],**numeric,absolute_index_gap=abs(gap),legacy_heuristic_gap_band=gap_band(abs(gap)),legacy_heuristic_ratio_band=ratio_band(ratio),interpretation='Illustrative difference between independently min-max-scaled official GRP and arbitrary seed42 synthetic prewar indices; no measured economic error or AML inference.',current_posture='benchmark_only',sector_allocation_approved=False,used_in_scoring=False))
    if any(not math.isclose(sum(r[k] for r in result),1,abs_tol=1e-9) for k in ('official_grp_share_of_waris_total','synthetic_prewar_share_of_total')):raise ValueError('Shares do not sum to one in fixed reviewed universe')
    return sorted(result,key=lambda r:(-r['absolute_index_gap'],r['waris_oblast']))

def probe_inventory(root:Path)->tuple:
    base=root/'work/original/waris_ukraine_aml_risk_model_publish';raw=base/'data/raw';bodies=[]
    with next(raw.glob('*21_19_35*.csv')).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.reader(stream);next(reader);source_values={(r[2],r[8]):Decimal(r[9]) for r in reader if (r[0],r[4],r[6])==('GRP','_Z','A') and r[9]}
    for path in sorted(raw.rglob('ukrstat*raw.json'))+sorted((raw/'ukrstat_oblast_baseline_success_responses').glob('*.json'))+sorted(raw.glob('ukrstat*raw.txt')):
        text=path.read_text(encoding='utf-8-sig');variants=[text]
        try:variants.append(json.dumps(json.loads(text),ensure_ascii=False,separators=(',',':')))
        except json.JSONDecodeError:pass
        bodies.append((path,variants))
    audit=[];summaries=[]
    for name in PROBES:
        filename='ukrstat_'+name+'_results.csv';rows=read(base/'outputs/tables'/filename);records=[]
        for index,row in enumerate(rows,1):
            url=row['url'];parsed=urlsplit(url)
            if parsed.scheme!='https' or parsed.hostname!='stat.gov.ua' or parsed.username or parsed.password:raise ValueError('Unexpected source URL')
            matches=[path for path,variants in bodies if any(preview_matches(row['response_preview'],v) for v in variants)]
            association='no_retained_body_preview_match';exact_path='';observations=0
            if row.get('raw_response_path'):
                path=retained_path(base,row['raw_response_path']);assert path.is_file()
                payload=json.loads(path.read_bytes());data=payload['data'];st=data['structures'][0];ds=data['dataSets'][0]
                assert len(ds['series'])==1
                key,series=next(iter(ds['series'].items()));dimensions={spec['id']:spec['values'][int(i)]['id'] for spec,i in zip(st['dimensions']['series'],key.split(':'))}
                assert dimensions=={'INDICATOR':'GRP','REGION':row['region_code'],'NACE':'_Z','FREQ':'A'}
                assert row['sdmx_key']=='.'.join(dimensions[k] for k in ('INDICATOR','REGION','NACE','FREQ')) and parsed.path.endswith('/'+row['sdmx_key'])
                observations=sum(entry[0] is not None for entry in series['observations'].values())
                assert observations==int(row['observation_value_count'])==18
                times=st['dimensions']['observation'][0]['values']
                for position,entry in series['observations'].items():
                    period=str(times[int(position)].get('value',times[int(position)].get('id')))
                    assert Decimal(str(entry[0]))==source_values[(row['region_code'],period)]
                assert path in matches,'Explicit body preview mismatch'
                association='explicit_retained_path_and_series_key_match_not_authenticated_HTTP_exchange';exact_path=path.relative_to(base).as_posix()
            elif len(matches)==1:association='one_compatible_retained_prefix_only_not_authenticated_request'
            elif len(matches)>1:association='ambiguous_shared_prefix_not_authenticated_request'
            result=dict(table=filename,row_number=index,probe_name=row.get('probe_name',row.get('oblast','')),recorded_HTTP_status=row['http_status'],retained_body_association=association,preview_match_count=len(matches),explicit_retained_path=exact_path,explicit_body_sha256=sha(base/exact_path) if exact_path else '',decoded_numeric_observations=observations,recorded_url=url,compatible_retained_body_locators=';'.join(p.relative_to(base).as_posix() for p in matches),original_HTTP_status_headers_or_time_authenticated=False)
            audit.append(result);records.append(result)
        summaries.append(dict(table=filename,recorded_probe_rows=len(rows),recorded_HTTP_status_counts=json.dumps(dict(Counter(r['http_status'] for r in rows)),sort_keys=True),explicit_body_key_associations=sum(bool(r['explicit_retained_path']) for r in records),preview_only_ambiguous_rows=sum(not r['explicit_retained_path'] and r['preview_match_count']>1 for r in records),preview_only_single_compatible_rows=sum(not r['explicit_retained_path'] and r['preview_match_count']==1 for r in records),rows_without_compatible_body=sum(r['preview_match_count']==0 for r in records),HTTP_status_headers_and_request_time='not_independently_authenticated',public_scope='Retained diagnostic inventory only; no historical acquisition authentication or scoring approval.'))
    return audit,summaries
