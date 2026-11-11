"""Controlled preparation guards; no provider data or scoring authorization."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any
import pandas as pd
import csv,json,math
from collections import defaultdict

@dataclass(frozen=True)
class ArtifactStructure:
    content_state: str
    row_count: int | None
    content_record_count: int | None
    artifact_format: str
    parse_status: str


def require_acled_clearance() -> None:
    raise RuntimeError('ACLED acquisition and cache enrichment held: original acquisition evidence and output-specific rights remain unresolved. Use offline_demo.py.')

def assert_context_flags(frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    for field in ('used_in_scoring','used_in_monte_carlo'):
        if field not in frame or not frame[field].map(lambda v: str(v).lower()=='false').all():
            raise ValueError('Context use flag missing or asserted; refusing to overwrite it')
    if 'production_score_change' not in frame or not frame.production_score_change.eq('none').all():
        raise ValueError('Undocumented context score change')

def validate_confidence_labels(rows: list[dict[str, Any]]) -> None:
    allowed={'High','Medium-High','Medium','Medium-Low','Low','Unknown'}
    if not rows or any(r.get('confidence_level') not in allowed for r in rows):
        raise ValueError('Missing/unmapped confidence label; explicit mapping policy required')

def artifact_structure(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return asdict(ArtifactStructure(content_state='missing',row_count=None,content_record_count=None,artifact_format=path.suffix,parse_status='missing'))
    try:
        if path.suffix.lower()=='.json':
            value=json.loads(path.read_text(encoding='utf-8-sig'))
            if not isinstance(value,(dict,list)):
                raise ValueError('Expected JSON object or array')
            count=len(value)
            return asdict(ArtifactStructure(content_state='present' if count else 'empty',row_count=None,content_record_count=count,artifact_format='.json',parse_status='parsed_object_keys' if isinstance(value,dict) else 'parsed_array_items'))
        if path.suffix.lower()=='.csv':
            with path.open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f)
                if not reader.fieldnames:raise ValueError('Missing CSV header')
                count=sum(1 for row in reader)
            return asdict(ArtifactStructure(content_state='present' if count else 'empty',row_count=count,content_record_count=count,artifact_format='.csv',parse_status='parsed'))
        return asdict(ArtifactStructure(content_state='unparsed',row_count=None,content_record_count=None,artifact_format=path.suffix,parse_status='unsupported'))
    except (ValueError,UnicodeError,csv.Error):
        return asdict(ArtifactStructure(content_state='invalid',row_count=None,content_record_count=None,artifact_format=path.suffix,parse_status='invalid'))


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
