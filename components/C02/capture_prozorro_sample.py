"""Capture a planned bounded PUBLIC sample into a NEW PRIVATE directory.

No credentials, attachments or automatic publication. One feed page only.
"""
from __future__ import annotations
import argparse,hashlib,json,re,time
from dataclasses import asdict,dataclass
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
import requests

BASE_URL="https://public.api.openprocurement.org/api/2.5/tenders"


@dataclass(frozen=True)
class CapturePlan:
    page_limit:int=100
    detail_limit:int=50
    pause_seconds:float=0.25
    def __post_init__(self)->None:
        if not (1<=self.detail_limit<=self.page_limit<=100):raise ValueError("Invalid bounded sample sizes")
        if not (0<=self.pause_seconds<=10):raise ValueError("Invalid pause")


def now()->str:return datetime.now(timezone.utc).isoformat()
def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def save(path:Path,value:Any)->None:
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8');temp.replace(path)


def capture(destination:Path,plan:CapturePlan,session:Any=None)->dict:
    """Retain every attempted response; stop on error, without replacing failures."""
    destination.mkdir(parents=True,exist_ok=False)
    specification={'plan':asdict(plan),'base_url':BASE_URL,'feed_pages':1,'selection':'first detail_limit IDs in returned feed order, with no substitutions',
        'descending':'requested; chronological completeness not assumed','scope':'bounded convenience sample, not national/date-period totals',
        'attachments':False,'authentication':False,'follow_redirects':False,'script_sha256':digest(Path(__file__).read_bytes())}
    save(destination/'capture_specification.json',specification)
    record={'status':'started','created_at_utc':now(),'specification_sha256':digest((destination/'capture_specification.json').read_bytes()),
            'responses':[],'raw_material':'PRIVATE; not publication approved'}
    manifest=destination/'capture_manifest.json';save(manifest,record)
    client=session or requests.Session()
    if session is None:
        class PublicOnlyAuth(requests.auth.AuthBase):
            def __call__(self, request: Any) -> Any:
                request.headers.pop("Authorization", None)
                return request
        client.auth = PublicOnlyAuth()  # Prevent implicit netrc credentials; retain proxy/CA settings.
    def request(url:str,filename:str,params:dict|None=None)->dict:
        entry={'requested_url':requests.Request('GET',url,params=params).prepare().url,
               'started_at_utc':now(),'attempt_state':'started','snapshot':filename}
        record['responses'].append(entry);save(manifest,record)
        response=client.get(url,params=params,timeout=(10,35),allow_redirects=False,
                            headers={'User-Agent':'WARIS bounded public procurement provenance capture'})
        data=response.content;(destination/filename).write_bytes(data)
        entry.update({'final_url':response.url,'completed_at_utc':now(),
            'http_status':response.status_code,'bytes':len(data),'sha256':digest(data),'attempt_state':'response_retained',
            'response_headers':{k:response.headers[k] for k in ['Date','ETag','Last-Modified','Content-Type'] if k in response.headers}})
        save(manifest,record)
        if response.status_code!=200 or response.url!=entry['requested_url']:
            raise ValueError('Unexpected response status or URL; see private receipt')
        return json.loads(data)
    try:
        params={'limit':plan.page_limit,'descending':'1','opt_fields':'id,dateModified,status,procurementMethodType'}
        feed=request(BASE_URL,'feed.json',params);rows=feed.get('data')
        if not isinstance(rows,list) or len(rows)>plan.page_limit or len(rows)<plan.detail_limit:raise ValueError('Unexpected feed count/schema')
        ids=[r.get('id') for r in rows if isinstance(r,dict)]
        if len(ids)!=len(rows) or any(not isinstance(x,str) or not re.fullmatch('[a-f0-9]{32}',x) for x in ids) or len(set(ids))!=len(ids):
            raise ValueError('Invalid/duplicate feed identities')
        selected=ids[:plan.detail_limit]
        record.update({'feed_rows':len(rows),'next_page':feed.get('next_page'),'selected_ordered_ids_sha256':digest('\n'.join(selected).encode())})
        save(manifest,record)
        for i,identifier in enumerate(selected,1):
            payload=request(BASE_URL+'/'+identifier,f'detail_{i:03d}.json')
            row=payload.get('data')
            if not isinstance(row,dict) or row.get('id')!=identifier:raise ValueError('Detail identity/schema mismatch')
            time.sleep(plan.pause_seconds)
        record.update({'status':'complete','completed_at_utc':now(),'successful_details':len(selected),'additional_pages_followed':0})
        save(manifest,record);return record
    except Exception as error:
        record.update({'status':'failed_partial','failed_at_utc':now(),'error_type':type(error).__name__})
        save(manifest,record);raise
    finally:
        if session is None:client.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--private-output',type=Path,required=True)
    parser.add_argument('--details',type=int,default=50);args=parser.parse_args()
    result=capture(args.private_output,CapturePlan(detail_limit=args.details))
    print(json.dumps({'status':result['status'],'feed_rows':result['feed_rows'],'successful_details':result['successful_details']}))
