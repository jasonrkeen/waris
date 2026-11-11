"""Offline plan/companion checks; optional exact locally retained component checks."""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import zipfile

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def validate(root: Path, components_dir: Path | None = None) -> dict:
    root=root.resolve()
    def safe(rel: str) -> Path:
        p=(root/rel).resolve()
        if not p.is_relative_to(root) or not p.is_file(): raise ValueError('Missing/unsafe plan file')
        return p
    manifest=json.loads(safe('FILE_MANIFEST.json').read_text(encoding='utf8'))
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.relative_to(root).as_posix()!='FILE_MANIFEST.json'}
    if actual!=set(manifest['files']):raise ValueError('Plan inventory mismatch')
    for rel,info in manifest['files'].items():
        data=safe(rel).read_bytes()
        if digest(data)!=info['sha256'] or len(data)!=info['bytes']:raise ValueError('Plan file hash mismatch')
    plan=json.loads(safe('FULL_RELEASE_PLAN.json').read_text(encoding='utf8'))
    boundaries=json.loads(safe('SOURCE_BOUNDARIES.json').read_text(encoding='utf8'))
    expected={'official_GRP':'benchmark_only','GRP_scoring_and_Monte_Carlo':'prohibited','GRP_sector_economic_allocation':'not_approved','unverified_FIU_claims':'excluded','expanded_procurement':'review_only','confidence':'categorical_counts_no_numeric_mean_or_adjusted_score','publication_or_push':False,'full_research_release':'blocked'}
    if any(boundaries.get(k)!=v for k,v in expected.items()) or plan['boundaries']!=boundaries or plan['published']:
        raise ValueError('Source/publication boundary violation')
    components={c['id']:c for c in plan['components']}
    if len(components)!=11 or len(plan['components'])!=11:raise ValueError('Component identity/count mismatch')
    if components['C11']['runtime_status']!='archival_replay_only':raise ValueError('Archival runtime promotion')
    for cid in ('C05','C06','C09'):
        if 'C11' not in components[cid]['dependencies']:raise ValueError('Required archival replay dependency omitted')
    visited=set();visiting=set()
    def visit(cid):
        if cid not in components:raise ValueError('Missing dependency')
        if cid in visiting:raise ValueError('Dependency cycle')
        if cid in visited:return
        visiting.add(cid)
        for dep in components[cid]['dependencies']:visit(dep)
        visiting.remove(cid);visited.add(cid)
    for cid in components:
        visit(cid);safe(components[cid]['mandatory_scope_companion'])
    def csv_rows(rel):
        with safe(rel).open(encoding='utf-8-sig',newline='') as handle:return list(csv.DictReader(handle))
    entries=csv_rows('MEMBER_INCLUSION_LIST.csv')
    if len({(r['component_id'],r['source_member']) for r in entries})!=len(entries):raise ValueError('Duplicate member identity')
    if any(r['component_id'] not in components for r in entries):raise ValueError('Unselected component member')
    decisions=csv_rows('COMPONENT_DECISIONS.csv')
    for c in components.values():
        matched=[r for r in decisions if r['source_zip']==c['source_zip']]
        if len(matched)!=1 or matched[0]['plan_action']!='selected_scoped_component' or matched[0]['sha256']!=c['sha256']:
            raise ValueError('Component inclusion decision drift')
    selected_zips={c['source_zip'] for c in components.values()}
    if {r['source_zip'] for r in decisions if r['plan_action']=='selected_scoped_component'}!=selected_zips:raise ValueError('Undeclared selected ZIP')
    transforms=json.loads(safe('TRANSFORMATIONS.json').read_text())
    if len(transforms)!=1 or transforms[0]['id']!='N01':raise ValueError('Transformation identity mismatch')
    n=transforms[0];data=safe(n['path']).read_bytes()
    if digest(data)!=n['sha256'] or len(data)!=n['bytes']:raise ValueError('Projection identity mismatch')
    allowed={'WAML-001','WAML-002','WAML-003','WAML-004','WAML-005','WAML-010'}
    themes=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    if len(themes)!=6 or {r['waris_id'] for r in themes}!=allowed:raise ValueError('Withheld literature theme restored')
    for rel in n['required_companions']:safe(rel)
    old=[r for r in entries if r['component_id']=='C04' and r['relative_member']=='docs/typology_conceptual_page_crosswalk.csv']
    if len(old)!=1 or old[0]['plan_action']!='omit_reader_version_replace_with_N01' or old[0]['sha256']!=n['source_sha256']:
        raise ValueError('Old reader crosswalk not superseded')
    checked_members=0
    if components_dir is not None:
        for cid,c in components.items():
            if Path(c['source_zip']).name!=c['source_zip']:raise ValueError('Unsafe component locator')
            p=components_dir/c['source_zip']
            if not p.is_file() or digest(p.read_bytes())!=c['sha256']:raise ValueError('Component missing or altered')
            with zipfile.ZipFile(p) as z:
                names={s for s in z.namelist() if not s.endswith('/')}
                component_entries=[r for r in entries if r['component_id']==cid]
                if names!={r['source_member'] for r in component_entries}:raise ValueError('Component inventory incomplete')
                for r in component_entries:
                    data=z.read(r['source_member'])
                    if digest(data)!=r['sha256'] or len(data)!=int(r['bytes']):raise ValueError('Component member mismatch')
                    checked_members+=1
    return {'components':11,'member_decisions':len(entries),'selected_direct_members':sum(r['plan_action']=='select_frozen_member' for r in entries),'withheld_reader_crosswalks_replaced':1,'literature_reader_themes':6,'acyclic_dependencies':True,'companion_files_present':True,'external_component_bytes_checked':components_dir is not None,'external_direct_members_verified':checked_members,'full_research_release':'blocked','publication':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--components-dir',type=Path);args=parser.parse_args()
    print(json.dumps(validate(Path(__file__).resolve().parents[1],args.components_dir),indent=2))
