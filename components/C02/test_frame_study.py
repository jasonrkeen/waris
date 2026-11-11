from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import json,shutil
import pytest,requests
from frame_study import build_frame,select,estimates,safe_cursor,freeze,verify_freeze,acquire,analyze,BASE_URL
from capture_prozorro_sample import save

def meta(i,method='aboveThreshold',status='complete'):
    return {'id':f'{i:032x}','procurementMethodType':method,'status':status,'dateModified':'synthetic','public_modified':1000-i}

def detail(item):
    return {**item,'lots':[{'id':'L','status':'complete'}],'bids':[{'id':'B','status':'active','lotValues':[{'relatedLot':'L'}]}]}

def test_frame_duplicates_first_observation():
    a=meta(1);b=meta(1,status='active.tendering')
    frame,diagnostic=build_frame([[a],[b,meta(2)]])
    assert frame[0]['status']=='complete' and len(frame)==2
    assert diagnostic=={'cross_page_duplicate_occurrences':1,'cross_page_conflicting_occurrences':1}

@pytest.mark.parametrize('data',[[meta(1),meta(1)],[{'id':'invalid'}],None])
def test_frame_bad_identity_or_schema(data):
    with pytest.raises(ValueError):build_frame([data])

def test_sampling_census_and_probability():
    frame=[meta(i) for i in range(1,101)]+[meta(101,'priceQuotation')]
    selection=select(frame,'fixed synthetic seed')
    assert selection==select(list(reversed(frame)),'fixed synthetic seed')
    assert selection['aboveThreshold']['n']==40 and selection['aboveThreshold']['inclusion_probability']==.4
    assert selection['aboveThreshold']['cluster_weight']==2.5
    assert selection['priceQuotation']['n']==1 and selection['priceQuotation']['cluster_weight']==1
    assert len(set(selection['aboveThreshold']['selected_ids']))==40

def test_only_predeclared_domains():
    assert select([meta(1,'reporting'),meta(2,status='active.awarded')],'s')['aboveThreshold']['n']==0

@pytest.mark.parametrize('cursor,seen',[('',set()),('x',{'x'}),(None,set()),('bad\n',set())])
def test_cursor_rejected(cursor,seen):
    with pytest.raises(ValueError):safe_cursor(cursor,seen)

def test_HT_totals_and_drift_not_replaced():
    frame=[meta(i) for i in range(1,101)];selection=select(frame,'s')
    details=[detail(next(x for x in frame if x['id']==i)) for i in selection['aboveThreshold']['selected_ids']]
    details[0]['status']='active.awarded'
    result=estimates(frame,selection,details);e=result['estimates'][0]
    assert e['eligible_sampled_clusters']==39 and e['eligible_unit_HT_total']==97.5
    assert e['single_active_HT_total']==97.5 and e['single_active_ratio']==1
    assert result['feed_detail_drift']=={'status_changed':1}

@pytest.fixture(scope='module')
def captured(tmp_path_factory):
    root=tmp_path_factory.mktemp('frame')/'f';freeze(root)
    class Session:
        def get(self,url,params=None,**kwargs):
            if url==BASE_URL:
                offset=(params or {}).get('offset')
                if offset is None:payload={'data':[meta(i) for i in range(1,101)],'next_page':{'offset':'c1'}}
                elif offset=='c1':payload={'data':[meta(i,'priceQuotation') for i in range(101,201)],'next_page':{'offset':'c2'}}
                else:payload={'data':[]}
            else:
                number=int(url.rsplit('/',1)[1],16);payload={'data':detail(meta(number,'aboveThreshold' if number<=100 else 'priceQuotation'))}
            class Response:pass
            r=Response();r.content=json.dumps(payload).encode();r.status_code=200;r.headers={};r.url=requests.Request('GET',url,params=params).prepare().url;return r
    with patch('frame_study.time.sleep'):r=acquire(root,Session())
    assert r['successful_details']==80 and r['frame_pages']==3
    return root

def test_capture_cursor_selection_and_analysis(captured,tmp_path):
    result=analyze(captured,tmp_path/'out')
    assert result['frame_unique_tenders']==200 and result['selected_details']==80
    assert all(x['eligible_unit_HT_total']==100 for x in result['estimates'])
    assert not result['national_or_period_inference']

@pytest.mark.parametrize('mode',['body','cursor','selection','early_details','extra_file','partial','plan','inventory'])
def test_integrity_rejects(captured,tmp_path,mode):
    root=tmp_path/'copy';shutil.copytree(captured,root);raw=root/'private_capture';manifest=raw/'capture_manifest.json';r=json.loads(manifest.read_text())
    if mode=='body':(raw/'detail_001.json').write_text('{}')
    elif mode=='cursor':r['responses'][1]['requested_url']='https://invalid.example/';r['responses'][1]['final_url']='https://invalid.example/'
    elif mode=='selection':(raw/'selection.json').write_text('{}')
    elif mode=='early_details':r['responses'][3]['started_at_utc']='2000-01-01T00:00:00+00:00'
    elif mode=='extra_file':(raw/'extra.json').write_text('{}')
    elif mode=='partial':r['status']='failed_partial'
    elif mode=='plan':(root/'study_plan.json').write_text('{}')
    else:r['responses'][0]=r['responses'][1]
    save(manifest,r)
    with pytest.raises((ValueError,KeyError)):analyze(root,tmp_path/'out')
    assert not (tmp_path/'out').exists()

def test_immutable_freeze(captured):
    verify_freeze(captured)
    with pytest.raises(FileExistsError):freeze(captured)
