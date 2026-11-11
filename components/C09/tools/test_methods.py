import copy
import pytest
from methods import rescale,documentation_projection

def inputs():
    official=[dict(waris_oblast=f'R{i}',official_grp_million_uah=str(i+10)) for i in range(25)]
    synthetic=[dict(oblast=f'R{i}',sector=f'S{j}',prewar_revenue_index_2021=str(j+10),current_revenue_index=str((j+10)/2)) for i in range(25) for j in range(6)]
    return official,synthetic

def test_region_sum_is_six_times_index_not_GRP_currency():
    a,b=inputs();out=rescale(a,b);mean=sum(float(r['official_grp_million_uah']) for r in a)/25
    assert len(out)==150
    for row in a:
        assert sum(r['scenario_prewar_revenue_index_2021'] for r in out if r['oblast']==row['waris_oblast'])==pytest.approx(6*float(row['official_grp_million_uah'])/mean*100)

def test_prototype_change_ratio_preserved():
    assert all(r['scenario_current_revenue_index']/r['scenario_prewar_revenue_index_2021']==pytest.approx(.5) for r in rescale(*inputs()))

def test_missing_sector_rejected():
    a,b=inputs()
    with pytest.raises(ValueError):rescale(a,b[:-1])

def test_duplicate_sector_rejected():
    a,b=inputs();b[0]['sector']=b[1]['sector']
    with pytest.raises(ValueError):rescale(a,b)

@pytest.mark.parametrize('value',['0','NaN','Infinity'])
def test_invalid_synthetic_inputs_rejected(value):
    a,b=inputs();b[0]['prewar_revenue_index_2021']=value
    with pytest.raises(ValueError):rescale(a,b)

def test_duplicate_region_rejected():
    a,b=inputs();a[0]['waris_oblast']=a[1]['waris_oblast']
    with pytest.raises(ValueError):rescale(a,b)

def test_unmapped_region_rejected():
    a,b=inputs();b[0]['oblast']='Unexpected'
    with pytest.raises(ValueError):rescale(a,b)

def test_mixed_scores_never_pass_into_projection():
    a,b=inputs();expected=rescale(a,b)
    for row in b:row.update(waris_aml_review_score='UNREVIEWED',conflict_proxy='UNREVIEWED')
    assert rescale(a,b)==expected and all('waris_aml_review_score' not in r for r in expected)

def bridge():
    return [dict(operational_artifact_family=name,artifact_status='available',artifact_summary='historical count only',current_use='documentation',production_score_change='none',used_in_scoring='False',used_in_monte_carlo='False') for name in ['analyst_review_workflow','false_positive_controls','source_freshness','run_manifest']]

def test_presence_does_not_establish_effectiveness_or_current_freshness():
    assert all(r['current_freshness_verified'] is False and r['empirical_effectiveness_verified'] is False and r['production_scoring_approved'] is False for r in documentation_projection(bridge()))

@pytest.mark.parametrize('field',['used_in_scoring','used_in_monte_carlo'])
def test_asserted_flag_stops_instead_of_being_reset(field):
    rows=bridge();rows[0][field]='True'
    with pytest.raises(ValueError):documentation_projection(rows)

@pytest.mark.parametrize('field',['used_in_scoring','used_in_monte_carlo'])
def test_missing_flag_stops(field):
    rows=bridge();del rows[0][field]
    with pytest.raises(ValueError):documentation_projection(rows)

def test_declared_score_change_stops():
    rows=bridge();rows[0]['production_score_change']='changed'
    with pytest.raises(ValueError):documentation_projection(rows)

def test_duplicate_control_family_stops():
    rows=bridge();rows[0]['operational_artifact_family']=rows[1]['operational_artifact_family']
    with pytest.raises(ValueError):documentation_projection(rows)
