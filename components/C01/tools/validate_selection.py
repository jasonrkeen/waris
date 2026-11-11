"""Offline inventory and companion closure; no provider/model certification."""
from pathlib import Path
import csv
import hashlib
import json
import zipfile

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def validate(root: Path) -> dict:
    root = root.resolve()
    def safe(rel: str) -> Path:
        p = (root / rel).resolve()
        if not p.is_relative_to(root) or not p.is_file():
            raise ValueError('Missing or unsafe declared file')
        return p
    manifest = json.loads(safe('FILE_MANIFEST.json').read_text(encoding='utf8'))
    listed = set(manifest['files'])
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and p.name != 'FILE_MANIFEST.json' and '__pycache__' not in p.parts}
    if listed != actual:
        raise ValueError('Inventory mismatch')
    for rel, info in manifest['files'].items():
        data = safe(rel).read_bytes()
        if digest(data) != info['sha256'] or len(data) != info['bytes']:
            raise ValueError('File hash/size mismatch')
    plan = json.loads(safe('INCLUSION_PLAN.json').read_text(encoding='utf8'))
    entries, artifacts = plan['entries'], plan['artifacts']
    if (len(entries), len(artifacts)) != (23, 20):
        raise ValueError('Selection count mismatch')
    if plan['grp'] != 'benchmark_only' or plan['unverified_FIU_claims'] != 'excluded' or plan['published']:
        raise ValueError('Source/publication boundary violation')
    by_id = {a['id']: a for a in artifacts}
    if len(by_id) != 20 or len({a['sha256'] for a in artifacts}) != 20:
        raise ValueError('Duplicate canonical identity')
    originals = {e['original_artifact'] for e in entries}
    if len(originals) != 23:
        raise ValueError('Duplicate original locator')
    if sum(e['package_action'] == 'duplicate_alias_to_selected_file' for e in entries) != 3:
        raise ValueError('Alias count mismatch')
    if sum(e['package_action'] == 'selected_once_for_historical_appendix' for e in entries) != 20:
        raise ValueError('Canonical action mismatch')
    for entry in entries:
        a = by_id[entry['canonical_id']]
        if (entry['sha256'], entry['package_path'], entry['companion']) != (a['sha256'], a['artifact_path'], a['companion']):
            raise ValueError('Alias identity drift')
        if entry['runtime_loading'] != 'not_integrated':
            raise ValueError('Runtime integration not approved')
    for a in artifacts:
        p = safe(a['artifact_path'])
        if not a['artifact_path'].startswith('artifacts/') or digest(p.read_bytes()) != a['sha256']:
            raise ValueError('Historical artifact identity drift')
        with p.open(encoding='utf-8-sig', newline='') as f:
            if len(list(csv.DictReader(f))) != a['rows']:
                raise ValueError('Row count mismatch')
        safe(a['companion'])
        for rel in a['mandatory_files']:
            safe(rel)
        if set(a['original_aliases']) != {e['original_artifact'] for e in entries if e['canonical_id'] == a['id']}:
            raise ValueError('Original alias mapping incomplete')
    with safe('EXCLUDED_HISTORICAL_FILES.csv').open(encoding='utf-8-sig', newline='') as handle:
        excluded = list(csv.DictReader(handle))
    if len(excluded) != 152 or originals & {r['original_artifact'] for r in excluded}:
        raise ValueError('Exclusion inventory violation')
    if any(r['sha256'] in {a['sha256'] for a in artifacts} for r in excluded):
        raise ValueError('Excluded historical bytes included as selected artifact')
    components = json.loads(safe('SOURCE_COMPONENTS.json').read_text(encoding='utf8'))
    source = safe(components['current_source_bundle'])
    expected = components['dependency_source_zips'][source.name]['sha256']
    if digest(source.read_bytes()) != expected:
        raise ValueError('Frozen rc13 source identity mismatch')
    with zipfile.ZipFile(source) as z:
        names = [n for n in z.namelist() if not n.endswith('/')]
        prefix = names[0].split('/')[0] + '/'
        current = json.loads(z.read(prefix + 'CONTROLLED_REVIEW_MANIFEST.json'))
        expected_names = {prefix + rel for rel in current['files']} | {prefix + 'CONTROLLED_REVIEW_MANIFEST.json'}
        if set(names) != expected_names:
            raise ValueError('Nested source inventory mismatch')
        for rel, info in current['files'].items():
            data = z.read(prefix + rel)
            if digest(data) != info['sha256'] or len(data) != info['bytes']:
                raise ValueError('Nested source file mismatch')
    return {'selected_inventory_rows':23, 'unique_historical_files':20, 'aliases':3,
            'excluded_historical_rows':152, 'mandatory_public_companions_present':True,
            'nested_rc13_source_files_verified':len(names), 'full_research_release':'blocked'}

if __name__ == '__main__':
    print(json.dumps(validate(Path(__file__).resolve().parents[1]), indent=2))
