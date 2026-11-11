import copy
import pytest
from clearance import benchmark, typed_components, verify_reference

def inputs():
    official=[dict(region_code=f'R{i}',geography_label_from_retained_export=f'N{i}',period='2021',unit_code='1090',scale_code='6',indicator_code='GRP',nace_code='_Z',frequency='A',value_million_UAH=str(i+1)) for i in range(25)]
    synthetic=[dict(oblast=f'N{i}',sector=f'S{j}',prewar_revenue_index_2021=(i+1)*10) for i in range(25) for j in range(6)]
    return official,synthetic,{f'N{i}':f'N{i}' for i in range(25)}

def test_known_proportional_benchmark():
    out=benchmark(*inputs())
    assert len(out)==25
    assert sum(r['official_grp_share_of_waris_total'] for r in out)==pytest.approx(1)
    assert all(r['official_to_synthetic_share_ratio']==pytest.approx(1) and r['official_vs_synthetic_index_gap']==pytest.approx(0) for r in out)

@pytest.mark.parametrize('field,value',[('unit_code','USD'),('scale_code','3'),('period','2022'),('nace_code','_T'),('value_million_UAH','NaN')])
def test_incompatible_observation_rejected(field,value):
    a,b,c=inputs();a[0][field]=value
    with pytest.raises(ValueError):benchmark(a,b,c)

def test_duplicate_region_rejected():
    a,b,c=inputs();a[1]['region_code']=a[0]['region_code']
    with pytest.raises(ValueError):benchmark(a,b,c)

def test_missing_sector_rejected():
    a,b,c=inputs()
    with pytest.raises(ValueError):benchmark(a,b[:-1],c)

def test_unmapped_region_rejected():
    a,b,c=inputs();b[0]['oblast']='unexpected'
    with pytest.raises(ValueError):benchmark(a,b,c)

def test_live_score_ignored():
    a,b,c=inputs();expected=benchmark(a,b,c)
    for r in b:r.update(waris_aml_review_score=999,conflict_intensity_proxy='RESTRICTED_UNUSED',current_revenue_index=9999)
    assert benchmark(a,b,c)==expected

def test_version_cannot_substitute():
    row=dict(id='X',agencyID='SSSU',version='1',name='Title')
    with pytest.raises(ValueError):verify_reference(row,[dict(row,version='2')])

def dsd():
    return dict(id='DSD_REGIONAL_ACCOUNTS',agencyID='SSSU',version='6.0.0',name='Test',dataStructureComponents={'dimensionList':{'dimensions':[dict(id=n,position=i) for i,n in enumerate(['INDICATOR','REGION','NACE','FREQ'])],'timeDimensions':[dict(id='TIME_PERIOD',position=4)]},'attributeList':{'attributes':[dict(id=f'A{i}') for i in range(15)]},'measureList':{'measures':[dict(id='OBS_VALUE')]}})

def test_only_axes_are_key_dimensions():
    out=typed_components(dsd())
    assert len(out)==21 and sum(r['key_axis'] for r in out)==5
    assert not any(r['key_axis'] for r in out if r['role'] in ('attribute','measure'))

def test_changed_axis_order_stops():
    item=dsd();item['dataStructureComponents']['dimensionList']['dimensions'][0]['position']=9
    with pytest.raises(ValueError):typed_components(item)
