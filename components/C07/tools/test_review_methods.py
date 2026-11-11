from pathlib import Path
import pytest
from review_methods import gap_band,ratio_band,gap_projection,retained_path,preview_matches

@pytest.mark.parametrize('value,expected',[(0,'minimal_gap'),(9.999,'minimal_gap'),(10,'small_gap'),(25,'moderate_gap'),(50,'large_gap'),(75,'very_large_gap')])
def test_legacy_gap_boundaries(value,expected):assert gap_band(value)==expected

@pytest.mark.parametrize('value,expected',[(2,'official_share_much_higher'),(1.25,'official_share_higher'),(.5,'official_share_much_lower'),(.8,'official_share_lower'),(1,'roughly_aligned')])
def test_legacy_ratio_boundaries(value,expected):assert ratio_band(value)==expected

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-1])
def test_invalid_gaps_stop(value):
    with pytest.raises(ValueError):gap_band(value)

def reviewed():
    return [dict(waris_oblast=f'Region{i}',official_grp_million_uah='10',official_grp_share_of_waris_total='.04',synthetic_prewar_share_of_total='.04',official_grp_index_0_100=str(i),synthetic_prewar_index_0_100=str(i),official_vs_synthetic_index_gap='0',official_to_synthetic_share_ratio='1') for i in range(25)]

def test_zero_gap_does_not_infer_economic_alignment():
    result=gap_projection(reviewed())
    assert all(r['used_in_scoring'] is False and r['sector_allocation_approved'] is False and 'no measured economic error' in r['interpretation'] for r in result)

def test_inconsistent_gap_stops():
    data=reviewed();data[0]['official_vs_synthetic_index_gap']='1'
    with pytest.raises(ValueError):gap_projection(data)

def test_duplicate_region_stops():
    data=reviewed();data[0]['waris_oblast']=data[1]['waris_oblast']
    with pytest.raises(ValueError):gap_projection(data)

def test_share_denominator_stops():
    data=reviewed()
    for r in data:r['official_grp_share_of_waris_total']='.08';r['official_to_synthetic_share_ratio']='2'
    with pytest.raises(ValueError):gap_projection(data)

def test_path_traversal_stops(tmp_path):
    with pytest.raises(ValueError):retained_path(tmp_path,'<project-root>/../escape.json')

def test_explicit_locator_resolves(tmp_path):
    assert retained_path(tmp_path,r'<project-root>\\data\\raw\\x.json')==tmp_path/'data/raw/x.json'

def test_empty_and_shared_prefix_are_not_identity_proof():
    assert not preview_matches('','anything')
    prefix='{"common_metadata":"'+'A'*50
    assert preview_matches(prefix,prefix+'region1"}') and preview_matches(prefix,prefix+'region2"}')

def test_minmax_roundoff_is_preserved_without_clipping():
    data=reviewed();data[0].update(official_grp_index_0_100='100',synthetic_prewar_index_0_100='100.00000000000001',official_vs_synthetic_index_gap=str(100-100.00000000000001))
    row=next(r for r in gap_projection(data) if r['waris_oblast']=='Region0')
    assert row['synthetic_prewar_index_0_100']==100.00000000000001

def test_substantively_out_of_range_index_stops():
    data=reviewed();data[0]['synthetic_prewar_index_0_100']='101';data[0]['official_vs_synthetic_index_gap']='-101'
    with pytest.raises(ValueError):gap_projection(data)
