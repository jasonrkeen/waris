"""Validate materialised rc13 selection and immutable source boundaries offline."""
from pathlib import Path
import csv,hashlib,json,zipfile

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def validate(root: Path) -> dict:
    root=root.resolve()
    def file(rel: str) -> Path:
        p=(root/rel).resolve()
        if not p.is_relative_to(root) or not p.is_file():raise ValueError('Missing or unsafe assembly file')
        return p
    def read_csv(rel: str) -> list[dict[str,str]]:
        with file(rel).open(encoding='utf-8-sig',newline='') as handle:return list(csv.DictReader(handle))
    manifest=json.loads(file('ASSEMBLY_MANIFEST.json').read_text(encoding='utf8'))
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.relative_to(root).as_posix()!='ASSEMBLY_MANIFEST.json'}
    if actual!=set(manifest['files']):raise ValueError('Unreviewed/missing assembly file')
    for rel,info in manifest['files'].items():
        data=file(rel).read_bytes()
        if digest(data)!=info['sha256'] or len(data)!=info['bytes']:raise ValueError('Assembly hash mismatch')
    plan=json.loads(file('plan/FULL_RELEASE_PLAN.json').read_text(encoding='utf8'))
    bounds=json.loads(file('SOURCE_BOUNDARIES.json').read_text(encoding='utf8'))
    if bounds!=plan['boundaries'] or bounds['official_GRP']!='benchmark_only' or bounds['unverified_FIU_claims']!='excluded' or bounds['publication_or_push']:
        raise ValueError('Source/publication boundary violation')
    entries=read_csv('plan/MEMBER_INCLUSION_LIST.csv')
    selected=[r for r in entries if r['plan_action']=='select_frozen_member']
    if len(selected)!=317:raise ValueError('Selection count mismatch')
    expected_components={r['planned_path'] for r in selected}
    actual_components={p.relative_to(root).as_posix() for p in (root/'components').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if expected_components!=actual_components:raise ValueError('Component selection drift')
    for r in selected:
        if digest(file(r['planned_path']).read_bytes())!=r['sha256']:raise ValueError('Frozen component bytes altered')
        file('plan/'+r['mandatory_scope_companion'])
    forbidden=root/'components/C04/docs/typology_conceptual_page_crosswalk.csv'
    if forbidden.exists():raise ValueError('Old ten-theme reader crosswalk restored')
    allowed={'WAML-001','WAML-002','WAML-003','WAML-004','WAML-005','WAML-010'}
    themes=read_csv('reader/literature/conceptual_page_crosswalk_six_themes.csv')
    if len(themes)!=6 or {r['waris_id'] for r in themes}!=allowed:raise ValueError('Withheld literature theme restored')
    if digest(file('reader/literature/conceptual_page_crosswalk_six_themes.csv').read_bytes())!=digest(file('plan/reader/literature/conceptual_page_crosswalk_six_themes.csv').read_bytes()):raise ValueError('N01 projection changed')
    file('reader/literature/ATTRIBUTION_AND_CHANGES.md')
    source=file('components/C01/source_baseline/WARIS-v0.12.0-rc13-docs-review-1.zip')
    if digest(source.read_bytes())!='64b635f93b164e6f3e859b7c5c67f4436c9e0339b0e5cea79b5022aa444c4158':raise ValueError('Current source ZIP changed')
    with zipfile.ZipFile(source) as z:
        original={n.split('/',1)[1]:z.read(n) for n in z.namelist() if not n.endswith('/')}
    current={p.relative_to(root/'runtime').as_posix() for p in (root/'runtime').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if current!=set(original):raise ValueError('Runtime source inventory changed')
    for rel,data in original.items():
        if file('runtime/'+rel).read_bytes()!=data:raise ValueError('Current runtime source changed')
    excluded={r['sha256'] for r in read_csv('components/C01/EXCLUDED_HISTORICAL_FILES.csv')}
    for rel in actual:
        if Path(rel).suffix.lower() in ('.csv','.png','.pdf') and digest(file(rel).read_bytes()) in excluded:raise ValueError('Excluded historical artifact restored')
    example_manifest=root/'examples/synthetic/synthetic_demo_manifest.json'
    if example_manifest.is_file():
        example=json.loads(example_manifest.read_text(encoding='utf8'))
        if example['data_mode']!='synthetic_only' or example['official_grp_posture']!='benchmark_only':raise ValueError('Example boundary violation')
        for name,info in example['files'].items():
            rows=read_csv('examples/synthetic/'+name)
            if len(rows)!=info['rows'] or any(r['data_mode']!='synthetic_only' for r in rows):raise ValueError('Example synthetic label/count violation')
            if digest(file('examples/synthetic/'+name).read_bytes())!=info['sha256']:raise ValueError('Example hash mismatch')
    return {'selected_component_files':317,'unchanged_runtime_files':len(original),'reader_literature_themes':6,'historical_exclusion_hashes_checked':len(excluded),'source_boundaries_preserved':True,'examples_labelled_synthetic':example_manifest.is_file(),'integrated_historical_or_live_pipeline_replayed':False,'full_research_release':'blocked','published':False}

if __name__=='__main__':print(json.dumps(validate(Path(__file__).resolve().parents[1]),indent=2))
