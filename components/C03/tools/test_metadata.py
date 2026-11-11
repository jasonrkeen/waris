import pytest
from reconcile_metadata import reconcile

def fixtures():
    row={'codelist_id':'CL_FREQ','dimension_id':'FREQ','codelist_version':'2.0.2','code_id':'A','code_name':'Annual','code_description':'Annual data'}
    payload={'id':'CL_FREQ','agencyID':'SDMX','version':'2.0.2','isPartial':False,'codes':[{'id':'A','name':'Annual','description':'Annual data'}]}
    return row,{'CL_FREQ':payload}

def test_exact_metadata_identity():
    r,p=fixtures();assert reconcile([r],p)[0]['metadata_name_description_match'] is True

@pytest.mark.parametrize('field,value',[('agencyID','SSSU'),('version','changed'),('isPartial',True)])
def test_wrong_metadata_identity_fails(field,value):
    r,p=fixtures();p['CL_FREQ'][field]=value
    with pytest.raises(ValueError):reconcile([r],p)

def test_wrong_code_name_fails():
    r,p=fixtures();p['CL_FREQ']['codes'][0]['name']='Quarterly'
    with pytest.raises(ValueError):reconcile([r],p)

def test_proposed_period_not_observation():
    r={'codelist_id':'','dimension_id':'TIME_PERIOD','code_id':'2022'}
    assert 'not_available_observation' in reconcile([r],{})[0]['verification']
