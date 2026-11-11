from copy import deepcopy
from pathlib import Path
import json
import pytest
from methods import money, artifact_structure, sfms_projection, SFMS_REFERRALS, SFMS_FUNDS, SFMS_CATEGORIES, review_recount
from methods import validate_confidence_labels

def fixture():
    return [dict(referral_context_id=f'FIU-NABU-{i+1:03}',reporting_period='2026-Q1',production_score_change='none',used_in_waris_scoring='False',used_in_monte_carlo='False',case_referrals_and_additional_referrals=str(n),funds_related_to_crime_uah_mln=f,person_category=SFMS_CATEGORIES[i]) for i,(n,f) in enumerate(zip(SFMS_REFERRALS,SFMS_FUNDS))]

def test_source_zero_and_decimal_comma():
    assert money('0,00') == 0
    assert str(money('41,28')) == '41.28'

@pytest.mark.parametrize('value',['','NaN','Infinity','-1','0.001'])
def test_missing_or_invalid_amount_rejected(value):
    with pytest.raises(ValueError): money(value)

def test_separate_total_and_duplicate_category_rows():
    out=sfms_projection(fixture())
    assert len(out)==10 and out[-1]['row_role']=='published_total_do_not_add'
    assert out[2]['referral_documents']==4 and out[7]['referral_documents']==1
    assert sum(r['referral_documents'] for r in out[:-1])==out[-1]['referral_documents']

@pytest.mark.parametrize('field,value',[('used_in_waris_scoring','True'),('funds_related_to_crime_uah_mln',''),('reporting_period','2025-Q1'),('case_referrals_and_additional_referrals','12')])
def test_wrong_source_or_use_flags_rejected(field,value):
    rows=fixture(); rows[0][field]=value
    with pytest.raises(ValueError): sfms_projection(rows)

def test_json_is_not_empty_csv(tmp_path):
    p=tmp_path/'manifest.json'; p.write_text(json.dumps({'run_id':'example','artifacts':[1]}))
    got=artifact_structure(p)
    assert got['data_rows'] is None and got['json_top_level_keys']==2

def test_no_freshness_inference_from_csv(tmp_path):
    p=tmp_path/'table.csv';p.write_text('a\n1\n')
    assert artifact_structure(p)['data_rows']==1
    assert 'fresh' not in str(artifact_structure(p))

def test_empty_queue_not_vacuously_safe():
    with pytest.raises(ValueError): review_recount([],[],[],[])

@pytest.mark.parametrize('label',['Medium-High','new_label',''])
def test_unmapped_confidence_never_silently_defaults(label):
    with pytest.raises(ValueError): validate_confidence_labels([{'confidence_level':label}])

def test_explicit_unknown_is_preserved_as_declared():
    validate_confidence_labels([{'confidence_level':'Unknown'}])
