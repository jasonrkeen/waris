import pytest
from verify_geography import reconcile,EXPECTED

def fixtures():
    legacy=[];official=[]
    for i,(english,ukrainian) in enumerate(EXPECTED.items()):
        code=f'UA{i:017d}';legacy.append({'waris_oblast':english,'ukrstat_oblast':'historical-label','region_code':code})
        official.append({'code':code,'name':ukrainian,'category':'K' if english=='Kyiv City' else 'O','worksheet_row':i+5})
    return legacy,official

def test_all_expected_geographies():
    a,b=fixtures();assert len(reconcile(a,b))==25

@pytest.mark.parametrize('issue',['code','name','category','duplicate','missing'])
def test_reject_geography_mismatch(issue):
    a,b=fixtures()
    if issue=='code':a[0]['region_code']='unknown'
    elif issue=='name':b[0]['name']='wrong'
    elif issue=='category':b[0]['category']='P'
    elif issue=='duplicate':b.append(b[0])
    else:a.pop()
    with pytest.raises(ValueError):reconcile(a,b)
