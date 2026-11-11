import pandas as pd
import pytest
from src import prozorro_procurement_features as p, official_baseline_merge_review as review, report_generator


@pytest.mark.parametrize('value,expected',[(None,None),([],0),([{}],1),([None],None)])
def test_bid_visibility_does_not_convert_missing_to_zero(value,expected):
    assert p._extract_bids_count({'bids':value})==expected


@pytest.mark.parametrize('value,expected',[(None,None),([],0),([{}],None),([{'suppliers':[]}],None),([{'suppliers':[{'name':'Synthetic supplier'}]}],1)])
def test_incomplete_award_suppliers_are_unknown(value,expected):
    assert p._extract_award_supplier_count({'awards':value})==expected


@pytest.mark.parametrize('bids,suppliers,expected',[(None,None,None),(1,None,1),(None,1,1),(2,None,None),(None,2,None),(0,0,0),(2,1,1),(2,2,0)])
def test_combined_proxy_uses_three_valued_observations(bids,suppliers,expected):
    assert p._combined_visible_proxy(bids,suppliers)==expected


def features():
    rows=[]
    for region,n,bids,suppliers in [('Lviv',6,None,None),('Odesa',4,1,1),('Poltava',5,2,1)]:
        for i in range(n):
            rows.append({'tender_id':f'synthetic-{region}-{i}','oblast':region,'sector':'Construction and reconstruction',
                'value_amount':10,'buyer_name':'Synthetic Buyer','procurement_method_type':'synthetic',
                'bids_count':bids,'supplier_count':suppliers,'single_bid_or_supplier_proxy':p._combined_visible_proxy(bids,suppliers),
                'single_visible_bid_flag':None if bids is None else int(bids==1),
                'single_visible_award_supplier_flag':None if suppliers is None else int(suppliers==1),'reconstruction_emergency_flag':0})
    return pd.DataFrame(rows)


def configure(tmp_path,monkeypatch):
    monkeypatch.setattr(p,'TABLE_DIR',tmp_path)
    for field in ['OBLAST_FEATURE_TABLE','OBLAST_SECTOR_FEATURE_TABLE','SCORING_CANDIDATE_TABLE','FEATURE_SUMMARY_TABLE']:
        monkeypatch.setattr(p,field,tmp_path/(field+'.csv'))


@pytest.mark.parametrize('grain',['oblast','sector'])
def test_unknown_rates_denominators_and_sparse_candidate_gate(tmp_path,monkeypatch,grain):
    configure(tmp_path,monkeypatch)
    frame=p.build_oblast_features(features()) if grain=='oblast' else p.build_oblast_sector_features(features())
    rows=frame.set_index('oblast');unknown=rows.loc['Lviv'];small=rows.loc['Odesa'];observed=rows.loc['Poltava']
    assert unknown.bids_observed_tender_count==0 and unknown.bids_unavailable_tender_count==6
    assert pd.isna(unknown.single_bid_or_supplier_proxy_rate) and pd.isna(unknown.single_visible_bid_rate)
    assert pd.isna(unknown.procurement_review_priority_candidate)
    assert small.unique_tender_count==4 and pd.isna(small.procurement_review_priority_candidate)
    assert small.candidate_support_status=='sparse_group_candidate_withheld'
    assert observed.bids_observed_tender_count==5 and observed.single_visible_bid_rate==0
    assert pd.notna(observed.procurement_review_priority_candidate)
    assert frame.publication_status.eq('held_individual_release_review_required').all()
    assert not frame.used_in_waris_scoring.any() and not frame.used_in_monte_carlo.any()


def test_duplicate_feature_identity_fails_instead_of_inflating_support(tmp_path,monkeypatch):
    configure(tmp_path,monkeypatch);data=features();data.loc[1,'tender_id']=data.loc[0,'tender_id']
    with pytest.raises(ValueError,match='identity'):p.build_oblast_features(data)


def test_combined_observed_denominator_is_not_all_tenders(tmp_path,monkeypatch):
    configure(tmp_path,monkeypatch);data=features().iloc[:6].copy()
    data.loc[0,['bids_count','single_visible_bid_flag','single_bid_or_supplier_proxy']]=[1,1,1]
    frame=p.build_oblast_features(data).iloc[0]
    assert frame.combined_proxy_observed_tender_count==1 and frame.combined_proxy_unavailable_tender_count==5
    assert frame.single_bid_or_supplier_proxy_rate==1 and frame.bids_observed_tender_count==1
    assert pd.isna(frame.procurement_review_priority_candidate)


def test_missing_candidate_is_not_presented_as_low_context(tmp_path,monkeypatch):
    source=tmp_path/'bridge.csv';target=tmp_path/'review.csv'
    pd.DataFrame([{'waris_oblast':'Lviv','official_grp_million_uah':100,'official_vs_synthetic_index_gap':0,
        'procurement_review_priority_candidate':float('nan'),'candidate_support_status':'partial_observations_candidate_withheld'}]).to_csv(source,index=False)
    monkeypatch.setattr(review,'TABLE_DIR',tmp_path);monkeypatch.setattr(review,'OFFICIAL_BASELINE_PROZORRO_CONTEXT_BRIDGE_TABLE',source)
    monkeypatch.setattr(review,'OFFICIAL_BASELINE_PROZORRO_CONTEXT_REVIEW_TABLE',target)
    row=review.build_prozorro_context_review().iloc[0]
    assert row.procurement_candidate_band=='not_available' and 'unavailable' in row.recommended_action.lower()
    assert 'low-priority' not in row.recommended_action.lower()


def test_pdf_numeric_missingness_is_distinct_from_observed_zero():
    table=report_generator._table_from_df(pd.DataFrame({'candidate':[float('nan'),0.0]}),['candidate'])
    unavailable=table._cellvalues[1][0].getPlainText().lower()
    zero=table._cellvalues[2][0].getPlainText()
    assert 'not' in unavailable and 'available' in unavailable and zero=='0.00'


def test_dashboard_preserves_procurement_missing_values():
    import ast
    from pathlib import Path
    source=(Path(__file__).parents[1]/'app.py').read_text(encoding='utf8')
    tree=ast.parse(source);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='coerce_numeric')
    namespace={'pd':pd};exec(compile(ast.Module(body=[function],type_ignores=[]),'dashboard_helper','exec'),namespace)
    original=pd.DataFrame({'candidate':[None,0]})
    shown=namespace['coerce_numeric'](original,['candidate'],preserve_missing=True)
    assert pd.isna(shown.candidate.iloc[0]) and shown.candidate.iloc[1]==0
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='coerce_numeric' and n.args and isinstance(n.args[0],ast.Name) and 'prozorro' in n.args[0].id]
    assert len(calls)==4 and all(any(k.arg=='preserve_missing' and isinstance(k.value,ast.Constant) and k.value.value is True for k in n.keywords) for n in calls)


def test_direct_candidate_projection_cannot_restore_legacy_missingness_blind_priority(tmp_path,monkeypatch):
    configure(tmp_path,monkeypatch)
    legacy=pd.DataFrame([{'oblast':'Lviv','sector':'Construction and reconstruction','procurement_review_priority_candidate':99}])
    result=p.build_scoring_candidate_table(legacy)
    assert result.procurement_review_priority_candidate.isna().all()
    assert result.candidate_support_status.eq('missing_observation_metadata_candidate_withheld').all()
