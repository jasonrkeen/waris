import json
from pathlib import Path
import requests,pytest
from tools.capture_prozorro_sample import CapturePlan,capture


class Response:
    def __init__(self,url,data,status=200):
        self.url=url;self.status_code=status;self.content=json.dumps(data).encode()
        self.headers={'Date':'synthetic-clock','ETag':'synthetic-version','Set-Cookie':'must-not-record'}


class Source:
    def __init__(self,mode='valid'):self.mode=mode;self.calls=0
    def get(self,url,params,**kwargs):
        self.calls+=1;assert kwargs['allow_redirects'] is False
        if self.mode=='connection_failure':raise requests.ConnectionError('synthetic transport error')
        prepared=requests.Request('GET',url,params=params).prepare().url
        if self.calls==1:
            rows=[{'id':'0'*31+'1'},{'id':'0'*31+'2'}]
            if self.mode=='duplicates':rows[1]=rows[0]
            return Response(prepared,{'data':rows,'next_page':{'offset':'synthetic-next'}})
        identity=url.rsplit('/',1)[1]
        if self.mode=='wrong_identity':identity='0'*32
        return Response(prepared,{'data':{'id':identity}},302 if self.mode=='redirect' else 200)


def test_capture_freezes_plan_and_retains_complete_identity_checked_receipt(tmp_path):
    dest=tmp_path/'new';source=Source()
    result=capture(dest,CapturePlan(page_limit=2,detail_limit=2,pause_seconds=0),source)
    assert result['status']=='complete' and result['successful_details']==2 and source.calls==3
    assert result['additional_pages_followed']==0
    assert (dest/'capture_specification.json').is_file()
    assert all(x['http_status']==200 and x['attempt_state']=='response_retained' for x in result['responses'])
    assert 'Set-Cookie' not in json.dumps(result)


@pytest.mark.parametrize('mode',['duplicates','wrong_identity','redirect','connection_failure'])
def test_capture_errors_remain_partial_and_are_not_replaced(tmp_path,mode):
    dest=tmp_path/mode;source=Source(mode)
    with pytest.raises((ValueError,requests.ConnectionError)):
        capture(dest,CapturePlan(page_limit=2,detail_limit=2,pause_seconds=0),source)
    receipt=json.loads((dest/'capture_manifest.json').read_text())
    assert receipt['status']=='failed_partial' and len(receipt['responses'])>=1 and source.calls<=2


def test_capture_never_overwrites_existing_directory(tmp_path):
    dest=tmp_path/'existing';dest.mkdir();(dest/'keep').write_text('preserve')
    with pytest.raises(FileExistsError):capture(dest,CapturePlan(),Source())
    assert (dest/'keep').read_text()=='preserve'
