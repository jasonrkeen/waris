"""Run one local script/test command with provider network access denied."""
from pathlib import Path
from unittest.mock import patch
import os,runpy,socket,sys
import requests

def denied(*args,**kwargs):
    raise RuntimeError('Provider network access denied by controlled assembly check')

if __name__=='__main__':
    mode,*args=sys.argv[1:]
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    sys.path.insert(0,str(Path.cwd()))
    with patch.object(socket.socket,'connect',side_effect=denied),patch.object(socket,'create_connection',side_effect=denied),patch.object(requests.sessions.Session,'request',side_effect=denied):
        if mode=='pytest':
            import pytest
            raise SystemExit(pytest.main(['-q','-p','no:cacheprovider',*args]))
        if mode=='script':
            target=Path(args[0]).resolve();sys.path.insert(0,str(target.parent));sys.argv=[str(target),*args[1:]]
            runpy.run_path(str(target),run_name='__main__')
        else:raise ValueError('Unknown offline child mode')
