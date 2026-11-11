import copy,json
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest
from src import live_data,source_confidence,source_freshness,official_baseline_merge_review as review,official_baseline_merge_plan as plan,ukrstat_observations as observations
from src.controlled_guards import assert_context_flags,artifact_structure
from src.strict_grp import decode
from test_strict_grp_prepared import fixture

@pytest.mark.parametrize('value',[True,'True',None,'',1,'nan'])
def test_operational_reviewer_rejects_asserted_or_missing_use_flag(tmp_path,value):
    frame=pd.DataFrame([dict(used_in_scoring=value,used_in_monte_carlo=False,production_score_change='none')])
    with patch.object(review,'TABLE_DIR',tmp_path),patch.object(review,'_safe_read_csv',return_value=frame):
        with pytest.raises(ValueError):review.build_operational_controls_context_review()
    assert not list(tmp_path.glob('*.csv'))

def test_false_context_flags_survive_actual_reviewer(tmp_path):
    frame=pd.DataFrame([dict(operational_artifact_family='run_manifest',used_in_scoring=False,used_in_monte_carlo=False,production_score_change='none')])
    target=tmp_path/'review.csv'
    with patch.object(review,'TABLE_DIR',tmp_path),patch.object(review,'_safe_read_csv',return_value=frame),patch.object(review,'OFFICIAL_BASELINE_OPERATIONAL_CONTROLS_CONTEXT_REVIEW_TABLE',target):
        result=review.build_operational_controls_context_review()
    assert not result.used_in_scoring.any() and not result.used_in_monte_carlo.any()

def test_acled_gate_precedes_cache_credentials_and_network(tmp_path):
    with patch.object(live_data,'_get_acled_credentials',side_effect=AssertionError('credentials touched')),patch('requests.get',side_effect=AssertionError('network touched')),patch.object(pd,'read_csv',side_effect=AssertionError('cache touched')):
        with pytest.raises(RuntimeError,match='ACLED acquisition'):live_data.fetch_acled_ukraine()

def test_main_preflight_precedes_dotenv_and_all_provider_work():
    import main
    with patch('sys.argv',['main.py','--allow-live']),patch.object(main,'load_dotenv',side_effect=AssertionError('dotenv touched')),patch.object(main,'enrich_with_optional_live_data',side_effect=AssertionError('provider work touched')):
        with pytest.raises(RuntimeError,match='ACLED acquisition'):main.main()

def test_json_structure_not_misclassified_as_empty_or_current(tmp_path):
    p=tmp_path/'manifest.json';p.write_text(json.dumps({'run_id':'demo','artifacts':[]}))
    specs=[dict(path=p,source_family='run_manifest',artifact_name='manifest',expected_use='documentation',current_use='run_manifest_documentation',scoring_dependency=False,freshness_expectation_days=30)]
    with patch.object(source_freshness,'EXPECTED_SOURCE_ARTIFACTS',specs):
        inventory=source_freshness._build_inventory()
    assert inventory.content_record_count.item()==2 and pd.isna(inventory.row_count.item())
    assessment=source_freshness._build_assessment(inventory)
    assert assessment.freshness_status.item()=='source_freshness_unverified'
    summary=source_freshness._build_summary(inventory,assessment)
    assert summary.loc[summary.summary_area.eq('Overall freshness posture'),'status'].item()=='review_required'
    assert not assessment.provider_freshness_verified.any()

def test_invalid_json_is_not_available_evidence(tmp_path):
    p=tmp_path/'manifest.json';p.write_text('{')
    assert artifact_structure(p)['content_state']=='invalid'

def test_confidence_guard_runs_before_file_output(tmp_path):
    frame=pd.DataFrame([dict(field_name='example',model_area='demo',current_source_type='synthetic',confidence_level='Unsupported',replacement_priority='Low')])
    with patch.object(source_confidence,'TABLE_DIR',tmp_path):
        with pytest.raises(ValueError,match='mapping policy'):source_confidence.build_source_confidence_assessment(frame)
    assert not list(tmp_path.glob('*.csv'))

def test_valid_confidence_entrypoint_returns_categorical_counts(tmp_path):
    frame=pd.DataFrame([dict(field_name='example',model_area='demo',current_source_type='synthetic',confidence_level='High',replacement_priority='Low')])
    with patch.object(source_confidence,'TABLE_DIR',tmp_path),patch.object(source_confidence,'SOURCE_CONFIDENCE_TABLE',tmp_path/'confidence.csv'):
        result=source_confidence.build_source_confidence_assessment(frame)
    assert 'avg_confidence_score' not in result
    assert json.loads(result.confidence_label_counts.item())['High']==1

def test_actual_parser_preserves_sparse_labels_null_zero_and_identity():
    data=fixture();series=data['data']['dataSets'][0]['series']['0:0:0:0'];series['observations']={'0':[0],'1':[None]}
    rows=observations._parse_sdmx_observations_to_rows(data,{},pd.DataFrame({'time_period_start':['1990']}))
    assert [r['time_period'] for r in rows]==['2004','2006']
    assert rows[0]['obs_value']=='0' and rows[1]['source_state']=='explicit_unavailable'
    with pytest.raises(ValueError):observations._parse_sdmx_observations_to_rows(data,{'region_code':'WRONG'})

def test_all_parser_entry_points_use_strict_decoder(tmp_path):
    p=tmp_path/'response.json';data=fixture();data['data']['structures'][0]['dimensions']['observation'][0]['values']=[];p.write_text(json.dumps(data))
    with patch.object(observations,'TABLE_DIR',tmp_path),patch.object(observations,'RAW_DIR',tmp_path),patch.object(observations,'UKRSTAT_CONFIRMED_SERIES_RAW',p),patch.object(observations,'UKRSTAT_OBSERVATION_DATA_RESPONSE_RAW',p):
        with pytest.raises(ValueError):observations.parse_confirmed_series_response()
        with pytest.raises(ValueError):observations.parse_observation_probe_response(pd.DataFrame(),pd.DataFrame())

def test_negative_series_index_cannot_select_last_axis_value():
    data=fixture();series=data['data']['dataSets'][0]['series'].pop('0:0:0:0');data['data']['dataSets'][0]['series']['-1:0:0:0']=series
    with pytest.raises(ValueError):decode(data)

def test_actual_rescale_rejects_unequal_sector_support(tmp_path):
    official=pd.DataFrame([dict(waris_oblast=f'r{i}',official_grp_million_uah=10+i) for i in range(25)])
    model=pd.DataFrame([dict(oblast=f'r{i}',sector=f's{j}',prewar_revenue_index_2021=100,current_revenue_index=90) for i in range(25) for j in range(6)])
    with patch.object(plan,'RESCALE_SCENARIO_TABLE',tmp_path/'scenario.csv'):
        result=plan.build_rescale_scenario(model,official)
        assert len(result)==150 and result.current_use_in_scoring.eq('not_yet_used').all()
        with pytest.raises(ValueError):plan.build_rescale_scenario(model.iloc[:-1],official)
