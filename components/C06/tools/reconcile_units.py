"""Reconcile selected GRP unit evidence without filling missing observations."""
from pathlib import Path
from decimal import Decimal
from collections import Counter
from typing import Any
import csv,json,hashlib

YEARS=[str(y) for y in range(2004,2022)]
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path:Path)->list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path:Path,records:list[dict[str,Any]])->None:
    with path.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
def decimal(value:Any)->Decimal|None:
    if value is None or value=='':return None
    result=Decimal(str(value))
    if not result.is_finite():raise ValueError('Non-finite source observation')
    return result
def positional_long(path:Path)->list[list[str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f);headers=next(reader);data=list(reader)
    expected=['Indicator','Indicator','Region','Region','Economic activity type','Economic activity type','Frequency','Frequency','Time period','Observation value','Unit of measure','Unit of measure','Scaling','Scaling','Decimals displayed','Decimals displayed','Observation flag','Observation flag','Dataset notes','Timeseries notes','Observation notes']
    if headers!=expected or any(len(row)!=21 for row in data):raise ValueError('Unexpected positional export schema')
    return [r for r in data if (r[0],r[4],r[6])==('GRP','_Z','A')]
def keyed(records:list, key)->dict:
    result={}
    for row in records:
        k=key(row)
        if k in result:raise ValueError('Duplicate observation/series key')
        result[k]=row
    return result
def english(value:Any)->str:
    if value is None:return ''
    if isinstance(value,dict):return value.get('en',json.dumps(value,ensure_ascii=False,sort_keys=True))
    return str(value)
def decode_api(payload:dict)->dict[str,Any]:
    data=payload['data']
    if len(data['dataSets'])!=1 or len(data['structures'])!=1:raise ValueError('Expected one structure/dataset')
    ds=data['dataSets'][0];st=data['structures'][0]
    if len(ds['series'])!=1:raise ValueError('Expected one series')
    series_key,series=next(iter(ds['series'].items()))
    dims=st['dimensions']['series'];positions=series_key.split(':')
    if len(dims)!=len(positions):raise ValueError('Series dimension mismatch')
    identity={spec['id']:spec['values'][int(index)]['id'] for spec,index in zip(dims,positions)}
    if identity.get('INDICATOR')!='GRP' or identity.get('NACE')!='_Z' or identity.get('FREQ')!='A':raise ValueError('Wrong series identity')
    specs=st['attributes']['series'];attributes=series.get('attributes',[])
    if len(specs)!=len(attributes):raise ValueError('Attribute alignment mismatch')
    attrs={}
    for spec,value in zip(specs,attributes):
        attrs[spec['id']]=spec['values'][value]['id'] if isinstance(value,int) and 'values' in spec else value
    if (attrs.get('UNITS_OF_MEASURE'),attrs.get('SCALE'),attrs.get('DECIMALS_DISPLAYED'))!=('1090','6','0'):raise ValueError('Unit/scale/decimals mismatch')
    times=st['dimensions']['observation']
    if len(times)!=1 or times[0]['id']!='TIME_PERIOD':raise ValueError('Time axis mismatch')
    periods=times[0]['values'];observations={}
    for index,entry in series['observations'].items():
        period=str(periods[int(index)].get('value',periods[int(index)].get('id')))
        if period not in YEARS:continue
        if period in observations:raise ValueError('Duplicate period')
        extras={spec['id']:entry[i+1] if i+1<len(entry) else None for i,spec in enumerate(st['attributes']['observation'])}
        observations[period]=dict(value=decimal(entry[0]),flag=english(extras.get('OBS_FLAG')),note=english(extras.get('NOTES_OBS')))
    return dict(region_code=identity['REGION'],attributes=attrs,observations=observations,structure_annotations=st.get('annotations',[]))

def reconcile(long:list[list[str]],wide:list[dict],historical:list[dict],api:dict[str,dict],mapping:dict[str,str])->tuple:
    li=keyed(long,lambda r:(r[2],r[8]));wi=keyed([r for r in wide if (r['Indicator'],r['Economic activity type'],r['Frequency'])==('Gross regional product','Not applicable','Annual')],lambda r:r['Region'])
    names={}
    for r in long:
        if r[2] in names and names[r[2]]!=r[3]:raise ValueError('Identifier has inconsistent label')
        names[r[2]]=r[3]
    if set(names)!=set(api) or set(names.values())!=set(wi):raise ValueError('Region/series coverage mismatch')
    hi=keyed(historical,lambda r:(r['region_name'],r['time_period']))
    evidence=[];slots=[];profiles=[];note_differences=[]
    for code,label in sorted(names.items()):
        source=api[code];w=wi[label];stats=Counter()
        if source['region_code']!=code:raise ValueError('API region mismatch')
        for year in YEARS:
            l=li.get((code,year));a=source['observations'].get(year);wv=decimal(w[year])
            if l is None:
                if a is not None or wv is not None:raise ValueError('Absent slot mismatch across sources')
                status='absent_in_long_and_API'
            else:
                if a is None or decimal(l[9])!=a['value'] or decimal(l[9])!=wv:raise ValueError('Value/presence mismatch across sources')
                if l[20]!=a['note'] or l[17]!=a['flag'] or l[19]!=english(source['attributes'].get('NOTES_TS')):raise ValueError('Long/API observation note, flag or series note mismatch')
                if (l[10],l[11],l[12],l[13],l[14],l[15])!=('1090','UAH','6','Millions','0','Zero'):raise ValueError('Long units mismatch')
                status='explicit_not_available' if a['value'] is None else 'numeric_value_matched'
                if l[20]!=w['Observation notes']:
                    note_differences.append(dict(region_code=code,region_label=label,period=year,long_observation_note=l[20],wide_series_level_note=w['Observation notes'],resolution='retain_wide_note_as_series_export_field_not_per_year_status'))
                if a['value'] is not None:
                    h=hi.pop((label,year))
                    expected=dict(indicator_code=l[0],indicator_name=l[1],region_code=label,region_name=label,waris_oblast=mapping.get(label,label),nace_code=l[4],nace_name=l[5],freq_code=l[6],freq_name=l[7],time_period=year,observation_value=l[9],unit_code=l[11],unit_name=l[11],scaling_code=l[13],scaling_name=l[13],decimals_code=l[15],decimals_name=l[15])
                    for key,value in expected.items():
                        if key=='observation_value':
                            if decimal(h[key])!=decimal(value):raise ValueError('Historical value mismatch')
                        elif h[key]!=value:raise ValueError('Historical field mismatch: '+key)
                    evidence.append(dict(region_code=code,source_region_label=label,waris_oblast=mapping.get(label,''),geography_role='national_aggregate_not_additive_to_regions' if label=='Ukraine' else ('WARIS_region' if label in mapping else 'outside_WARIS_universe'),indicator_code='GRP',nace_code='_Z',frequency='A',period=year,value_million_UAH=str(a['value']),unit_code='1090',unit_label='UAH',scale_code='6',scale_label='Millions',decimals_code='0',source_observation_flag=a['flag'],source_observation_note=a['note'],source_timeseries_note=english(source['attributes'].get('NOTES_TS')),wide_export_series_note_not_per_year=w['Observation notes'],used_in_scoring=False,use_scope='historical_unit_and_benchmark_evidence_only'))
            stats[status]+=1
            slots.append(dict(region_code=code,source_region_label=label,period=year,source_state=status,value_million_UAH='' if a is None or a['value'] is None else str(a['value'])))
        profiles.append(dict(region_code=code,source_region_label=label,geography_role='national_aggregate' if label=='Ukraine' else ('WARIS_region' if label in mapping else 'outside_WARIS_universe'),period_min='2004',period_max='2021',numeric_observations=stats['numeric_value_matched'],explicit_unavailable=stats['explicit_not_available'],absent_slots=stats['absent_in_long_and_API'],unit_code='1090',unit_label='UAH',scale_code='6',scale_label='Millions',source_timeseries_note=english(source['attributes'].get('NOTES_TS')),wide_export_series_note_not_per_year=w['Observation notes'],used_in_scoring=False))
    if hi:raise ValueError('Unmatched historical evidence rows')
    return evidence,slots,profiles,note_differences

def run(root:Path,output:Path)->dict:
    base=root/'work/original/waris_ukraine_aml_risk_model_publish';work=root/'work/ukrstat_units_validation_20261020'
    source_long=next((base/'data/raw').glob('*21_19_35*.csv'));source_wide=next((base/'data/raw').glob('*21_23_00*.csv'))
    long=positional_long(source_long);wide=read(source_wide);historical=read(base/'outputs/tables/official_baseline_unit_evidence.csv')
    import sys
    sys.path.insert(0,str(root/'work/release_candidate/WARIS-v0.12.0-rc11'))
    from src.official_baseline_merge_plan import UKRSTAT_TO_WARIS_OBLAST as mapping
    api={};receipts=json.loads((root/'outputs/WARIS_Cleared_Research_Supplements_2026-10-18/grp/acquisition_receipt.json').read_text())['receipts']+json.loads((work/'source_fetches/receipts.json').read_text())
    for receipt in receipts:
        code=receipt['region_code'];p=(work/'source_fetches'/f'{code}.json') if code in ('UA00000000000000000','UA01000000000013043','UA85000000000065278') else (root/'work/artifact_clearance_20261018/grp'/f'{code}.json')
        if sha(p)!=receipt['response_sha256']:raise ValueError('Source receipt fingerprint mismatch')
        api[code]=decode_api(json.loads(p.read_bytes()))
    evidence,slots,profiles,differences=reconcile(long,wide,historical,api,mapping)
    output.mkdir(exist_ok=False)
    for name,records in [('historical_GRP_unit_evidence_reconciled.csv',evidence),('source_slots_PRIVATE.csv',slots),('series_unit_coverage.csv',profiles),('note_reconciliation.csv',differences)]:write(output/name,records)
    summary=dict(review_date_local='2026-10-20',historical_rows_matched=len(evidence),historical_fields_per_row=17,long_GRP_rows=len(long),expected_region_year_slots=len(slots),source_state_counts=dict(Counter(r['source_state'] for r in slots)),source_series=len(profiles),WARIS_series=sum(r['geography_role']=='WARIS_region' for r in profiles),wide_note_field_differences=len(differences),national_series_not_additive_to_regions=True,old_code_fields_contain_labels=True,original_HTTP_timestamp_recovered=False,production_scoring_changed=False,sector_allocation_approved=False,long_sha256=sha(source_long),wide_sha256=sha(source_wide),historical_evidence_sha256=sha(base/'outputs/tables/official_baseline_unit_evidence.csv'),api_response_receipts=receipts)
    (output/'reconciliation.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    return summary

if __name__=='__main__':
    result=run(Path.cwd(),Path(__file__).resolve().parent/'reconciliation_first')
    print(json.dumps({k:v for k,v in result.items() if k!='api_response_receipts'},indent=2))
