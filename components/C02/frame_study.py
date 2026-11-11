"""Recorded finite-frame probability sampling; never national procurement inference."""
from __future__ import annotations
import argparse,json,random,re,secrets,time
from dataclasses import dataclass,asdict
from collections import Counter
from pathlib import Path
from typing import Any
import requests
from capture_prozorro_sample import BASE_URL,now,save,digest
from lot_study import units,summarize

PROCEDURES=('aboveThreshold','priceQuotation')

@dataclass(frozen=True)
class Plan:
    version:str='recorded-cursor-frame-1'
    max_pages:int=10
    page_size:int=100
    sample_per_procedure:int=40

def specification(seed:str)->dict:
    return {**asdict(Plan()),'seed':seed,'procedures':PROCEDURES,
      'target':'Unique IDs first observed in at most ten consecutive descending API pages, starting without offset. Operational recorded frame only; not national, calendar-period, creation-date or all-completed procurement.',
      'frame_stop':'Follow next_page.offset on fixed base endpoint. Stop at first empty page or after page 10 regardless of outcomes. Nonempty short pages do not terminate early. Missing/repeated/unsafe cursor before cap fails. No retries, substitutions or extra pages.',
      'duplicates':'Reject duplicate IDs within a page. Across pages keep first observed metadata and record duplicate and conflicting metadata counts. Do not infer snapshot isolation or period completeness.',
      'selection':'After all frame pages, define two domains by first-observed exact procedure and status complete. Independently sample min(40,N) IDs without replacement using random.Random(seed+procedure).sample on sorted IDs. Seed generated before frame acquisition. Census when N<=40; zero domain remains zero. Freeze private selection with N,n, inclusion probability and N/n weight before detail requests.',
      'budget':'At most 1000 feed records and 80 details. This fixed feasibility budget is not a power calculation; no stopping when a desired rate or eligible count appears.',
      'eligibility':'Reused immutable lot-aware rules determine detail eligibility and counts. Feed-to-detail changes remain sample members; no replacements, no reclassification into the other sampling domain.',
      'estimands':'Conditional on recorded feed-defined domain, detail-time eligible units and exactly-one-visible/active-linked-object totals estimated by tender-cluster Horvitz-Thompson weights N/n. Ratio is weighted numerator/denominator, not an unbiased ratio estimate. Detail-domain drift contributes zero eligible units; unknown eligible counts withhold rates. Domains and unit types never pooled.',
      'support':'At least five distinct sampled eligible tender clusters in exact domain, detail procedure and unit type, with complete eligible count observation; otherwise null. Finite-frame weights do not correct frame undercoverage, hidden records, modification bias or changes during traversal. No confidence intervals or national extrapolation.',
      'provenance':'Plan/code frozen before first request, complete frame/selection before first detail, per-attempt retained response hashes and exact inventories verified. HTTP/schema failure leaves failed_partial and no analysis.',
      'boundaries':'No production score changes. GRP benchmark only; expanded procurement review only; FIU national context only with unverified annual claims excluded; literature reference only.',
      'publication':'All provider data, IDs, selected membership, record URLs, weights and numeric diagnostics private pending separate review. MIT code is not source-data permission.',
      'references':['https://prozorro-api-docs-uk.readthedocs.io/uk/master/basic-actions/feed.html','https://data.open-contracting.org/en/publication/154']}

def freeze(root:Path)->None:
    root.mkdir(parents=True,exist_ok=False)
    save(root/'study_plan.json',specification(secrets.token_hex(32)))
    save(root/'freeze.json',{'created_at_utc':now(),'plan_sha256':digest((root/'study_plan.json').read_bytes()),
       'code':{n:digest((Path(__file__).parent/n).read_bytes()) for n in ('frame_study.py','lot_study.py','capture_prozorro_sample.py')}})

def verify_freeze(root:Path)->dict:
    f=json.loads((root/'freeze.json').read_text(encoding='utf8'))
    if digest((root/'study_plan.json').read_bytes())!=f['plan_sha256']:raise ValueError('Frozen plan changed')
    if set(f['code'])!={'frame_study.py','lot_study.py','capture_prozorro_sample.py'}:raise ValueError('Frozen inventory changed')
    for n,h in f['code'].items():
        if digest((Path(__file__).parent/n).read_bytes())!=h:raise ValueError('Frozen code changed')
    return f

