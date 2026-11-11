import json
from unittest.mock import patch
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from src.acled_context import assess_sample,SampleScope
from src.confidence_policy import summarize_confidence
from src import live_data,source_confidence


def fields():
    return pd.DataFrame([dict(field_name=f'f{i}',model_area='example',current_source_type='declared',confidence_level=label,replacement_priority='Low') for i,label in enumerate(['High','Medium-High','Unknown'])])


def events():
    return pd.DataFrame([dict(event_id_cnty='fixture1',event_date='2025-01-01',year=2025,event_type='Battles',country='Ukraine',admin1='Kyiv',fatalities='0'),dict(event_id_cnty='fixture2',event_date='2025-01-02',year=2025,event_type='Battles',country='Ukraine',admin1='Kyiv City',fatalities='')])


def assess(frame):
    return assess_sample(frame,('Kyiv','Kyiv City','Lviv'),{},SampleScope('synthetic_fixture'))


def test_labels_and_unknown_counted_without_numeric_average():
    row=summarize_confidence(fields()).iloc[0]
    counts=json.loads(row.confidence_label_counts)
    assert counts['Medium-High']==counts['High']==counts['Unknown']==1
    assert sum(counts.values())==row.field_count==3
    assert 'avg_confidence_score' not in row.index
    assert not row.empirical_reliability_established and not row.source_rights_established


def test_reordering_fields_does_not_change_categorical_result():
    assert_frame_equal(summarize_confidence(fields()),summarize_confidence(fields().iloc[::-1]))


@pytest.mark.parametrize('column,value',[('confidence_level','Unsupported'),('replacement_priority','Urgent'),('model_area',''),('field_name',None)])
def test_invalid_register_stops_without_default(column,value):
    frame=fields();frame.loc[0,column]=value
    with pytest.raises(ValueError):summarize_confidence(frame)


def test_duplicated_field_identity_never_inflates_counts():
    frame=fields();frame.loc[1,'field_name']='f0'
    with pytest.raises(ValueError):summarize_confidence(frame)


def test_categorical_urgency_is_separate_from_confidence():
    frame=fields();frame.loc[2,'replacement_priority']='High'
    row=summarize_confidence(frame).iloc[0]
    assert row.highest_declared_replacement_priority=='High' and row.unknown_confidence_fields==1


def test_actual_confidence_entry_point_accepts_medium_high(tmp_path):
    with patch.object(source_confidence,'TABLE_DIR',tmp_path),patch.object(source_confidence,'SOURCE_CONFIDENCE_TABLE',tmp_path/'assessment.csv'):
        row=source_confidence.build_source_confidence_assessment(fields()).iloc[0]
    assert json.loads(row.confidence_label_counts)['Medium-High']==1


def test_unobserved_region_is_null_and_reported_zero_is_preserved():
    result=assess(events());rows=result.regions.set_index('oblast')
    assert rows.loc['Kyiv','reported_fatalities_sum']==0
    assert pd.isna(rows.loc['Lviv','sample_event_count']) and pd.isna(rows.loc['Lviv','reported_fatalities_sum'])
    assert rows.loc['Lviv','sample_membership']=='not_observed_in_retained_sample'
    assert not result.audit['population_coverage_verified'] and not result.audit['used_in_scoring']


def test_missing_fatalities_do_not_become_zero_or_complete_group_total():
    frame=events();frame.loc[1,'admin1']='Kyiv'
    row=assess(frame).regions.set_index('oblast').loc['Kyiv']
    assert row.sample_event_count==2 and row.missing_fatality_rows==1
    assert pd.isna(row.reported_fatalities_sum) and row.known_reported_fatalities_partial_sum==0


@pytest.mark.parametrize('value',['bad','-1','inf','NaN'])
def test_invalid_nonmissing_fatalities_never_coerced_to_zero(value):
    frame=events();frame.loc[0,'fatalities']=value
    with pytest.raises(ValueError):assess(frame)


def test_duplicate_id_and_missing_id_stop_without_deduplication():
    frame=events();frame.loc[1,'event_id_cnty']=frame.loc[0,'event_id_cnty']
    with pytest.raises(ValueError):assess(frame)
    frame.loc[1,'event_id_cnty']=''
    with pytest.raises(ValueError):assess(frame)


@pytest.mark.parametrize('column,value',[('country',None),('country','Other'),('event_type','Unrecognised'),('event_date','2025-02-31'),('year',2024)])
def test_invalid_country_type_date_or_year_cannot_enter_context(column,value):
    frame=events();frame.loc[0,column]=value
    with pytest.raises(ValueError):assess(frame)


def test_exact_aliases_preserve_city_and_do_not_match_substrings():
    frame=events();frame.loc[0,'admin1']='text containing Kyiv'
    result=assess(frame)
    assert result.audit['unmapped_or_outside_universe_rows']==1
    rows=result.regions.set_index('oblast')
    assert pd.isna(rows.loc['Kyiv','sample_event_count']) and rows.loc['Kyiv City','sample_event_count']==1


def test_input_and_source_zeros_not_rewritten():
    frame=events();before=frame.copy(deep=True);assess(frame)
    assert_frame_equal(frame,before)


def test_old_event_dates_are_not_promoted_to_current_acquisition():
    frame=events();frame['year']=2018;frame['event_date']=['2018-01-01','2018-01-02']
    result=assess(frame)
    assert result.audit['event_date_max']=='2018-01-02'
    assert not result.audit['historical_acquisition_time_verified']
    assert not result.audit['population_coverage_verified']


def test_empty_sample_does_not_invent_zero_event_regions():
    result=assess(events().iloc[:0])
    assert result.regions.sample_event_count.isna().all() and result.audit['modeled_regions_without_sample_records']==3


def test_retained_provider_scope_requires_fingerprint():
    with pytest.raises(ValueError):assess_sample(events(),('Kyiv',),{},SampleScope('retained_provider_sample'))


def test_legacy_acled_scoring_proxy_is_retired_even_if_called_directly():
    with pytest.raises(RuntimeError,match='retired'):live_data.build_conflict_proxy(events())


def test_alias_collision_is_rejected():
    with pytest.raises(ValueError):assess_sample(events(),('Kyiv','Kyiv City'),{'kyiv':'Kyiv City'},SampleScope('synthetic_fixture'))
