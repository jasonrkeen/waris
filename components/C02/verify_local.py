from pathlib import Path
import json,socket
from unittest.mock import patch
import requests
from frame_study import analyze,save,digest
BASE=Path(__file__).resolve().parent
with patch.object(requests.sessions.Session,'request',side_effect=AssertionError('Network denied')),patch.object(socket.socket,'connect',side_effect=AssertionError('Network denied')):
    a=analyze(BASE/'frozen_study',BASE/'offline_replay_a')
    b=analyze(BASE/'frozen_study',BASE/'offline_replay_b')
assert a==b==json.loads((BASE/'analysis_first/frame_results_PRIVATE.json').read_text())
assert (BASE/'offline_replay_a/frame_results_PRIVATE.json').read_bytes()==(BASE/'offline_replay_b/frame_results_PRIVATE.json').read_bytes()
frame=json.loads((BASE/'frozen_study/private_capture/frame.json').read_text())
times=[x.get('public_modified') for x in frame]
observed=[x for x in times if isinstance(x,(int,float)) and not isinstance(x,bool)]
save(BASE/'execution_validation.json',{'network_denied_replays':2,'byte_identical_results':True,'responses_verified':a['frame_pages']+a['selected_details'],'details_verified':a['selected_details'],
    'frame_pages':a['frame_pages'],'unique_frame_tenders':len(frame),'selection_frozen_before_details':True,
    'public_modified_observed':len(observed),'public_modified_nonincreasing_if_all_observed':all(x>=y for x,y in zip(observed,observed[1:])) if len(observed)==len(times) else None,
    'result_sha256':digest((BASE/'offline_replay_a/frame_results_PRIVATE.json').read_bytes()),'plan_sha256':a['plan_sha256'],
    'capture_manifest_sha256':a['capture_manifest_sha256'],'national_complete_period_claim':False,'public_numeric_clearance':False})
print('Two offline replays matched. Finite recorded frame only.')
