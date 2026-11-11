"""Qualitative documentation policy; no ordinal arithmetic or calibrated reliability."""
from __future__ import annotations

from dataclasses import dataclass
import json
import pandas as pd
from .controlled_guards import validate_confidence_labels


@dataclass(frozen=True)
class ConfidencePolicy:
    version: str = 'confidence-categorical-1'
    labels: tuple[str, ...] = ('High','Medium-High','Medium','Medium-Low','Low','Unknown')
    urgency: tuple[str, ...] = ('Low','Medium','High')


POLICY = ConfidencePolicy()


def summarize_confidence(fields: pd.DataFrame) -> pd.DataFrame:
    required = ('field_name','model_area','current_source_type','confidence_level','replacement_priority')
    if not set(required).issubset(fields.columns) or fields.empty:
        raise ValueError('Nonempty field register with explicit identity, labels and priority required')
    if any(fields[c].isna().any() or fields[c].astype(str).str.strip().eq('').any() for c in required):
        raise ValueError('Blank field identity, group, confidence or priority')
    if fields.field_name.duplicated().any():
        raise ValueError('Duplicate field identity; do not inflate confidence counts')
    validate_confidence_labels(fields.to_dict('records'))
    if not fields.replacement_priority.isin(POLICY.urgency).all():
        raise ValueError('Unrecognised replacement priority; no default urgency')
    result = []
    for (area,source_type),group in fields.groupby(['model_area','current_source_type'],sort=True):
        counts = {label:int(group.confidence_level.eq(label).sum()) for label in POLICY.labels}
        priority = next(label for label in reversed(POLICY.urgency) if group.replacement_priority.eq(label).any())
        result.append(dict(model_area=area,current_source_type=source_type,field_count=len(group),confidence_label_counts=json.dumps(counts,separators=(',',':')),unknown_confidence_fields=counts['Unknown'],confidence_interpretation='; '.join(f'{k}: {v}' for k,v in counts.items() if v)+' (declared; uncalibrated)',replacement_priority_interpretation=priority+' replacement priority',highest_declared_replacement_priority=priority,confidence_policy_version=POLICY.version,assessment_scope='first_party_declared_qualitative_labels_only',empirical_reliability_established=False,source_rights_established=False,used_in_scoring=False,used_in_monte_carlo=False,production_score_change='none'))
    return pd.DataFrame(result)
