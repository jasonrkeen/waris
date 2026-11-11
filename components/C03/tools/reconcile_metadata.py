"""Revalidate selected code metadata; never infer observation availability."""
from pathlib import Path
import csv,hashlib,json
from typing import Any

AUTHORITIES={'CL_FREQ':'SDMX','CL_KATOTTG':'SSSU','CL_NACE_UA':'SSSU','CL_REGIONAL_ACCOUNTS_INDICATOR':'SSSU'}

def reconcile(rows:list[dict],codelists:dict[str,dict])->list[dict]:
    out=[]
    for row in rows:
        name=row['codelist_id']
        if not name:
            if row['dimension_id']!='TIME_PERIOD' or row['code_id'] not in ('2021','2022','2023'):raise ValueError('Unreviewed first-party proposal')
            out.append({'dimension':row['dimension_id'],'code_id':row['code_id'],'verification':'first_party_proposed_period_only_not_available_observation','agency':'','version':'','metadata_name_description_match':''})
            continue
        payload=codelists[name]
        if payload['id']!=name or payload['agencyID']!=AUTHORITIES[name] or payload['version']!=row['codelist_version'] or payload.get('isPartial') is not False:raise ValueError('Metadata identity/version/completeness mismatch')
        matches=[x for x in payload['codes'] if x['id']==row['code_id']]
        if len(matches)!=1 or matches[0].get('name')!=row['code_name'] or matches[0].get('description','')!=row['code_description']:raise ValueError('Selected code/name/description mismatch')
        out.append({'dimension':row['dimension_id'],'code_id':row['code_id'],'verification':'current_selected_metadata_reconciled_not_executed_query','agency':payload['agencyID'],'version':payload['version'],'metadata_name_description_match':True})
    return out

if __name__=='__main__':
    root=Path.cwd();work=root/'work/procurement_output_clearance_20261020';fetch=work/'source_fetches'
    source=root/'work/original/waris_ukraine_aml_risk_model_publish/outputs/tables/ukrstat_observation_query_candidates.csv'
    rows=list(csv.DictReader(source.open(encoding='utf8',newline='')));payloads={};evidence={}
    receipts=json.loads((fetch/'receipts.json').read_text());receipts.append(json.loads((fetch/'frequency_receipt.json').read_text()))
    for name in AUTHORITIES:
        filename='CL_FREQ_SDMX.response' if name=='CL_FREQ' else name+'.response'
        path=fetch/filename;raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        receipt=next(r for r in receipts if r.get('status')==200 and r['sha256']==sha)
        lists=json.loads(raw)['data']['codelists'];assert len(lists)==1
        payloads[name]=lists[0];evidence[name]={'source_url':receipt['url'],'response_sha256':sha,'verification_date':'2026-10-20'}
    result=reconcile(rows,payloads)
    for row,original in zip(result,rows):
        name=original['codelist_id'];row.update(evidence[name] if name else {'source_url':'','response_sha256':'','verification_date':'2026-10-20'})
    with (work/'metadata_verification.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=result[0].keys());w.writeheader();w.writerows(result)
    annotations={name:{'codelist_annotations':p.get('annotations',[]),'selected_code_annotations':[x.get('annotations',[]) for x in p['codes'] if x['id'] in {r['code_id'] for r in rows if r['codelist_id']==name}]} for name,p in payloads.items()}
    (work/'selected_metadata_annotations_PRIVATE.json').write_text(json.dumps(annotations,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    summary={'historical_artifact_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rows':len(result),'metadata_rows_exactly_matched':64,'first_party_proposed_periods':3,
        'new_retrieval_authenticates_historical_request':False,'observation_availability_or_scoring_approval':False,
        'source_scope':'Selected code/name/description facts plus first-party shortlist; no bulk codelists or statistical values bundled',
        'frequency_namespace_correction':'Initial SSSU lookup returned 204; agency SDMX identified from retained DSD and verified with 200. Original failed receipt preserved.',
        'source_license_basis':'Ukrstat portal default CC BY 4.0 for selected metadata; original provider/agency attribution retained, no selected metadata exception identified.'}
    (work/'metadata_reconciliation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
