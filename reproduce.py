"""Supported offline engineering replays; no acquisition or full empirical-run claim."""
from pathlib import Path
from dataclasses import dataclass
import argparse,csv,hashlib,importlib.util,json,math,os,shutil,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from git_distribution import restore_replay_metadata

@dataclass(frozen=True)
class ReplayContext:
    output: Path
    child: Path

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path: Path) -> list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as handle:return list(csv.DictReader(handle))

def compare_numeric(actual: Path, expected: Path, keys: list[str]) -> int:
    rows=read(actual);reference=read(expected)
    lookup={tuple(r[k] for k in keys):r for r in reference}
    if len(lookup)!=len(reference) or len(rows)!=len(reference):raise ValueError('Replay support mismatch')
    count=0
    for row in rows:
        other=lookup[tuple(row[k] for k in keys)]
        for field,value in row.items():
            if field in keys:continue
            if field not in other:raise ValueError('Replay column mismatch')
            try:a,b=float(value),float(other[field])
            except ValueError:
                if value!=other[field]:raise ValueError('Replay text mismatch')
            else:
                if not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12):raise ValueError('Replay numeric mismatch')
                count+=1
    return count

def main() -> None:
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    output=args.output_dir.resolve()
    if output.exists():raise ValueError('Refusing to overwrite an existing replay directory')
    output.mkdir(parents=True,exist_ok=False)
    ctx=ReplayContext(output=output,child=ROOT/'tools/offline_child.py')
    logs=output/'logs';logs.mkdir()
    def run(name: str, script: Path, cwd: Path, extra: list[str] | None=None, expected_failure: bool=False) -> subprocess.CompletedProcess:
        result=subprocess.run([sys.executable,'-X','utf8',str(ctx.child),'script',str(script),*(extra or [])],cwd=cwd,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,encoding='utf8',timeout=180)
        (logs/(name+'.log')).write_text(result.stdout+'\n'+result.stderr,encoding='utf8')
        if expected_failure:
            if result.returncode==0:raise ValueError('Live gate unexpectedly permitted execution')
        elif result.returncode:raise RuntimeError(f'Offline replay failed: {name}; see its local log')
        return result
    with tempfile.TemporaryDirectory(prefix='.scratch-',dir=output) as temporary:
        scratch=Path(temporary).resolve();assert scratch.is_relative_to(output)
        current=scratch/'runtime';archival=scratch/'archival_rc11'
        shutil.copytree(ROOT/'runtime',current,ignore=shutil.ignore_patterns('__pycache__','outputs','data','.pytest_cache'))
        shutil.copytree(ROOT/'components/C11',archival,ignore=shutil.ignore_patterns('__pycache__','outputs','data','.pytest_cache'))
        # Restore only recorded Git metadata in disposable replay copies so the
        # historical full-source fingerprints remain exact; code is unchanged.
        restore_replay_metadata(ROOT,current,archival)
        run('synthetic_demo',current/'offline_demo.py',current)
        synthetic=output/'synthetic';synthetic.mkdir()
        manifest=json.loads((current/'outputs/reports/synthetic_demo_manifest.json').read_text())
        if manifest['data_mode']!='synthetic_only' or manifest['official_grp_posture']!='benchmark_only':raise ValueError('Demo source boundary violation')
        for name,info in manifest['files'].items():
            p=current/'outputs/tables'/name
            if digest(p)!=info['sha256']:raise ValueError('Demo manifest mismatch')
            rows=read(p)
            if len(rows)!=info['rows'] or any(r['data_mode']!='synthetic_only' for r in rows):raise ValueError('Synthetic labels/count mismatch')
            shutil.copy2(p,synthetic/name)
        shutil.copy2(current/'outputs/reports/synthetic_demo_manifest.json',synthetic/'synthetic_demo_manifest.json')
        gate=run('live_preflight_gate',current/'main.py',current,['--allow-live'],expected_failure=True)
        gate_text=gate.stdout+gate.stderr
        if 'clearance' not in gate_text.lower() and 'ACLED' not in gate_text:raise ValueError('Unexpected reason for live preflight failure')
        if 'Provider network access denied' in gate_text:raise ValueError('Live gate reached a provider connection')

        # Frozen benchmark helper runs against a disposable exact rc11 copy, not current runtime.
        bench=scratch/'benchmark'
        run('benchmark',ROOT/'components/C05/tools/replay_benchmark.py',ROOT/'components/C05/tools',[
            '--source',str(archival),'--grp',str(ROOT/'components/C04/grp/ukrstat_GRP_2021_benchmark_2026-10-18.csv'),'--output',str(bench)])
        benchmark=output/'benchmark';benchmark.mkdir()
        for name in ('independent_benchmark_reconstruction.csv','REPLAY_SCOPE.json'):shutil.copy2(bench/name,benchmark/name)
        count=compare_numeric(benchmark/'independent_benchmark_reconstruction.csv',ROOT/'components/C05/benchmark/independent_benchmark_reconstruction.csv',['waris_oblast','region_code'])
        if count!=250:raise ValueError('Benchmark numeric cell count mismatch')
        gap=output/'gap';gap.mkdir()
        run('gap',ROOT/'components/C07/tools/replay_public_gap.py',ROOT/'components/C07/tools',[
            '--input',str(ROOT/'components/C07/review/reviewed_benchmark_input.csv'),'--output',str(gap/'gap_review_reconciled.csv')])
        if digest(gap/'gap_review_reconciled.csv')!=digest(ROOT/'components/C07/review/gap_review_reconciled.csv'):raise ValueError('Public gap byte replay mismatch')

        # Standard-library projection only; it does not invoke legacy review or live source loading.
        spec=importlib.util.spec_from_file_location('assembly_scoped_methods',ROOT/'components/C09/tools/methods.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        rescale=output/'rescale';rescale.mkdir()
        projected=module.rescale(module.read(ROOT/'components/C09/reviewed/official_benchmark_input.csv'),module.read(ROOT/'components/C09/reviewed/synthetic_seed42_inputs.csv'))
        module.write(rescale/'rescale_arithmetic_reconstruction.csv',projected)
        rescale_cells=compare_numeric(rescale/'rescale_arithmetic_reconstruction.csv',ROOT/'components/C09/reviewed/rescale_arithmetic_reconstruction.csv',['oblast','sector'])
        if rescale_cells!=1200:raise ValueError('Rescale numeric support mismatch')
        docs=module.documentation_projection(module.read(ROOT/'components/C09/historical/official_baseline_operational_controls_context_bridge.csv'))
        module.write(rescale/'operational_claims_reviewed.csv',docs)
        if digest(rescale/'operational_claims_reviewed.csv')!=digest(ROOT/'components/C09/reviewed/operational_claims_reviewed.csv'):raise ValueError('Documentation projection byte mismatch')

    observed=read(ROOT/'components/C03/procurement/procurement_observed_summary.csv')
    weighted=read(ROOT/'components/C03/procurement/procurement_frame_weighted_estimates.csv')
    if len(observed)!=2 or len(weighted)!=2:raise ValueError('Unreviewed procurement partition')
    for row,weight in zip(observed,weighted):
        if (row['procedure'],row['unit_type'])!=(weight['procedure'],weight['unit_type']):raise ValueError('Procurement domains pooled/misaligned')
        if row['used_in_scoring']!='False' or weight['used_in_scoring']!='False':raise ValueError('Procurement scoring flag')
        n,N=float(row['sampled_tenders']),float(row['domain_frame_tenders'])
        denominator=float(row['observed_eligible_units']);numerator=float(row['observed_exactly_one_active_object_units'])
        for a,b in [(numerator/denominator,float(row['active_object_share'])),(denominator*N/n,float(weight['HT_eligible_unit_total'])),(numerator*N/n,float(weight['HT_exactly_one_active_object_total'])),(numerator/denominator,float(weight['ratio_of_HT_totals']))]:
            if not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12):raise ValueError('Procurement arithmetic mismatch')
    allowed={'WAML-001','WAML-002','WAML-003','WAML-004','WAML-005','WAML-010'}
    if {r['waris_id'] for r in read(ROOT/'reader/literature/conceptual_page_crosswalk_six_themes.csv')}!=allowed:raise ValueError('Withheld reader theme restored')
    if {r['typology_id'] for r in read(ROOT/'components/C04/literature/waris_wartime_aml_typology_register.csv')}!=allowed:raise ValueError('Withheld theme restored in literature register')
    sfms=read(ROOT/'components/C10/reviewed/sfms_q1_2026_selected_facts.csv')
    if len(sfms)!=10 or any(r['context_only']!='True' or r['used_in_scoring']!='False' for r in sfms):raise ValueError('SFMS source boundary')
    wb=read(ROOT/'components/C04/world_bank/world_bank_national_context_2026-10-18.csv')
    if len(wb)!=136 or len({r['indicator_code'] for r in wb})!=4:raise ValueError('World Bank snapshot scope mismatch')
    result={'assembly_id':'WARIS-v0.12.0-rc13-assembled-review-1','network_denied_in_replay_children':True,'synthetic_demo_rows':150,'synthetic_demo_files':5,'benchmark_numeric_cells_matched':250,'gap_byte_replay_matches':True,'rescale_numeric_cells_matched':1200,'documentation_projection_byte_replay_matches':True,'procurement_two_domain_supplied_arithmetic_checked':True,'literature_reader_allowed_themes':6,'SFMS_national_context_rows':10,'World_Bank_snapshot_rows':136,'live_preflight_blocked_before_provider_work':True,'historical_HTTP_or_private_snapshot_replay':False,'full_legacy_pipeline_or_PDF_generated':False,'official_GRP':'benchmark_only','unverified_FIU_claims':'excluded','files':{p.relative_to(output).as_posix():{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(output.rglob('*')) if p.is_file() and 'logs' not in p.relative_to(output).parts}}
    (output/'REPLAY_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
