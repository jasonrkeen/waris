from copy import deepcopy
import pytest
from lot_study import units,summarize,freeze,verify_freeze
from lot_study import analyze
from capture_prozorro_sample import capture,CapturePlan,save,BASE_URL
import json
import requests
from unittest.mock import patch

def row(**kwargs):
    return {'procurementMethodType':'aboveThreshold','status':'complete','lots':[{'id':'L1','status':'complete'},{'id':'L2','status':'cancelled'}],
      'bids':[{'id':'B1','status':'active','lotValues':[{'relatedLot':'L1'},{'relatedLot':'L2','status':'deleted'}]},
              {'id':'B2','status':'invalid','lotValues':[{'relatedLot':'L1'}]}],**kwargs}

def test_linkage_inactive_and_mixed_outcomes():
    a,b=units(row(),0)
    assert (a['visible_objects'],a['active_objects'],a['inactive_objects'])==(2,1,1)
    assert (b['visible_objects'],b['active_objects'])==(1,0)
    assert a['eligible'] and not b['eligible'] and a['mixed_outcome_parent']

@pytest.mark.parametrize('bids',[None,'bad',[{}],[{'id':'B','status':'active'},{'id':'B','status':'active'}],
  [{'id':'B','status':'active','lotValues':[]}],[{'id':'B','status':'active','lotValues':[{'relatedLot':'MISSING'}]}],
  [{'id':'B','status':'active','lotValues':[{'relatedLot':'L1'},{'relatedLot':'L1'}]}],
  [{'id':'B','lotValues':[{'relatedLot':'L1'}]}],[{'id':'B','status':'future','lotValues':[{'relatedLot':'L1'}]}],
  [{'id':'B','status':'active','lotValues':[{'relatedLot':'L1','status':'future'}]}]])
def test_ambiguous_links_fail_closed(bids):
    assert all(x['active_objects'] is None and x['visible_objects'] is None for x in units(row(bids=bids),0))

def test_empty_bids_observed_zero():
    assert all(x['active_objects']==0 for x in units(row(bids=[]),0))

@pytest.mark.parametrize('lots',[None,'bad',[{}],[{'id':'L','status':'complete'},{'id':'L','status':'complete'}]])
def test_invalid_lot_structure(lots):
    result=units(row(lots=lots),0)
    assert len(result)==1 and result[0]['unit_type']=='invalid_lots' and not result[0]['eligible']

@pytest.mark.parametrize('change',[{'status':'active.awarded'},{'status':'unsuccessful'},{'procurementMethodType':'reporting'},
 {'procurementMethodType':'future'},{'mode':'test'},{'config':{'restricted':True}},{'config':None}])
def test_primary_eligibility(change):
    assert all(not x['eligible'] for x in units(row(**change),0))

def test_absent_explicit_lots_not_auto_allocated():
    r=row(lots=[])
    assert units(r,0)[0]['active_objects'] is None
    r['bids']=[{'id':'B','status':'active'}]
    assert units(r,0)[0]['active_objects']==1

def test_one_explicit_lot_still_needs_links():
    r=row(lots=[{'id':'L1','status':'complete'}],bids=[{'id':'B','status':'active'}])
    assert units(r,0)[0]['active_objects'] is None

def test_awards_never_substitute():
    r=row();r.pop('bids');r['awards']=[{'suppliers':[{'name':'Synthetic'}]}]
    assert all(x['active_objects'] is None for x in units(r,0))

def test_same_bid_on_two_lots_not_two_clusters():
    r=row(lots=[{'id':'L1','status':'complete'},{'id':'L2','status':'complete'}],bids=[{'id':'B','status':'active','lotValues':[{'relatedLot':'L1'},{'relatedLot':'L2'}]}])
    result=summarize([r])['strata'][0]
    assert result['units']==2 and result['eligible_tender_clusters']==1 and result['single_active_object_rate'] is None

def test_five_clusters_supported_without_geographic_inference():
    result=summarize([row() for _ in range(5)])
    complete=[x for x in result['strata'] if x['unit_status']=='complete'][0]
    assert complete['single_active_object_rate']==1 and complete['single_visible_object_rate']==0
    assert not result['population_inference'] and not result['production_score_change']

