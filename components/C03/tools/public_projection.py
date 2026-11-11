"""Explicitly reviewed coarse release projection; not automatic future clearance."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import argparse,csv,json,hashlib

REVIEWED_RESULT_SHA256='80f16c7432cb488805e701f158e75a10f48ca9c0792cdd2a8f3590245c8862a4'
REVIEWED_PLAN_SHA256='a63ccf9b2071d363dd81e5b609cc767e17c7ca1777b4e1d3c681fb413d3ef8a6'
SCOPES={'aboveThreshold':'explicit_lot','priceQuotation':'no_explicit_lots'}

@dataclass(frozen=True)
class Projection:
    observed: list[dict]
    weighted: list[dict]

def fraction(n:int,d:int)->str:
    return format(Decimal(n)/Decimal(d),'f')

def project(result:dict)->Projection:
    if result.get('national_or_period_inference') is not False or result.get('production_score_change') is not False:
        raise ValueError('Protected boundary missing or changed')
    if result.get('plan_sha256')!=REVIEWED_PLAN_SHA256:raise ValueError('Unreviewed plan')
    if len(result.get('estimates',[]))!=2 or set(result.get('domains',{}))!=set(SCOPES):raise ValueError('Unreviewed domain layout')
    observed=[];weighted=[];seen=set()
    for e in result['estimates']:
        method=e['sampling_domain'];domain=result['domains'][method]
        if method in seen or method not in SCOPES or e['detail_procedure']!=method or e['unit_type']!=SCOPES[method]:raise ValueError('Unreviewed stratum')
        seen.add(method)
        N,n=domain['N'],domain['n'];den=e['eligible_units'];clusters=e['eligible_sampled_clusters']
        if any(type(x) is not int for x in (N,n,den,clusters)) or not (0<n<=N and 5<=clusters<=n and den>=clusters):raise ValueError('Insufficient or invalid support')
        if e['eligible_observed_units']!=den or e['support']!='supported_within_recorded_frame_only':raise ValueError('Missing observation support')
        # Recover observed numerator, then require integer consistency with retained ratio and HT total.
        numerator=int(round(e['single_active_ratio']*den));visible=int(round(e['single_visible_ratio']*den))
        if not (0<=numerator<=den and 0<=visible<=den):raise ValueError('Invalid numerator')
        if abs(numerator/den-e['single_active_ratio'])>1e-12 or abs(visible/den-e['single_visible_ratio'])>1e-12:raise ValueError('Ratio not consistent with integer counts')
        weight=Decimal(N)/Decimal(n)
        if abs(float(weight)-domain['cluster_weight'])>1e-12 or abs(n/N-domain['inclusion_probability'])>1e-12:raise ValueError('Sampling metadata inconsistent')
        if abs(float(Decimal(numerator)*weight)-e['single_active_HT_total'])>1e-10 or abs(float(Decimal(den)*weight)-e['eligible_unit_HT_total'])>1e-10:raise ValueError('Weighted totals inconsistent')
        common={'study_id':'WARIS-PROC-FRAME-20261020','procedure':method,'unit_type':e['unit_type'],
            'retrieval_date_utc':'2026-10-20','scope':'recorded_API_frame_only','use_scope':'descriptive_research_only','used_in_scoring':False}
        common.update(source_publisher='Prozorro public procurement API',source_url='https://public.api.openprocurement.org/api/2.5/tenders',
            transformation='Procedure/lifecycle-conditioned linked bid-object counts; tender-cluster sampling')
        observed.append({**common,'domain_frame_tenders':N,'sampled_tenders':n,'eligible_sampled_tender_clusters':clusters,
            'observed_eligible_units':den,'observed_exactly_one_active_object_units':numerator,
            'observed_exactly_one_visible_object_units':visible,'active_object_share':fraction(numerator,den),'visible_object_share':fraction(visible,den)})
        weighted.append({**common,'domain_frame_tenders':N,'sampled_tenders':n,'tender_inclusion_probability_fraction':f'{n}/{N}',
            'cluster_weight_fraction':f'{N}/{n}','HT_eligible_unit_total':format(Decimal(den)*weight,'f'),
            'HT_exactly_one_active_object_total':format(Decimal(numerator)*weight,'f'),
            'ratio_of_HT_totals':fraction(numerator,den),'total_status':'census_within_recorded_domain' if n==N else 'estimated_not_observed_unsampled_records'})
    return Projection(observed,weighted)

def write_csv(path:Path,rows:list[dict])->None:
    with path.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

def export(source:Path,destination:Path)->Projection:
    if hashlib.sha256(source.read_bytes()).hexdigest()!=REVIEWED_RESULT_SHA256:raise ValueError('Unreviewed input bytes; new clearance required')
    projection=project(json.loads(source.read_text(encoding='utf8')))
    destination.mkdir(parents=True,exist_ok=False)
    write_csv(destination/'procurement_observed_summary.csv',projection.observed)
    write_csv(destination/'procurement_frame_weighted_estimates.csv',projection.weighted)
    return projection

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('private_results',type=Path);p.add_argument('new_destination',type=Path);a=p.parse_args()
    export(a.private_results,a.new_destination)
