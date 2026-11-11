"""Separate preparation checks; no provider access or production score changes."""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

SFMS_REFERRALS = (13, 5, 4, 7, 2, 17, 7, 1, 14, 70)
SFMS_FUNDS = ('0.00', '41.28', '0.00', '27117.94', '0.00', '16.57', '63.08', '2.24', '0.00', '27241.11')
SFMS_CATEGORIES = ('members of the Cabinet of Ministers of Ukraine and their deputies', 'members of parliament and deputies of local councils', 'heads of the central executive authorities', 'civil servants', 'judges', 'senior commanders and the rest of the soldiers', 'heads of state enterprises', 'heads of the central executive authorities', 'other persons', 'total')

def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def write(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError('Explicit rows required')
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_confidence_labels(rows: list[dict[str, str]]) -> None:
    """Require an explicit policy instead of silently scoring unmapped labels."""
    allowed = {'High', 'Medium', 'Medium-Low', 'Low', 'Unknown'}
    if not rows or any(row.get('confidence_level') not in allowed for row in rows):
        raise ValueError('Missing/unmapped confidence label; mapping policy required')

def money(text: str) -> Decimal:
    try:
        value = Decimal(text.replace(',', '.'))
    except InvalidOperation as exc:
        raise ValueError('Invalid source amount') from exc
    if not value.is_finite() or value < 0 or value != value.quantize(Decimal('.01')):
        raise ValueError('Nonnegative finite two-decimal amount required')
    return value

def sfms_projection(rows: list[dict[str, str]]) -> list[dict]:
    """Match every row to the newly read official quarterly text; never infer missing."""
    if len(rows) != 10:
        raise ValueError('Nine categories and one separate total required')
    out = []
    for i, row in enumerate(rows):
        if row['referral_context_id'] != f'FIU-NABU-{i+1:03}' or row['reporting_period'] != '2026-Q1':
            raise ValueError('Period/order mismatch')
        if row['person_category'] != SFMS_CATEGORIES[i]:
            raise ValueError('Source category mismatch')
        if row['production_score_change'] != 'none' or row['used_in_waris_scoring'] != 'False' or row['used_in_monte_carlo'] != 'False':
            raise ValueError('Non-scoring context flags required')
        amount = money(row['funds_related_to_crime_uah_mln'])
        if int(row['case_referrals_and_additional_referrals']) != SFMS_REFERRALS[i] or amount != money(SFMS_FUNDS[i]):
            raise ValueError('Official source mismatch')
        out.append(dict(source_row='total' if i == 9 else str(i+1), reporting_period='2026-Q1', category_as_published=SFMS_CATEGORIES[i], row_role='published_total_do_not_add' if i == 9 else 'category', referral_documents=SFMS_REFERRALS[i], source_reported_associated_funds_million_UAH=f'{amount:.2f}', category_label_repeated_in_source=i in (2,7), context_only=True, used_in_scoring=False, used_in_monte_carlo=False))
    if sum(SFMS_REFERRALS[:-1]) != SFMS_REFERRALS[-1] or sum(map(money,SFMS_FUNDS[:-1])) != money(SFMS_FUNDS[-1]):
        raise ValueError('Source total mismatch')
    if rows[2]['person_category'] != rows[7]['person_category'] or rows[9]['person_category'] != 'total':
        raise ValueError('Duplicate-label/total structure changed')
    return out

def artifact_structure(path: Path) -> dict:
    """Report structure, never age-derived freshness or provider provenance."""
    if not path.is_file():
        return dict(exists=False, format=path.suffix, parse_status='missing', data_rows=None, json_top_level_keys=None)
    if path.suffix.lower() == '.json':
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        return dict(exists=True, format='.json', parse_status='parsed', data_rows=None, json_top_level_keys=len(value) if isinstance(value,dict) else None)
    if path.suffix.lower() == '.csv':
        return dict(exists=True, format='.csv', parse_status='parsed', data_rows=len(read(path)), json_top_level_keys=None)
    return dict(exists=True, format=path.suffix, parse_status='not_parsed', data_rows=None, json_top_level_keys=None)

def review_recount(queue: list[dict], questions: list[dict], checklist: list[dict], controls: list[dict]) -> dict:
    if not queue or not controls:
        raise ValueError('Nonempty review evidence required')
    for row in queue:
        if row['human_review_required'] != 'True' or row['automated_adverse_action_allowed'] != 'False' or row['entity_level_findings_allowed'] != 'False':
            raise ValueError('Unsafe declared workflow flag')
    if any(r['production_score_change'] != 'none' for r in controls):
        raise ValueError('Score change declared')
    return dict(queue_rows=len(queue), question_rows=len(questions), checklist_rows=len(checklist), control_rows=len(controls), declared_control_status_counts=dict(Counter(r['test_status'] for r in controls)), queue_status_counts=dict(Counter(r['review_status'] for r in queue)), nonblank_dispositions=sum(bool(r.get('analyst_disposition','').strip()) for r in queue), nonblank_review_dates=sum(bool(r.get('date_reviewed','').strip()) for r in queue), checklist_status_counts=dict(Counter(r['checklist_status'] for r in checklist)), empirical_false_positive_rate_established=False, runtime_control_effectiveness_established=False, provider_freshness_established=False)