def test_missingness_withholds_rate():
    result=summarize([row() for _ in range(5)]+[row(bids=None)])
    complete=[x for x in result['strata'] if x['unit_status']=='complete'][0]
    assert complete['eligible_coverage']==5/6 and complete['single_active_object_rate'] is None

def test_exact_procedures_and_grains_separate():
    result=summarize([row(),row(procurementMethodType='priceQuotation'),row(lots=[],bids=[])])
    assert len(result['strata'])==5

def test_unknown_lot_state_not_eligible():
    assert not units(row(lots=[{'id':'L1','status':'future'}],bids=[]),0)[0]['eligible']

def test_cannot_overwrite_freeze(tmp_path):
    freeze(tmp_path/'f');verify_freeze(tmp_path/'f')
    with pytest.raises(FileExistsError):freeze(tmp_path/'f')

def test_tampered_plan_rejected(tmp_path):
    root=tmp_path/'f';freeze(root);(root/'study_plan.json').write_text('{}')
    with pytest.raises(ValueError):verify_freeze(root)

def test_cancelled_lot_with_complete_parent_not_primary():
    assert not units(row(),0)[1]['eligible']

def test_explicit_null_lot_value_status_is_unknown():
    r=row(bids=[{'id':'B','status':'active','lotValues':[{'relatedLot':'L1','status':None}]}])
    assert units(r,0)[0]['active_objects'] is None

@pytest.fixture
def captured(tmp_path):
    root=tmp_path/'f';freeze(root)
    class Session:
        def get(self,url,params=None,**kwargs):
            if url==BASE_URL:payload={'data':[{'id':f'{i:032x}','status':'complete','procurementMethodType':'aboveThreshold','dateModified':'synthetic'} for i in range(1,101)]}
            else:payload={'data':{'id':url.rsplit('/',1)[1],**row(),'dateModified':'synthetic'}}
            class Response:pass
            r=Response();r.content=json.dumps(payload).encode();r.status_code=200;r.headers={'Content-Type':'application/json'}
            r.url=requests.Request('GET',url,params=params).prepare().url
            return r
    with patch('capture_prozorro_sample.time.sleep'):
        capture(root/'private_capture',CapturePlan(100,100),Session())
    return root

def test_complete_capture_analysis(captured,tmp_path):
    result=analyze(captured,tmp_path/'out')
    assert result['captured_tenders']==100 and result['eligible_tender_clusters']==100
    assert result['feed_detail_drift']=={}

@pytest.mark.parametrize('change',['duplicate_receipt','partial','body_changed','wrong_identity','unexpected_file','bad_code_inventory','old_timestamp','spec_changed'])
def test_capture_provenance_rejections(captured,tmp_path,change):
    raw=captured/'private_capture';manifest=raw/'capture_manifest.json';r=json.loads(manifest.read_text())
    if change=='duplicate_receipt':r['responses'][1]=r['responses'][2]
    elif change=='partial':r['status']='failed_partial'
    elif change=='body_changed':(raw/'detail_001.json').write_text('{}')
    elif change=='wrong_identity':r['selected_ordered_ids_sha256']='invalid'
    elif change=='unexpected_file':(raw/'extra.json').write_text('{}')
    elif change=='old_timestamp':r['created_at_utc']='2000-01-01T00:00:00+00:00'
    elif change=='spec_changed':(raw/'capture_specification.json').write_text('{}')
    else:
        f=json.loads((captured/'freeze.json').read_text());f['code']={};save(captured/'freeze.json',f)
    save(manifest,r)
    with pytest.raises((ValueError,KeyError)):analyze(captured,tmp_path/'out')
    assert not (tmp_path/'out').exists()

def test_capture_short_page_retains_failed_attempt(tmp_path):
    class Session:
        def get(self,url,params=None,**kwargs):
            class Response:
                content=b'{"data": []}';status_code=200;headers={}
            r=Response();r.url=requests.Request('GET',url,params=params).prepare().url;return r
    root=tmp_path/'raw'
    with pytest.raises(ValueError):capture(root,CapturePlan(100,100),Session())
    r=json.loads((root/'capture_manifest.json').read_text())
    assert r['status']=='failed_partial' and len(r['responses'])==1 and (root/'feed.json').exists()
