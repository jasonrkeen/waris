"""Offline replay using rc11 source and the separately cleared official GRP CSV."""
from pathlib import Path
from unittest.mock import patch
import argparse, json, socket, sys
from clearance import rows, write, sha, benchmark

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--grp',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    seal=json.loads((Path(__file__).resolve().parent.parent/'rc11_source_fingerprints.json').read_text())
    for name,expected in seal.items():
        if sha(args.source/name)!=expected:raise ValueError('Source candidate does not match reviewed rc11')
    if sha(args.grp)!='8d8cd8eb8d361569d3374be529eea8965084de0cc143dbdc9e24b90aa7410490':
        raise ValueError('Expected exact previously cleared GRP input')
    import requests
    sys.path.insert(0,str(args.source.resolve()))
    from src import data_collection as dc
    from src.official_baseline_merge_plan import UKRSTAT_TO_WARIS_OBLAST
    args.output.mkdir(parents=True,exist_ok=False)
    dc.RAW_DIR=args.output/'synthetic_only_work';dc.TABLE_DIR=args.output/'synthetic_only_tables'
    with patch.object(requests.sessions.Session,'request',side_effect=AssertionError('Network denied')),patch.object(socket.socket,'connect',side_effect=AssertionError('Network denied')):
        synthetic=dc.build_synthetic_oblast_sector_data(seed=42).to_dict('records')
        result=benchmark(rows(args.grp),synthetic,UKRSTAT_TO_WARIS_OBLAST)
    write(args.output/'independent_benchmark_reconstruction.csv',result)
    (args.output/'REPLAY_SCOPE.json').write_text(json.dumps(dict(seed=42,network_denied=True,production_scoring_changed=False,official_GRP_benchmark_only=True),indent=2)+'\n')

if __name__=='__main__':main()
