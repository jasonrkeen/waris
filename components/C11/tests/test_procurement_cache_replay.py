import io,json
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from src import prozorro_procurement_features as procurement


def tender():
    return {'id':'synthetic-record','title':'synthetic repair','description':None,
        'procuringEntity':{'name':'Synthetic Buyer','address':{'region':'Lviv'}},
        'value':{'amount':125.25,'currency':'UAH','valueAddedTaxIncluded':True},
        'items':[{'classification':{'id':'00000000-0'}}],
        'bids':[{'id':'synthetic-bid-1'},{'id':'synthetic-bid-2'}],
        'awards':[{'suppliers':[{'identifier':{'id':'synthetic-supplier'}}]}]}


@pytest.mark.parametrize('encoding',['legacy_literal','json'])
def test_nested_csv_round_trip_preserves_live_feature_frame(encoding):
    live=pd.DataFrame([tender(),{'id':'synthetic-empty','title':'synthetic'}])
    expected=procurement._prepare_tender_feature_rows(live)
    cached=live.copy()
    if encoding=='json':
        for col in ['value','procuringEntity','items','bids','awards']:
            cached[col]=cached[col].map(lambda x:json.dumps(x) if isinstance(x,(dict,list)) else x)
    restored=pd.read_csv(io.StringIO(cached.to_csv(index=False)))
    actual=procurement._prepare_tender_feature_rows(restored)
    assert_frame_equal(expected,actual)
    assert actual.loc[0,'value_amount']==125.25
    assert actual.loc[0,'bids_count']==2 and actual.loc[0,'supplier_count']==1
    assert actual.loc[0,'currency']=='UAH'


@pytest.mark.parametrize('bad',["__import__('os').system('echo must-not-run')",'{not valid',"{'amount': external_name}"])
def test_invalid_cache_literal_fails_without_executing_or_echoing_source(bad):
    with pytest.raises(ValueError) as err:
        procurement._prepare_tender_feature_rows(pd.DataFrame([{'value':bad}]))
    assert bad not in str(err.value)


@pytest.mark.parametrize('field,bad',[('value','[]'),('bids','{}')])
def test_wrong_nested_container_fails(field,bad):
    with pytest.raises(ValueError):
        procurement._prepare_tender_feature_rows(pd.DataFrame([{field:bad}]))


def test_oversized_nested_cache_cell_fails():
    with pytest.raises(ValueError,match='Oversized'):
        procurement._prepare_tender_feature_rows(pd.DataFrame([{'value':'{'+' '*2_000_001}]))


def test_missing_text_never_becomes_nan_keyword_text():
    assert procurement._flatten_text(float('nan'))==''
    assert procurement._flatten_text(None)==''
