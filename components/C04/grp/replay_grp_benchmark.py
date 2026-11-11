"""Rebuild the reviewed GRP benchmark from retained, hashed official responses."""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from decimal import Decimal
from pathlib import Path


def rebuild(snapshots: Path, receipt_path: Path, output: Path) -> dict:
    if output.exists():raise ValueError('Output must be new')
    receipt=json.loads(receipt_path.read_text(encoding='utf8'));rows=[];codes=set()
    for entry in receipt['receipts']:
        code=entry['region_code']
        if not re.fullmatch('UA[0-9]+',code) or code in codes:raise ValueError('Invalid or duplicate region')
        codes.add(code);raw=(snapshots/(code+'.json')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['response_sha256']:raise ValueError('Source integrity mismatch')
        payload=json.loads(raw);ds=payload['data']['dataSets'][0];st=payload['data']['structures'][0]
        if len(ds['series'])!=1:raise ValueError('Unexpected series count')
        key,series=next(iter(ds['series'].items()))
        dims={d['id']:d['values'][int(i)]['id'] for d,i in zip(st['dimensions']['series'],key.split(':'))}
        if dims!={'INDICATOR':'GRP','REGION':code,'NACE':'_Z','FREQ':'A'}:raise ValueError('Source dimensions mismatch')
        periods=st['dimensions']['observation'][0]['values']
        values={str(periods[int(i)].get('value',periods[int(i)].get('id'))):v for i,v in series['observations'].items()}
        row=dict(receipt['reviewed_row_metadata'][code]);row['value_million_UAH']=str(Decimal(str(values[receipt['period']][0])))
        rows.append(row)
    if len(rows)!=receipt['records']:raise ValueError('Region count mismatch')
    rows.sort(key=lambda r:r['region_code']);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=receipt['output_columns']);writer.writeheader();writer.writerows(rows)
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    if digest!=receipt['supplement_sha256']:raise ValueError('Rebuilt supplement differs from reviewed file')
    return {'rows':len(rows),'period':receipt['period'],'sha256':digest,'byte_identical':True,'use':'benchmark_only'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots',type=Path,required=True);parser.add_argument('--receipt',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(rebuild(args.snapshots,args.receipt,args.output)))