def build_frame(pages:list[list[dict]])->tuple[list[dict],dict]:
    seen={};duplicates=0;conflicts=0
    for page in pages:
        if not isinstance(page,list) or len(page)>100:raise ValueError('Invalid page schema/count')
        ids=[x.get('id') if isinstance(x,dict) else None for x in page]
        if any(not isinstance(i,str) or not re.fullmatch('[a-f0-9]{32}',i) for i in ids) or len(set(ids))!=len(ids):raise ValueError('Invalid page identities')
        for row in page:
            key=row['id']
            if key in seen:
                duplicates+=1
                conflicts+=int(any(seen[key].get(k)!=row.get(k) for k in ('status','procurementMethodType','dateModified','public_modified')))
            else:seen[key]=row
    return list(seen.values()),{'cross_page_duplicate_occurrences':duplicates,'cross_page_conflicting_occurrences':conflicts}

def select(frame:list[dict],seed:str)->dict:
    domains={}
    for method in PROCEDURES:
        ids=sorted(x['id'] for x in frame if x.get('status')=='complete' and x.get('procurementMethodType')==method)
        n=min(Plan().sample_per_procedure,len(ids));chosen=random.Random(seed+'|'+method).sample(ids,n)
        domains[method]={'N':len(ids),'n':n,'inclusion_probability':n/len(ids) if ids else None,
            'cluster_weight':len(ids)/n if n else None,'selected_ids':chosen}
    return domains

def safe_cursor(value:Any,seen:set[str])->str:
    if not isinstance(value,str) or not value or len(value)>4096 or value in seen or any(ord(c)<32 for c in value):raise ValueError('Missing/repeated/unsafe cursor')
    return value

def acquire(root:Path,session:Any=None)->dict:
    frozen=verify_freeze(root);plan=json.loads((root/'study_plan.json').read_text(encoding='utf8'))
    raw=root/'private_capture';raw.mkdir(exist_ok=False)
    record={'status':'started','created_at_utc':now(),'plan_sha256':frozen['plan_sha256'],'responses':[]}
    manifest=raw/'capture_manifest.json';save(manifest,record)
    client=session or requests.Session()
    if session is None:
        class PublicAuth(requests.auth.AuthBase):
            def __call__(self,r):r.headers.pop('Authorization',None);return r
        client.auth=PublicAuth()
    def request(url:str,name:str,params:dict|None=None)->dict:
        entry={'snapshot':name,'requested_url':requests.Request('GET',url,params=params).prepare().url,'started_at_utc':now(),'attempt_state':'started'}
        record['responses'].append(entry);save(manifest,record)
        r=client.get(url,params=params,timeout=(10,35),allow_redirects=False,headers={'User-Agent':'WARIS bounded recorded-frame research capture'})
        (raw/name).write_bytes(r.content)
        entry.update(final_url=r.url,completed_at_utc=now(),http_status=r.status_code,bytes=len(r.content),sha256=digest(r.content),attempt_state='response_retained',
            response_headers={k:r.headers[k] for k in ('Date','ETag','Last-Modified','Content-Type') if k in r.headers})
        save(manifest,record)
        if r.status_code!=200 or r.url!=entry['requested_url']:raise ValueError('Unexpected HTTP status/URL')
        return json.loads(r.content)
    try:
        pages=[];cursors=set();cursor=None
        for page in range(1,11):
            params={'limit':100,'descending':'1','opt_fields':'id,dateModified,status,procurementMethodType,public_modified'}
            if cursor is not None:params['offset']=cursor
            response=request(BASE_URL,f'feed_{page:02d}.json',params);data=response.get('data')
            build_frame([data]);pages.append(data)
            if not data:record['frame_stop']='empty_page';break
            if page==10:record['frame_stop']='fixed_page_cap';break
            cursor=safe_cursor(response.get('next_page',{}).get('offset'),cursors);cursors.add(cursor)
            time.sleep(.25)
        frame,duplicate_info=build_frame(pages);selection=select(frame,plan['seed'])
        save(raw/'frame.json',frame);save(raw/'selection.json',selection)
        record.update(frame_pages=len(pages),frame_rows=sum(map(len,pages)),unique_frame_tenders=len(frame),duplicate_info=duplicate_info,
            frame_sha256=digest((raw/'frame.json').read_bytes()),selection_sha256=digest((raw/'selection.json').read_bytes()),selection_frozen_at_utc=now())
        save(manifest,record)
        ordered=[i for method in PROCEDURES for i in selection[method]['selected_ids']]
        for index,identifier in enumerate(ordered,1):
            payload=request(BASE_URL+'/'+identifier,f'detail_{index:03d}.json')
            if not isinstance(payload.get('data'),dict) or payload['data'].get('id')!=identifier:raise ValueError('Detail identity mismatch')
            time.sleep(.25)
        record.update(status='complete',completed_at_utc=now(),successful_details=len(ordered));save(manifest,record);return record
    except Exception as error:
        record.update(status='failed_partial',failed_at_utc=now(),error_type=type(error).__name__);save(manifest,record);raise
    finally:
        if session is None:client.close()

