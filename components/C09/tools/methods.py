from pathlib import Path
from collections import defaultdict
from typing import Any
import csv,json,math,hashlib

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path:Path)->list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(path:Path,rows:list[dict[str,Any]])->None:
    with path.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def rescale(official:list[dict],synthetic:list[dict])->list[dict]:
    if len(official)!=25 or len({r['waris_oblast'] for r in official})!=25:raise ValueError('Expected reviewed 25-region universe')
    amounts={r['waris_oblast']:float(r['official_grp_million_uah']) for r in official}
    if any(not math.isfinite(v) or v<=0 for v in amounts.values()):raise ValueError('Invalid GRP')
    grouped=defaultdict(list);seen=set()
    for row in synthetic:
        key=(row['oblast'],row['sector'])
        if key in seen:raise ValueError('Duplicate synthetic sector')
        seen.add(key);grouped[row['oblast']].append(row)
        if any(not math.isfinite(float(row[k])) or float(row[k])<=0 for k in ('prewar_revenue_index_2021','current_revenue_index')):raise ValueError('Invalid synthetic index')
    if set(grouped)!=set(amounts) or any(len(v)!=6 for v in grouped.values()):raise ValueError('Require six unique synthetic sectors for each of 25 regions; no arbitrary allocation approval')
    mean=sum(amounts.values())/25;result=[]
    for name,rows in grouped.items():
        total=sum(float(r['prewar_revenue_index_2021']) for r in rows);scale=amounts[name]/mean*100
        for r in rows:
            pre=float(r['prewar_revenue_index_2021']);current=float(r['current_revenue_index']);share=pre/total;scenario=scale*share*6
            result.append(dict(oblast=name,sector=r['sector'],official_grp_million_uah=amounts[name],official_oblast_scale_index=scale,sector_share_within_oblast=share,prewar_revenue_index_2021=pre,scenario_prewar_revenue_index_2021=scenario,current_revenue_index=current,scenario_current_revenue_index=scenario*current/pre,original_revenue_change_pct=(current/pre-1)*100))
    return sorted(result,key=lambda r:(r['oblast'],r['sector']))
def documentation_projection(bridge:list[dict])->list[dict]:
    expected={'analyst_review_workflow','false_positive_controls','source_freshness','run_manifest'}
    if len(bridge)!=4 or {r['operational_artifact_family'] for r in bridge}!=expected:raise ValueError('Expected four unique documentation families')
    result=[]
    for row in bridge:
        for field in ('used_in_scoring','used_in_monte_carlo'):
            if str(row.get(field,'')).lower()!='false':raise ValueError('Missing or asserted use flag; do not overwrite it with false')
        if row.get('production_score_change')!='none':raise ValueError('Unreviewed declared score change')
        family=row['operational_artifact_family']
        result.append(dict(family=family,historical_artifact_presence=row['artifact_status'],historical_summary_as_recorded=row['artifact_summary'],declared_current_use=row['current_use'],review_scope='Historical documentation counts/flags only, not completed review, measured false-positive performance, source vintage, runtime enforcement or current freshness.',current_freshness_verified=False,empirical_effectiveness_verified=False,production_scoring_approved=False,unverified_FIU_claims='excluded'))
    return sorted(result,key=lambda r:r['family'])
