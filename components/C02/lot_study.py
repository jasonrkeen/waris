"""Frozen lot-aware descriptive study. No WARIS score or entity findings."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any
from capture_prozorro_sample import CapturePlan, capture, digest, now, save

COMPETITIVE=('aboveThreshold','aboveThresholdUA','aboveThresholdEU','belowThreshold','priceQuotation')
LIMITED=('reporting','negotiation','negotiation.quick')
ACTIVE=('active','active.enquiries','active.tendering','active.auction','active.qualification','active.awarded','active.pre-qualification','active.pre-qualification.stand-still')
BID_STATES=('active','draft','pending','invalid','deleted','invalid.pre-qualification','cancelled','unsuccessful')
LOT_STATES=('active','complete','cancelled','unsuccessful')

@dataclass(frozen=True)
class Plan:
    version: str='lot-aware-feasibility-1'
    details: int=100
    minimum_tender_clusters: int=5
    page_count: int=1

def spec()->dict:
    return {**asdict(Plan()),'selection':'One new page of 100 recently modified records, all IDs in order. No retries, replacements, extensions or outcome-based selection. Short page or any HTTP failure fails the study.',
     'sample_size_rationale':'Fixed 100-detail engineering feasibility budget, comparable to prior study; not powered for prevalence or national inference. Minimum five independent tender clusters is an engineering screen only.',
     'population':'Recent-modification convenience sample; not complete period, historical reconstruction or national sample. Cross-sectional status at capture, not lifecycle follow-up.',
     'development':'Prior 150/50/100 snapshots informed design only; not pooled or analyzed as independent validation.',
     'procedures':COMPETITIVE,'limited_procedures':LIMITED,'active_lifecycles':ACTIVE,'bid_states':BID_STATES,'lot_states':LOT_STATES,
     'units':'Explicit lots are separate units linked to parent tender cluster; absent/empty lots yields one no_explicit_lots unit. Invalid/duplicate lot IDs yield one quarantined placeholder. Do not mix unit types.',
     'eligibility':'Exact competitive procedure; parent status complete; unit status complete; mode absent/null; config absent or restricted false. Complete lots of complete tenders with other cancelled/unsuccessful lots remain eligible separately; other lot outcomes retained, not imputed.',
     'linkage':'Each visible bid needs a unique nonempty string ID. Explicit-lot bids need a nonempty lotValues list with unique, existing relatedLot links. Missing/invalid/orphan/duplicate links make all unit counts unknown, even for one explicit lot. Never allocate total tender bids to lots. No awards fallback.',
     'measures':'Visible linked bid objects and active linked offer objects, not firms or valid offers. Active requires bid.status active and lotValue.status absent or active. Missing lotValue.status is an explicitly assumed no-additional-filter rule because generic schema does not require it; unknown/invalid provided statuses quarantine counts. Missing/unknown bid status makes all counts unknown. Known inactive states retained but not active. No entity resolution or amendments-history reconstruction.',
     'missingness':'Missing/null/malformed bids unknown; empty list observed zero. In no-explicit-lots units, any nonempty or malformed lotValues is inconsistent and quarantines counts. Unknown is never zero.',
     'aggregation':'Exact procedure x parent lifecycle x unit type x unit status; tender is cluster. Primary rates only among eligible units with >=5 distinct eligible parent tenders and all eligible counts known in that stratum. Report distinct clusters, units, coverage, inactive objects and mixed-outcome tender counts. No confidence intervals or causal/AML inference.',
     'provenance':'Code/plan freeze precedes capture. Per-attempt raw receipts, ordered selection and exact file inventory verified. Feed/detail method/status/dateModified drift recorded, detail controls analysis. Partial capture retained but no study results.',
     'privacy_and_rights':'Raw bodies, record URLs, identifiers and all numeric results private pending separate clearance. No regional, sector, buyer or supplier outputs. Five is not legal anonymity. MIT code does not license source data.',
     'boundaries':'Core scores unchanged; GRP benchmark only, expanded Prozorro review only, FIU national context only with annual claims excluded; literature reference only.',
     'references':['https://prozorro-api-docs.readthedocs.io/en/latest/standard/bid.html','https://prozorro-api-docs.readthedocs.io/en/latest/standard/lot.html','https://prozorro-api-docs.readthedocs.io/en/latest/standard/tender.html','https://prozorro-api-docs.readthedocs.io/en/master/tendering/basic-actions/tenders.html']}

def life(s:Any)->str:
    if s in ('complete','cancelled','unsuccessful','draft'):return s
    return 'in_progress' if s in ACTIVE else 'unknown'

def usable_id(x:Any)->bool:return isinstance(x,str) and bool(x.strip())

def units(row:dict,cluster:int)->list[dict]:
    method=row.get('procurementMethodType');known=method in COMPETITIVE or method in LIMITED
    parent=life(row.get('status'));lots=row.get('lots',[])
    invalid=not isinstance(lots,list)
    if not invalid:
        ids=[x.get('id') if isinstance(x,dict) else None for x in lots]
        invalid=any(not usable_id(x) for x in ids) or len(set(ids))!=len(ids)
    if invalid:raw_units=[('invalid_lots',None,'unknown')]
    elif lots:raw_units=[('explicit_lot',x['id'],x.get('status')) for x in lots]
    else:raw_units=[('no_explicit_lots',None,row.get('status'))]
    config=row.get('config',{})
    unrestricted=isinstance(config,dict) and config.get('restricted',False) is False
    mixed=bool(not invalid and lots and len({x.get('status') if isinstance(x.get('status'),str) else 'unknown' for x in lots})>1)
    output=[]
    for grain,identifier,status in raw_units:
        unit_status=status if grain=='no_explicit_lots' else (status if status in LOT_STATES else 'unknown')
        eligible=bool(method in COMPETITIVE and parent=='complete' and unit_status=='complete' and unrestricted and row.get('mode') is None and grain!='invalid_lots')
        output.append({'cluster':cluster,'procedure':method if known else 'unreviewed_procedure','parent_lifecycle':parent,
            'unit_type':grain,'unit_status':unit_status if isinstance(unit_status,str) else 'unknown',
            'eligible':eligible,'mixed_outcome_parent':mixed,'visible_objects':None,'active_objects':None,
            'inactive_objects':None,'observation_status':'unknown','_lot':identifier})
    if invalid:return output
    bids=row.get('bids')
    def unknown(reason:str)->list[dict]:
        for u in output:u['observation_status']=reason
        return output
    if not isinstance(bids,list):return unknown('bids_missing_or_invalid')
    bids_ids=[b.get('id') if isinstance(b,dict) else None for b in bids]
    if any(not usable_id(x) for x in bids_ids) or len(set(bids_ids))!=len(bids_ids):return unknown('invalid_or_duplicate_bid_id')
    counts={u['_lot']:[0,0] for u in output}
    for bid in bids:
        state=bid.get('status')
        if state not in BID_STATES:return unknown('missing_or_unknown_bid_status')
        if lots:
            values=bid.get('lotValues')
            if not isinstance(values,list) or not values:return unknown('lot_links_missing_or_invalid')
            links=[v.get('relatedLot') if isinstance(v,dict) else None for v in values]
            if any(not usable_id(x) or x not in counts for x in links) or len(set(links))!=len(links):return unknown('orphan_or_duplicate_lot_link')
            for value in values:
                if 'status' in value and value['status'] not in BID_STATES:return unknown('unknown_lot_value_status')
                key=value['relatedLot'];counts[key][0]+=1
                counts[key][1]+=int(state=='active' and value.get('status','active')=='active')
        else:
            values=bid.get('lotValues',[])
            if not isinstance(values,list) or values:return unknown('lot_links_without_lots')
            counts[None][0]+=1;counts[None][1]+=int(state=='active')
    for u in output:
        visible,active=counts[u['_lot']]
        u.update(visible_objects=visible,active_objects=active,inactive_objects=visible-active,observation_status='observed')
    return output

def summarize(rows:list[dict])->dict:
    groups=defaultdict(list);all_units=[]
    for i,row in enumerate(rows):
        for unit in units(row,i):
            key=tuple(unit[k] for k in ('procedure','parent_lifecycle','unit_type','unit_status'))
            groups[key].append(unit);all_units.append(unit)
    result=[]
    for key,items in sorted(groups.items()):
        eligible=[x for x in items if x['eligible']];observed=[x for x in eligible if x['active_objects'] is not None]
        clusters=len({x['cluster'] for x in eligible})
        supported=clusters>=Plan().minimum_tender_clusters and len(observed)==len(eligible)
        result.append({**dict(zip(('procedure','parent_lifecycle','unit_type','unit_status'),key)),
            'units':len(items),'tender_clusters':len({x['cluster'] for x in items}),
            'mixed_outcome_tender_clusters':len({x['cluster'] for x in items if x['mixed_outcome_parent']}),
            'eligible_units':len(eligible),'eligible_tender_clusters':clusters,'eligible_observed_units':len(observed),
            'eligible_coverage':len(observed)/len(eligible) if eligible else None,
            'single_active_object_rate':sum(x['active_objects']==1 for x in observed)/len(observed) if supported else None,
            'single_visible_object_rate':sum(x['visible_objects']==1 for x in observed)/len(observed) if supported else None,
            'all_units_observation_status':dict(Counter(x['observation_status'] for x in items)),
            'observed_inactive_object_count':sum(x['inactive_objects'] for x in items if x['inactive_objects'] is not None),
            'rate_status':'descriptive_supported_private' if supported else 'withheld_ineligible_sparse_or_missing',
            'publication_status':'private_separate_review_required'})
    return {'captured_tenders':len(rows),'unit_count':len(all_units),'eligible_units':sum(x['eligible'] for x in all_units),
        'eligible_tender_clusters':len({x['cluster'] for x in all_units if x['eligible']}),'strata':result,
        'production_score_change':False,'population_inference':False}

def freeze(root:Path)->None:
    root.mkdir(parents=True,exist_ok=False);save(root/'study_plan.json',spec())
    save(root/'freeze.json',{'created_at_utc':now(),'plan_sha256':digest((root/'study_plan.json').read_bytes()),
         'code':{n:digest((Path(__file__).parent/n).read_bytes()) for n in ('lot_study.py','capture_prozorro_sample.py')},'stage':'before_acquisition'})

def verify_freeze(root:Path)->dict:
    f=json.loads((root/'freeze.json').read_text(encoding='utf8'))
    if digest((root/'study_plan.json').read_bytes())!=f['plan_sha256']:raise ValueError('Frozen plan changed')
    for n,h in f['code'].items():
        if n not in ('lot_study.py','capture_prozorro_sample.py') or digest((Path(__file__).parent/n).read_bytes())!=h:raise ValueError('Frozen code changed')
    if set(f['code'])!={'lot_study.py','capture_prozorro_sample.py'}:raise ValueError('Incomplete frozen code inventory')
    return f

def analyze(root:Path,output:Path)->dict:
    f=verify_freeze(root);raw=root/'private_capture'
    receipt=json.loads((raw/'capture_manifest.json').read_text(encoding='utf8'))
    specification=json.loads((raw/'capture_specification.json').read_text(encoding='utf8'))
    expected=['feed.json']+[f'detail_{i:03d}.json' for i in range(1,101)]
    if receipt['status']!='complete' or receipt['successful_details']!=100:raise ValueError('Incomplete capture')
    if [r['snapshot'] for r in receipt['responses']]!=expected:raise ValueError('Unexpected receipt inventory/order')
    if {p.name for p in raw.iterdir()}!=set(expected)|{'capture_manifest.json','capture_specification.json'}:raise ValueError('Unexpected raw file inventory')
    if receipt['specification_sha256']!=digest((raw/'capture_specification.json').read_bytes()) or specification['script_sha256']!=f['code']['capture_prozorro_sample.py'] or specification['plan']!={'page_limit':100,'detail_limit':100,'pause_seconds':0.25}:raise ValueError('Capture plan mismatch')
    if not f['created_at_utc']<receipt['created_at_utc']:raise ValueError('Capture predates freeze')
    for entry in receipt['responses']:
        p=raw/entry['snapshot']
        if entry['attempt_state']!='response_retained' or entry['http_status']!=200 or entry['requested_url']!=entry['final_url'] or entry['bytes']!=p.stat().st_size or digest(p.read_bytes())!=entry['sha256']:raise ValueError('Response integrity failed')
        if entry['started_at_utc']<receipt['created_at_utc']:raise ValueError('Invalid attempt timestamp')
    feed=json.loads((raw/'feed.json').read_text(encoding='utf8'))['data'];ids=[r['id'] for r in feed]
    if len(ids)!=100 or len(set(ids))!=100 or digest('\n'.join(ids).encode())!=receipt['selected_ordered_ids_sha256']:raise ValueError('Selection mismatch')
    rows=[];drift=Counter()
    for i,entry in enumerate(feed,1):
        row=json.loads((raw/f'detail_{i:03d}.json').read_text(encoding='utf8'))['data']
        if row['id']!=entry['id']:raise ValueError('Detail identity mismatch')
        for k in ('status','procurementMethodType','dateModified'):
            if k not in entry:drift[k+'_feed_missing']+=1
            elif entry[k]!=row.get(k):drift[k+'_changed']+=1
        rows.append(row)
    result=summarize(rows);result.update(frozen_plan_sha256=f['plan_sha256'],capture_manifest_sha256=digest((raw/'capture_manifest.json').read_bytes()),
        feed_detail_drift=dict(drift),capture_started_at_utc=receipt['created_at_utc'],capture_completed_at_utc=receipt['completed_at_utc'])
    output.mkdir(parents=True,exist_ok=False);save(output/'lot_study_results_PRIVATE.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['freeze','capture','analyze']);p.add_argument('--study-root',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='freeze':freeze(a.study_root)
    elif a.action=='capture':
        verify_freeze(a.study_root);r=capture(a.study_root/'private_capture',CapturePlan(page_limit=100,detail_limit=100));print(json.dumps({'status':r['status'],'details':r['successful_details']}))
    else:
        if a.output is None:p.error('--output required')
        r=analyze(a.study_root,a.output);print(json.dumps({k:r[k] for k in ('captured_tenders','unit_count','eligible_units','eligible_tender_clusters')}))
