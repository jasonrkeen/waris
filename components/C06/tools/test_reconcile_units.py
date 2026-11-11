import copy
import pytest
from reconcile_units import YEARS,decode_api,reconcile,keyed,decimal

def fixture():
    l=['GRP','Gross regional product','CODE','Region label','_Z','Not applicable','A','Annual','2004','5','1090','UAH','6','Millions','0','Zero','','','','','']
    blank=l.copy();blank[8]='2005';blank[9]='';blank[20]='Not available.'
    w=dict(Indicator='Gross regional product',Region='Region label',Frequency='Annual',**{'Economic activity type':'Not applicable','Observation notes':'Not available.'})
    w.update({y:('5' if y=='2004' else '') for y in YEARS})
    h=dict(indicator_code='GRP',indicator_name='Gross regional product',region_code='Region label',region_name='Region label',waris_oblast='Canonical',nace_code='_Z',nace_name='Not applicable',freq_code='A',freq_name='Annual',time_period='2004',observation_value='5.0',unit_code='UAH',unit_name='UAH',scaling_code='Millions',scaling_name='Millions',decimals_code='Zero',decimals_name='Zero')
    api={'CODE':dict(region_code='CODE',attributes={'NOTES_TS':None},observations={'2004':dict(value=decimal('5'),flag='',note=''),'2005':dict(value=None,flag='',note='Not available.')})}
    return [l,blank],[w],[h],api,{'Region label':'Canonical'}

def test_absent_is_distinct_from_explicit_null_and_zero():
    evidence,slots,profiles,diff=reconcile(*fixture())
    assert len(evidence)==1 and evidence[0]['value_million_UAH']=='5'
    assert profiles[0]['explicit_unavailable']==1 and profiles[0]['absent_slots']==16
    assert slots[1]['source_state']=='explicit_not_available' and slots[2]['source_state']=='absent_in_long_and_API'

def test_wide_series_note_does_not_erase_numeric_value():
    evidence,slots,profiles,diff=reconcile(*fixture())
    assert evidence[0]['source_observation_note']=='' and evidence[0]['wide_export_series_note_not_per_year']=='Not available.'
    assert len(diff)==1

def test_real_identifier_is_not_the_historical_label():
    evidence,_,_,_=reconcile(*fixture())
    assert evidence[0]['region_code']=='CODE' and evidence[0]['source_region_label']=='Region label'

def test_duplicate_observation_stops():
    f=fixture();f[0].append(f[0][0].copy())
    with pytest.raises(ValueError):reconcile(*f)

def test_value_revision_stops():
    f=fixture();f[3]['CODE']['observations']['2004']['value']=decimal('6')
    with pytest.raises(ValueError):reconcile(*f)

def test_source_note_conflict_stops():
    f=fixture();f[3]['CODE']['observations']['2005']['note']='Different'
    with pytest.raises(ValueError):reconcile(*f)

def test_historical_label_as_code_checked():
    f=fixture();f[2][0]['region_code']='CODE'
    with pytest.raises(ValueError):reconcile(*f)

def test_no_guess_for_absent_observation():
    f=fixture();f[3]['CODE']['observations']['2006']=dict(value=None,flag='',note='Not available.')
    with pytest.raises(ValueError):reconcile(*f)

@pytest.mark.parametrize('value',['NaN','Infinity','-Infinity'])
def test_nonfinite_stops(value):
    with pytest.raises(ValueError):decimal(value)

def test_numeric_zero_is_a_value():
    assert decimal('0')==0 and decimal('') is None

def api_fixture():
    dimensions=[dict(id=key,values=[dict(id=value)]) for key,value in [('INDICATOR','GRP'),('REGION','CODE'),('NACE','_Z'),('FREQ','A')]]
    specs=[dict(id=key,values=[dict(id=value)]) for key,value in [('UNITS_OF_MEASURE','1090'),('SCALE','6'),('DECIMALS_DISPLAYED','0')]]+[dict(id='NOTES_TS')]
    return {'data':{'dataSets':[{'series':{'0:0:0:0':{'attributes':[0,0,0,None],'observations':{'0':['0'],'1':[None,None,{'en':'Not available.'}]}}}}],'structures':[{'dimensions':{'series':dimensions,'observation':[{'id':'TIME_PERIOD','values':[{'value':'2004'},{'value':'2005'}]}]},'attributes':{'series':specs,'observation':[dict(id='OBS_FLAG'),dict(id='NOTES_OBS')]}}]}}

def test_api_zero_null_and_absence_preserved():
    result=decode_api(api_fixture())['observations']
    assert result['2004']['value']==0 and result['2005']['value'] is None and '2006' not in result

def test_api_unit_mismatch_stops():
    payload=api_fixture();payload['data']['structures'][0]['attributes']['series'][0]['values'][0]['id']='USD'
    with pytest.raises(ValueError):decode_api(payload)

def test_api_attribute_alignment_stops():
    payload=api_fixture();payload['data']['dataSets'][0]['series']['0:0:0:0']['attributes'].pop()
    with pytest.raises(ValueError):decode_api(payload)

def test_api_duplicate_time_stops():
    payload=api_fixture();payload['data']['structures'][0]['dimensions']['observation'][0]['values'][1]['value']='2004'
    with pytest.raises(ValueError):decode_api(payload)
