"""Strict selected annual-GRP parsing and retained metadata reconciliation."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
from typing import Any
import csv,json,hashlib,re

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path:Path)->list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path:Path,rows:list[dict[str,Any]])->None:
    with path.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def finite(value:Any)->Decimal|None:
    if value is None or value=='':return None
    result=Decimal(str(value))
    if not result.is_finite():raise ValueError('Nonfinite observation')
    return result
def period_label(value:dict)->str:
    labels=[str(value[k]) for k in ('value','id') if k in value and value[k] not in (None,'')]
    if not labels or len(set(labels))!=1 or not re.fullmatch(r'\d{4}',labels[0]):raise ValueError('Explicit unambiguous annual source label required')
    return labels[0]
def decode(payload:dict)->list[dict[str,Any]]:
    data=payload['data']
    if len(data.get('dataSets',[]))!=1 or len(data.get('structures',[]))!=1:raise ValueError('Expected one dataset and structure')
    ds=data['dataSets'][0];st=data['structures'][0]
    if not ds.get('series'):
        if ds.get('observations'):raise ValueError('Unsupported dataset-level observations')
        return []
    if len(ds['series'])!=1:raise ValueError('Expected one series')
    key,series=next(iter(ds['series'].items()));dims=st['dimensions']['series'];indices=key.split(':')
    if [d['id'] for d in dims]!=['INDICATOR','REGION','NACE','FREQ'] or len(indices)!=4:raise ValueError('Unexpected series axes/order')
    identity={d['id']:d['values'][int(i)]['id'] for d,i in zip(dims,indices)}
    if (identity['INDICATOR'],identity['NACE'],identity['FREQ'])!=('GRP','_Z','A'):raise ValueError('Unexpected series identity')
    specs=st['attributes']['series'];attrs=series.get('attributes',[])
    if len(specs)!=len(attrs):raise ValueError('Misaligned series attributes')
    decoded={}
    for spec,value in zip(specs,attrs):
        if isinstance(value,int) and not isinstance(value,bool) and 'values' in spec:
            if value<0 or value>=len(spec['values']):raise ValueError('Invalid attribute index')
            value=spec['values'][value]['id']
        decoded[spec['id']]=value
    if (decoded.get('UNITS_OF_MEASURE'),decoded.get('SCALE'),decoded.get('DECIMALS_DISPLAYED'))!=('1090','6','0'):raise ValueError('Unexpected units/scale/decimals')
    time=st['dimensions']['observation']
    if len(time)!=1 or time[0]['id']!='TIME_PERIOD':raise ValueError('Expected explicit time axis')
    labels=[period_label(value) for value in time[0]['values']]
    if len(labels)!=len(set(labels)):raise ValueError('Duplicate source period')
    dataset_specs=st['attributes'].get('dataSet',[]);dataset_attrs=ds.get('attributes',[])
    if len(dataset_specs)!=len(dataset_attrs):raise ValueError('Misaligned dataset attributes')
    dataset_meta={spec['id']:value for spec,value in zip(dataset_specs,dataset_attrs)}
    result=[]
    for index,entry in series.get('observations',{}).items():
        if not index.isdigit() or int(index)>=len(labels):raise ValueError('Observation has no explicit period label; no availability fallback allowed')
        notes={spec['id']:entry[i+1] if i+1<len(entry) else None for i,spec in enumerate(st['attributes'].get('observation',[]))}
        value=finite(entry[0])
        result.append(dict(region_code=identity['REGION'],indicator_code='GRP',nace_code='_Z',frequency='A',source_period_label=labels[int(index)],period_kind='annual_label_not_observation_day',value_million_UAH='' if value is None else str(value),source_state='explicit_unavailable' if value is None else 'numeric_observation',unit_code='1090',unit_label='UAH',scale_code='6',scale_label='Millions',decimals_code='0',source_timeseries_note_json=json.dumps(decoded.get('NOTES_TS'),ensure_ascii=False,sort_keys=True),source_observation_flag_json=json.dumps(notes.get('OBS_FLAG'),ensure_ascii=False,sort_keys=True),source_observation_note_json=json.dumps(notes.get('NOTES_OBS'),ensure_ascii=False,sort_keys=True),source_UPDATED_metadata_not_acquisition_time_json=json.dumps(dataset_meta.get('UPDATED'),ensure_ascii=False,sort_keys=True),used_in_scoring=False,used_in_monte_carlo=False,sector_allocation_approved=False))
    return sorted(result,key=lambda r:r['source_period_label'])

def flatten(value:Any,path:str='')->list[tuple[str,str]]:
    if isinstance(value,dict):return [leaf for k,v in value.items() for leaf in flatten(v,f'{path}.{k}' if path else str(k))]
    if isinstance(value,list):return [leaf for i,v in enumerate(value) for leaf in flatten(v,f'{path}[{i}]')]
    return [(path,'' if value is None else str(value)[:500])]
def path_role(path:str)->str:
    if path.startswith('data.structures['):return 'structure_metadata_not_observation'
    if re.match(r'data\.dataSets\[\d+\]\.attributes',path):return 'dataset_attribute_value_not_observation'
    if re.match(r'data\.dataSets\[\d+\]\.(series.*\.)?observations',path):return 'observation_payload_requires_typed_decoding'
    if path.startswith('data.dataSets['):return 'dataset_control_metadata_not_observation'
    return 'other_metadata_not_observation'
def constraint_projection(payload:dict)->list[dict[str,Any]]:
    out=[]
    for ci,constraint in enumerate(payload['data'].get('dataConstraints',[])):
        annotations={a['id']:str(a.get('title',a.get('value',''))) for a in constraint.get('annotations',[])}
        for cube_index,cube in enumerate(constraint.get('cubeRegions',[])):
            for component in cube.get('components',[]):
                out.append(dict(constraint_index=ci,cube_index=cube_index,component=component['id'],record_kind='component_metadata_not_observed_value',listed_value_count=len(component.get('values',[])),cube_include_as_supplied=json.dumps(cube.get('include')),component_include_as_supplied=json.dumps(component.get('include')),remove_prefix_as_supplied=json.dumps(component.get('removePrefix')),annotation_value='',positive_query_selector_inferred=False,observation_availability_inferred=False,used_in_scoring=False))
        for key in ('series_count','time_period_start','time_period_end'):
            if key in annotations:out.append(dict(constraint_index=ci,cube_index='',component=key,record_kind='constraint_annotation_not_observed_value',listed_value_count='',cube_include_as_supplied='',component_include_as_supplied='',remove_prefix_as_supplied='',annotation_value=annotations[key],positive_query_selector_inferred=False,observation_availability_inferred=False,used_in_scoring=False))
    return out

def run(root:Path,output:Path)->dict:
    base=root/'work/original/waris_ukraine_aml_risk_model_publish';raw=base/'data/raw';tables=base/'outputs/tables';output.mkdir(exist_ok=False)
    confirmed_path=raw/'ukrstat_confirmed_series_response_raw.json';confirmed=decode(json.loads(confirmed_path.read_bytes()))
    old=read(tables/'ukrstat_confirmed_series_parsed.csv');assert len(old)==len(confirmed)==18
    for a,b in zip(old,confirmed):assert a['time_period']==b['source_period_label']+'-01-01' and finite(a['obs_value'])==finite(b['value_million_UAH']) and a['region_code']==b['region_code']
    for row in confirmed:row['retained_response_sha256']=sha(confirmed_path)
    write(output/'confirmed_series_reconciled.csv',confirmed)
    candidates=[]
    for old in read(tables/'ukrstat_oblast_baseline_candidates.csv'):
        path=raw/'ukrstat_oblast_baseline_success_responses'/f"{old['region_code']}_GRP__Z_A.json"
        values=decode(json.loads(path.read_bytes()));assert len(values)==18 and all(r['source_state']=='numeric_observation' for r in values)
        latest=values[-1].copy();assert old['latest_period']==latest['source_period_label']+'-01-01' and finite(old['official_regional_baseline_proxy'])==finite(latest['value_million_UAH']) and old['region_code']==latest['region_code']
        assert (old['indicator_code'],old['nace_code'],old['freq_code'])==('GRP','_Z','A')
        latest.update(source_region_label_as_recorded=old['oblast'],retained_response_sha256=sha(path),latest_period_scope='latest_in_this_retained_response_not_global_current_latest',historical_HTTP_request_authenticated=False)
        candidates.append(latest)
    assert len(candidates)==25 and len({r['region_code'] for r in candidates})==25
    small=read(tables/'ukrstat_confirmed_oblast_baseline_candidates.csv');assert len(small)==1
    latest=confirmed[-1];assert small[0]['region_code']==latest['region_code'] and finite(small[0]['official_regional_baseline_proxy'])==finite(latest['value_million_UAH']) and small[0]['latest_period']==latest['source_period_label']+'-01-01'
    write(output/'oblast_candidates_reconciled.csv',sorted(candidates,key=lambda r:r['region_code']))
    constraint_path=raw/'ukrstat_availability_discovery_response_raw.json';constraint=json.loads(constraint_path.read_bytes());projection=constraint_projection(constraint);write(output/'constraint_metadata_summary.csv',projection)
    availability=read(tables/'ukrstat_availability_value_candidates.csv');annotations={a['id']:a['title'] for a in constraint['data']['dataConstraints'][0]['annotations']};values=[]
    for component_index,component in enumerate(constraint['data']['dataConstraints'][0]['cubeRegions'][0]['components']):
        for value_index,value in enumerate(component['values']):values.append((component['id'],value['value'],str(component['include']),f'data.dataConstraints[0].cubeRegions[0].components[{component_index}].values[{value_index}]'))
    wanted=Counter(values);actual=Counter((r['dimension_id'],r['value_code'],r['include_status'],r['component_path']) for r in availability if r['dimension_id']!='TIME_PERIOD');assert actual==wanted
    for row in availability:
        assert row['series_count']==annotations['series_count'] and row['time_period_start']==annotations['time_period_start'] and row['time_period_end']==annotations['time_period_end']
        if row['dimension_id']=='TIME_PERIOD':assert row['value_code']==annotations[row['value_description'].lower()]
    assert len(availability)==60
    # Bulk imported-code facts are verified internally, never republished as an imported raw listing.
    refs=json.loads((raw/'ukrstat_dsd_regional_accounts_6_references_raw.json').read_bytes());codelists=refs['data']['codelists']
    bylist={}
    for c in codelists:
        if 'codes' in c:bylist[(c['id'],c['version'])]={x['id']:x for x in c['codes']}
    code_rows=read(tables/'ukrstat_dimension_code_candidates.csv');groups=Counter();matched=0
    for row in code_rows:
        item=bylist[(row['codelist_id'],row['codelist_version'])][row['code_id']]
        assert item.get('name','')==row['code_name'] and item.get('description','')==row['code_description']
        matched+=1;groups[(row['dimension_id'],row['codelist_id'],row['codelist_version'])]+=1
    write(output/'bulk_codelist_reconciliation_summary.csv',[dict(dimension_heuristic_not_authoritative_DSD_mapping=k[0],codelist=k[1],version=k[2],rows_matched=count,raw_listing_publicly_bundled=False,query_validity_or_source_rights_inferred=False) for k,count in sorted(groups.items())])
    payload=json.loads((raw/'ukrstat_observation_data_response_raw.json').read_bytes());paths=read(tables/'ukrstat_observation_response_paths.csv');leaves=flatten(payload);assert len(leaves)==len(paths)==77
    assert Counter((r['json_path'],r['value_preview']) for r in paths)==Counter(leaves)
    assert not decode(payload)
    path_counts=Counter(path_role(path) for path,value in leaves);write(output/'response_path_scope_summary.csv',[dict(reviewed_role=role,leaf_paths=count,observed_values_proved=0) for role,count in sorted(path_counts.items())])
    result=dict(confirmed_numeric_values_matched=18,single_oblast_latest_candidate_matched=1,oblast_latest_candidates_matched=25,selected_retained_series_observations_decoded=450,availability_component_values_matched=len(values),availability_boundary_annotations_matched=2,availability_rows_matched=60,component_include_flags='false as supplied; no positive selector inferred',availability_end_is_not_observed_year=True,bulk_imported_code_rows_matched=matched,bulk_codelist_groups=len(groups),response_leaf_paths_matched=77,response_observation_values=0,source_period_labels_read_directly=True,availability_period_fallback_used=False,source_request_time_authenticated=False,production_scoring_changed=False,unverified_FIU_claims='excluded',publication_or_push=False)
    (output/'reconciliation_summary.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':print(json.dumps(run(Path.cwd(),Path(__file__).resolve().parent/'first_reconciliation'),indent=2))
