"""Selected annual regional GRP decoder; benchmark-only, no inferred dates."""
from __future__ import annotations
from decimal import Decimal
from typing import Any
import json,re

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
    if any(not i.isdigit() or int(i)>=len(d['values']) for d,i in zip(dims,indices)):raise ValueError('Invalid series index')
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
