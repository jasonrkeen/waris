"""Local/CI review checks for an assembled rc13 tree; no data acquisition."""
from pathlib import Path
import argparse,json,os,platform,subprocess,sys,tempfile
from presentation_reproducibility import compare_presentation

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=parser.parse_args()
    root=a.root.resolve();env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'}
    def run(args:list,cwd:Path=root)->None:
        subprocess.run([sys.executable,'-X','utf8',*[str(v) for v in args]],cwd=cwd,env=env,check=True,timeout=600)
    run(['-m','pip','check']);run([root/'tools/validate_assembly.py'])
    suites=[('runtime',['tests']),('components/C01/tools',['test_selection.py']),('plan/tools',['test_plan.py']),('components/C02',['test_frame_study.py','test_lot_study.py','test_geography.py']),('components/C03/tools',['test_projection.py','test_metadata.py']),('components/C05/tools',['test_clearance.py']),('components/C06/tools',['test_reconcile_units.py']),('components/C07/tools',['test_review_methods.py']),('components/C08/tools',['test_candidates.py']),('components/C09/tools',['test_methods.py']),('components/C10/tools',['test_methods.py']),('tools',['test_assembly.py']),('presentation',['test_presentation.py'])]
    for rel,args in suites:
        if rel=='tools':args=[*args,'test_presentation_reproducibility.py']
        run([root/'tools/offline_child.py','pytest',*args],root/rel)
    with tempfile.TemporaryDirectory(prefix='waris-controlled-check-') as temp:
        scratch=Path(temp)
        run([root/'presentation/check_presentation_dashboard.py','--result',scratch/'dashboard.json'])
        expected=json.loads((root/'presentation/outputs/presentation_manifest.json').read_text())
        builds=[]
        for number in (1,2):
            output=scratch/f'build_{number}'
            run([root/'tools/offline_child.py','script',root/'presentation/build_report.py','--output-dir',output])
            builds.append(json.loads((output/'presentation_manifest.json').read_text()))
        if builds[0]!=builds[1]:raise ValueError('Independent presentation builds differ')
        if sys.platform=='win32':encoding_only=False
        elif sys.platform=='linux' and platform.machine()=='x86_64':encoding_only=True
        else:raise ValueError('Platform not qualified by the controlled review')
        comparisons=[compare_presentation(root/'presentation/outputs',scratch/f'build_{number}',encoding_only) for number in (1,2)]
        print(json.dumps({'same_platform_builds_byte_identical':True,'platform':sys.platform,'artifact_comparisons':comparisons},indent=2),flush=True)
    run([root/'tools/validate_assembly.py'])
    print('Controlled release checks passed. No acquisition, publication or empirical validation performed.')

if __name__=='__main__':main()
