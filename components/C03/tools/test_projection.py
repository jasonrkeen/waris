from copy import deepcopy
from pathlib import Path
import pytest
from public_projection import project,export,REVIEWED_PLAN_SHA256

def result():
    domains={'aboveThreshold':{'N':28,'n':28,'cluster_weight':1.,'inclusion_probability':1.},'priceQuotation':{'N':43,'n':40,'cluster_weight':1.075,'inclusion_probability':40/43}}
    estimates=[]
    for m,grain,den,clusters,num in [('aboveThreshold','explicit_lot',32,28,18),('priceQuotation','no_explicit_lots',40,40,21)]:
        w=domains[m]['cluster_weight'];estimates.append({'sampling_domain':m,'detail_procedure':m,'unit_type':grain,
          'eligible_units':den,'eligible_sampled_clusters':clusters,'eligible_observed_units':den,
          'support':'supported_within_recorded_frame_only','single_active_ratio':num/den,'single_visible_ratio':num/den,
          'single_active_HT_total':num*w,'eligible_unit_HT_total':den*w})
    return {'domains':domains,'estimates':estimates,'plan_sha256':REVIEWED_PLAN_SHA256,'national_or_period_inference':False,'production_score_change':False}

def test_observed_and_estimated_not_conflated():
    p=project(result());assert p.observed[1]['observed_exactly_one_active_object_units']==21
    assert p.weighted[1]['HT_exactly_one_active_object_total']=='22.575'
    assert p.weighted[1]['total_status']=='estimated_not_observed_unsampled_records'
    assert p.observed[0]['active_object_share']=='0.5625'

@pytest.mark.parametrize('issue',['national','scoring','plan','sparse','missing','weight','ratio','method','duplicate','total'])
def test_fail_closed(issue):
    r=result();e=r['estimates'][0]
    if issue=='national':r['national_or_period_inference']=True
    elif issue=='scoring':r['production_score_change']=True
    elif issue=='plan':r['plan_sha256']='changed'
    elif issue=='sparse':e['eligible_sampled_clusters']=4
    elif issue=='missing':e['eligible_observed_units']-=1
    elif issue=='weight':r['domains']['aboveThreshold']['cluster_weight']=2
    elif issue=='ratio':e['single_active_ratio']=.123
    elif issue=='method':e['detail_procedure']='reporting'
    elif issue=='duplicate':r['estimates'][1]=e
    else:e['single_active_HT_total']=999
    with pytest.raises(ValueError):project(r)

def test_input_hash_gate(tmp_path):
    p=tmp_path/'input.json';p.write_text('{}')
    with pytest.raises(ValueError,match='input bytes'):export(p,tmp_path/'out')
    assert not (tmp_path/'out').exists()

def test_private_keys_cannot_propagate():
    r=result();r['id']='synthetic-private';r['estimates'][0]['buyer_name']='synthetic-private'
    p=project(r)
    assert 'synthetic-private' not in str(p)