def estimates(frame:list[dict],selection:dict,details:list[dict])->dict:
    ordered=[(method,i) for method in PROCEDURES for i in selection[method]['selected_ids']]
    if len(details)!=len(ordered):raise ValueError('Detail count differs from selection')
    groups={};drift=Counter();lookup={x['id']:x for x in frame}
    for index,((domain,identifier),row) in enumerate(zip(ordered,details)):
        if row.get('id')!=identifier:raise ValueError('Selected detail order mismatch')
        for key in ('status','procurementMethodType','dateModified'):
            if lookup[identifier].get(key)!=row.get(key):drift[key+'_changed']+=1
        for unit in units(row,index):
            key=(domain,unit['procedure'],unit['unit_type'])
            groups.setdefault(key,[]).append(unit)
    output=[]
    for (domain,method,grain),items in sorted(groups.items()):
        # Detail drift stays in the original sampling domain; not pooled across methods.
        eligible=[x for x in items if x['eligible'] and method==domain]
        observed=[x for x in eligible if x['active_objects'] is not None]
        clusters=len({x['cluster'] for x in eligible});w=selection[domain]['cluster_weight']
        supported=clusters>=5 and len(observed)==len(eligible)
        output.append({'sampling_domain':domain,'detail_procedure':method,'unit_type':grain,'sampled_units':len(items),
            'eligible_units':len(eligible),'eligible_sampled_clusters':clusters,'eligible_observed_units':len(observed),
            'cluster_weight':w,'eligible_unit_HT_total':len(eligible)*w,
            'single_active_HT_total':sum(x['active_objects']==1 for x in observed)*w if len(observed)==len(eligible) else None,
            'single_active_ratio':sum(x['active_objects']==1 for x in observed)/len(eligible) if supported else None,
            'single_visible_ratio':sum(x['visible_objects']==1 for x in observed)/len(eligible) if supported else None,
            'support':'supported_within_recorded_frame_only' if supported else 'withheld_sparse_ineligible_or_unknown',
            'publication_status':'private_review_required'})
    return {'frame_unique_tenders':len(frame),'domains':{k:{a:b for a,b in v.items() if a!='selected_ids'} for k,v in selection.items()},
        'selected_details':len(details),'feed_detail_drift':dict(drift),'estimates':output,'lot_observation_diagnostics':summarize(details),
        'national_or_period_inference':False,'production_score_change':False}

