import copy
import pytest
from reconcile_candidates import decode,period_label,path_role,constraint_projection

def fixture():
    dims=[{'id':k,'values':[{'id':v}]} for k,v in [('INDICATOR','GRP'),('REGION','CODE'),('NACE','_Z'),('FREQ','A')]]
    attrs=[{'id':k,'values':[{'id':v}]} for k,v in [('UNITS_OF_MEASURE','1090'),('SCALE','6'),('DECIMALS_DISPLAYED','0')]]
    return {'data':{'dataSets':[{'series':{'0:0:0:0':{'attributes':[0,0,0],'observations':{'0':['5'],'1':['7']}}}}],'structures':[{'dimensions':{'series':dims,'observation':[{'id':'TIME_PERIOD','values':[{'value':'2004'},{'value':'2006'}]}]},'attributes':{'series':attrs,'dataSet':[],'observation':[]}}]}}

@pytest.mark.parametrize('obj',[{'value':'2004'},{'id':'2004'},{'value':'2004','id':'2004'}])
def test_explicit_period_supported(obj):assert period_label(obj)=='2004'

@pytest.mark.parametrize('obj',[{}, {'name':'2004'}, {'value':'2004','id':'2005'}, {'value':'2004-01-01'}])
def test_ambiguous_or_nonannual_label_stops(obj):
    with pytest.raises(ValueError):period_label(obj)

def test_noncontiguous_source_years_preserved():
    records=decode(fixture());assert [r['source_period_label'] for r in records]==['2004','2006']
    assert all(r['period_kind']=='annual_label_not_observation_day' for r in records)

def test_no_fallback_from_missing_source_labels():
    d=fixture();d['data']['structures'][0]['dimensions']['observation'][0]['values']=[]
    with pytest.raises(ValueError):decode(d)

def test_empty_response_is_not_a_zero_observation():
    d=fixture();d['data']['dataSets'][0].pop('series')
    assert decode(d)==[]

def test_null_and_zero_remain_distinct():
    d=fixture();d['data']['dataSets'][0]['series']['0:0:0:0']['observations']={'0':['0'],'1':[None]}
    a,b=decode(d);assert a['value_million_UAH']=='0' and a['source_state']=='numeric_observation'
    assert b['value_million_UAH']=='' and b['source_state']=='explicit_unavailable'

def test_wrong_unit_stops():
    d=fixture();d['data']['structures'][0]['attributes']['series'][0]['values'][0]['id']='USD'
    with pytest.raises(ValueError):decode(d)

def test_duplicate_time_labels_stop():
    d=fixture();d['data']['structures'][0]['dimensions']['observation'][0]['values'][1]['value']='2004'
    with pytest.raises(ValueError):decode(d)

def test_reordered_axes_stop():
    d=fixture();d['data']['structures'][0]['dimensions']['series'].reverse()
    with pytest.raises(ValueError):decode(d)

def test_nonfinite_value_stops():
    d=fixture();d['data']['dataSets'][0]['series']['0:0:0:0']['observations']['0']=['NaN']
    with pytest.raises(ValueError):decode(d)

def test_unindexed_period_stops():
    d=fixture();d['data']['dataSets'][0]['series']['0:0:0:0']['observations']['2']=['9']
    with pytest.raises(ValueError):decode(d)

@pytest.mark.parametrize('path,role',[
('data.structures[0].dimensions.series[0].values[0].id','structure_metadata_not_observation'),
('data.dataSets[0].attributes[0]','dataset_attribute_value_not_observation'),
('data.dataSets[0].structure','dataset_control_metadata_not_observation'),
('data.dataSets[0].series[0].observations[0]','observation_payload_requires_typed_decoding')])
def test_path_semantics(path,role):assert path_role(path)==role

def test_false_include_is_never_promoted_to_positive_selector():
    d={'data':{'dataConstraints':[{'cubeRegions':[{'include':True,'components':[{'id':'INDICATOR','include':False,'removePrefix':False,'values':[{'value':'GRP'}]}]}],'annotations':[{'id':'time_period_end','title':'2022-01-01'}]}]}}
    records=constraint_projection(d)
    assert records[0]['component_include_as_supplied']=='false' and records[0]['cube_include_as_supplied']=='true'
    assert all(r['positive_query_selector_inferred'] is False and r['observation_availability_inferred'] is False for r in records)
