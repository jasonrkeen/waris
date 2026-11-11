from pathlib import Path
from unittest.mock import patch
import argparse,ipaddress,json,shutil,socket,sys,tempfile
import requests
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--result',type=Path,required=True);args=parser.parse_args()
    original_connect=socket.socket.connect
    def connect(sock: socket.socket,address: tuple):
        try:local=isinstance(address,tuple) and ipaddress.ip_address(address[0]).is_loopback
        except ValueError:local=False
        if not local:raise RuntimeError('External network denied')
        return original_connect(sock,address)
    results=[]
    with patch.object(socket.socket,'connect',new=connect),patch.object(requests.sessions.Session,'request',side_effect=RuntimeError('Provider HTTP denied')):
        at=AppTest.from_file(str(ROOT/'presentation/dashboard.py'),default_timeout=60).run()
        assert not at.exception
        for section in at.radio[0].options:
            at.radio[0].set_value(section).run();assert not at.exception,section
            assert any('Synthetic WARIS' in r.value for r in at.warning)
            results.append({'section':section,'exceptions':0,'tables':len(at.dataframe)})
        at.radio[0].set_value('Synthetic illustration').run()
        at.multiselect[0].set_value([at.multiselect[0].options[0]]).run();assert not at.exception
        assert at.metric[0].value=='6'
        at.multiselect[1].set_value([at.multiselect[1].options[0]]).run();assert not at.exception;assert at.metric[0].value=='1'
        at.slider[0].set_value(100.0).run();assert not at.exception;assert at.metric[0].value=='0';assert len(at.dataframe)==0
        with tempfile.TemporaryDirectory() as temporary:
            copied=Path(temporary)/'candidate';shutil.copytree(ROOT,copied,ignore=shutil.ignore_patterns('__pycache__'))
            source=copied/'examples/synthetic/waris_scored_oblast_sector.csv';source.write_bytes(source.read_bytes()+b'\n')
            bad=AppTest.from_file(str(copied/'presentation/dashboard.py'),default_timeout=60).run()
            assert not bad.exception and len(bad.dataframe)==0 and any('Snapshot validation failed' in e.value for e in bad.error)
    receipt={'sections':results,'all_seven_sections_rendered':len(results)==7,'one_region_six_rows':True,'one_region_one_sector_one_row':True,'threshold_100_empty_selection_remains_empty':True,'tampered_snapshot_fails_closed_without_results':True,'external_network_and_provider_HTTP_denied':True,'loopback_only_for_framework':True,'browser_visual_check_separate':True}
    args.result.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
