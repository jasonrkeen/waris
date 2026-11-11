"""Rebuild the cleared context CSV from privately retained official API snapshots.

This performs no downloads. A future API response is a new vintage and cannot
replace the recorded snapshots without a new review and acquisition receipt.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from decimal import Decimal
from pathlib import Path


def rebuild(snapshots: Path, receipt_path: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError('Output must be new; original artifacts are preserved')
    receipt=json.loads(receipt_path.read_text(encoding='utf8'))
    rows=[]
    for entry in receipt['receipts']:
        code=entry['indicator_code'];raw=(snapshots/(code+'.json')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['response_sha256']:
            raise ValueError('API snapshot integrity mismatch')
        payload=json.loads(raw,parse_float=Decimal)
        if payload[0]['pages']!=1 or payload[0]['total']!=len(payload[1]):
            raise ValueError('Incomplete source pagination')
        for r in payload[1]:
            if r['countryiso3code']!='UKR' or r['indicator']['id']!=code:
                raise ValueError('Country or indicator mismatch')
            value='' if r['value'] is None else str(r['value'])
            rows.append({'country_code':'UKR','indicator_code':code,'indicator_name':r['indicator']['value'],
                'year':r['date'],'value':value,'value_status':'missing_not_imputed' if not value else 'reported_api_value',
                'unit':'percent_of_GDP' if code=='GC.TAX.TOTL.GD.ZS' else 'current_USD',
                'series_license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
                'source_url':entry['source_url'],'api_url':entry['api_url'],'api_response_sha256':entry['response_sha256'],
                'retrieved_at_utc':entry['retrieved_at_utc'],'source_last_updated':entry['source_last_updated'],
                'underlying_provider_credit':receipt['credits_by_indicator'][code],'use_scope':'national_context_only_not_scoring'})
    rows.sort(key=lambda r:(r['indicator_code'],int(r['year'])))
    if len(rows)!=receipt['rows'] or len({(r['country_code'],r['indicator_code'],r['year']) for r in rows})!=len(rows):
        raise ValueError('Unexpected row count or duplicate grain')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',encoding='utf8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    if digest!=receipt['supplement_sha256']:
        raise ValueError('Rebuilt table does not match the reviewed supplement')
    return {'rows':len(rows),'missing_not_imputed':sum(not r['value'] for r in rows),'sha256':digest,'byte_identical':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(rebuild(args.snapshots,args.receipt,args.output)))
