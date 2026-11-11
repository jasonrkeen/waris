"""Headless behavior check only; not browser/layout or full research-PDF QA."""
from pathlib import Path
from unittest.mock import patch
import argparse,ipaddress,json,os,shutil,socket,subprocess,sys,tempfile
import requests

ROOT=Path(__file__).resolve().parents[1]

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--result',type=Path,required=True);args=parser.parse_args()
    if args.result.exists():raise ValueError('Refusing to overwrite dashboard check receipt')
    with tempfile.TemporaryDirectory(prefix='waris-dashboard-') as temporary:
        target=Path(temporary).resolve()/'runtime'
        shutil.copytree(ROOT/'runtime',target,ignore=shutil.ignore_patterns('__pycache__','outputs','data'))
        result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/offline_child.py'),'script',str(target/'offline_demo.py')],cwd=target,capture_output=True,text=True,encoding='utf8',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=180)
        if result.returncode:raise RuntimeError('Synthetic dashboard inputs failed')
        sys.path.insert(0,str(target))
        from streamlit.testing.v1 import AppTest
        original_connect=socket.socket.connect
        def loopback_only(sock: socket.socket, address: tuple) -> None:
            # Windows asyncio uses a local socket pair even for headless AppTest.
            try:local=isinstance(address,tuple) and ipaddress.ip_address(address[0]).is_loopback
            except ValueError:local=False
            if not local:raise RuntimeError('External network denied in dashboard check')
            return original_connect(sock,address)
        with patch.object(socket.socket,'connect',new=loopback_only),patch.object(requests.sessions.Session,'request',side_effect=RuntimeError('Provider HTTP denied')):
            at=AppTest.from_file(str(target/'app.py'),default_timeout=60).run()
            if at.exception:raise ValueError('Dashboard raised an exception')
            warnings=[x.value for x in at.warning]
            if not any('synthetic' in x.lower() for x in warnings):raise ValueError('Missing synthetic dashboard notice')
            initial_frames=len(at.dataframe)
            if at.multiselect:
                options=at.multiselect[0].options
                if options:at.multiselect[0].set_value([options[0]]).run()
                if at.exception:raise ValueError('Dashboard filtering raised an exception')
            receipt={'synthetic_inputs_only':True,'initial_render_exception_count':0,'filter_render_exception_count':0,'synthetic_notice_present':True,'initial_dataframes':initial_frames,'multiselect_widgets':len(at.multiselect),'headless_AppTest_only':True,'external_connections_and_provider_HTTP_denied':True,'loopback_allowed_for_Windows_asyncio_socketpair':True,'browser_visual_or_PDF_QA':False,'optional_research_tabs_not_populated_from_historical_caches':True,'runtime_source_unchanged':True}
        args.result.parent.mkdir(parents=True,exist_ok=True);args.result.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