def analyze(root:Path,output:Path)->dict:
    frozen=verify_freeze(root);raw=root/'private_capture';record=json.loads((raw/'capture_manifest.json').read_text())
    if record['status']!='complete' or record['plan_sha256']!=frozen['plan_sha256'] or not frozen['created_at_utc']<record['created_at_utc']<record['selection_frozen_at_utc']:raise ValueError('Incomplete/unfrozen capture')
    if not 1<=record['frame_pages']<=10:raise ValueError('Frame pages outside plan')
    expected=[f'feed_{i:02d}.json' for i in range(1,record['frame_pages']+1)]+[f'detail_{i:03d}.json' for i in range(1,record['successful_details']+1)]
    if [x['snapshot'] for x in record['responses']]!=expected or {p.name for p in raw.iterdir()}!=set(expected)|{'capture_manifest.json','frame.json','selection.json'}:raise ValueError('Wrong receipt/file inventory')
    for e in record['responses']:
        body=(raw/e['snapshot']).read_bytes()
        if e['http_status']!=200 or e['requested_url']!=e['final_url'] or digest(body)!=e['sha256'] or len(body)!=e['bytes'] or e['attempt_state']!='response_retained':raise ValueError('Response integrity failure')
        if e['started_at_utc']<record['created_at_utc']:raise ValueError('Attempt predates acquisition')
        if e['snapshot'].startswith('detail_') and e['started_at_utc']<record['selection_frozen_at_utc']:raise ValueError('Selection not frozen before details')
    pages=[];seen=set();cursor=None
    for index in range(1,record['frame_pages']+1):
        payload=json.loads((raw/f'feed_{index:02d}.json').read_text());pages.append(payload['data'])
        params={'limit':100,'descending':'1','opt_fields':'id,dateModified,status,procurementMethodType,public_modified'}
        if cursor is not None:params['offset']=cursor
        url=requests.Request('GET',BASE_URL,params=params).prepare().url
        if url!=record['responses'][index-1]['requested_url']:raise ValueError('Cursor chain mismatch')
        if index<record['frame_pages']:
            if not payload['data']:raise ValueError('Traversed past empty page')
            cursor=safe_cursor(payload.get('next_page',{}).get('offset'),seen);seen.add(cursor)
    if pages[-1]:
        if len(pages)!=10 or record['frame_stop']!='fixed_page_cap':raise ValueError('Stopped before fixed cap')
    elif record['frame_stop']!='empty_page':raise ValueError('Invalid stop classification')
    frame,duplicate_info=build_frame(pages);plan=json.loads((root/'study_plan.json').read_text());selection=select(frame,plan['seed'])
    for name,value in [('frame',frame),('selection',selection)]:
        p=raw/(name+'.json')
        if value!=json.loads(p.read_text()) or digest(p.read_bytes())!=record[name+'_sha256']:raise ValueError('Frame/selection changed')
    if duplicate_info!=record['duplicate_info']:raise ValueError('Duplicate audit mismatch')
    details=[json.loads((raw/f'detail_{i:03d}.json').read_text())['data'] for i in range(1,record['successful_details']+1)]
    ordered=[i for method in PROCEDURES for i in selection[method]['selected_ids']]
    for index,identifier in enumerate(ordered):
        if record['responses'][len(pages)+index]['requested_url']!=BASE_URL+'/'+identifier:raise ValueError('Detail request URL mismatch')
    if record['frame_rows']!=sum(map(len,pages)) or record['unique_frame_tenders']!=len(frame):raise ValueError('Frame count mismatch')
    result=estimates(frame,selection,details)
    result.update(plan_sha256=frozen['plan_sha256'],capture_manifest_sha256=digest((raw/'capture_manifest.json').read_bytes()),
        frame_pages=len(pages),frame_rows=sum(map(len,pages)),duplicate_info=duplicate_info,capture_started_at_utc=record['created_at_utc'],capture_completed_at_utc=record['completed_at_utc'])
    output.mkdir(parents=True,exist_ok=False);save(output/'frame_results_PRIVATE.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','capture','analyze']);p.add_argument('--study-root',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='freeze':freeze(a.study_root)
    elif a.action=='capture':
        r=acquire(a.study_root);print(json.dumps({'status':r['status'],'frame_tenders':r['unique_frame_tenders'],'sampled_details':r['successful_details']}))
    else:
        if a.output is None:p.error('--output required')
        r=analyze(a.study_root,a.output);print(json.dumps({'frame_tenders':r['frame_unique_tenders'],'sampled_details':r['selected_details']}))
