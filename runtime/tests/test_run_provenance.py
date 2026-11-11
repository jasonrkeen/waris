from dataclasses import asdict
import json

import pandas as pd
import pytest

from src import provenance as p, run_manifest as manifest


@pytest.fixture
def project(tmp_path, monkeypatch):
    for folder in ['src', 'data/raw', 'outputs/tables', 'outputs/reports']:
        (tmp_path/folder).mkdir(parents=True, exist_ok=True)
    (tmp_path/'src/example.py').write_text('VALUE = 1\n', encoding='utf8')
    (tmp_path/'.env').write_text('PASSWORD=must_never_be_captured\n', encoding='utf8')
    (tmp_path/'data/raw/existing.csv').write_text('value\n5\n', encoding='utf8')
    for name, path in {'BASE_DIR':tmp_path,'OUTPUT_DIR':tmp_path/'outputs','REPORT_DIR':tmp_path/'outputs/reports',
                       'TABLE_DIR':tmp_path/'outputs/tables','RUN_MANIFEST_TABLE':tmp_path/p.METADATA_PATHS[0],
                       'RUN_MANIFEST_SUMMARY_TABLE':tmp_path/p.METADATA_PATHS[1],
                       'RUN_MANIFEST_JSON':tmp_path/p.METADATA_PATHS[2]}.items():
        monkeypatch.setattr(manifest, name, path)
    return tmp_path


def finish(root):
    context = p.start_run(root)
    context = p.capture_scoring_input(context, root, pd.DataFrame({'input':[1.25,2.5]}))
    context = p.capture_simulation_input(context, root, pd.DataFrame({'score':[10.5,20.5]}))
    (root/'outputs/reports/report.pdf').write_bytes(b'%PDF-final-content')
    manifest.build_run_manifest_artifacts(context=context, manifest_phase='final')
    return context


def test_unique_ids_do_not_depend_on_wall_clock(project, monkeypatch):
    monkeypatch.setattr(p, 'utc_now', lambda:'2026-10-18T00:00:00+00:00')
    contexts = [p.start_run(project) for _ in range(100)]
    assert len({c.run_id for c in contexts}) == 100
    assert len({c.started_at_utc for c in contexts}) == 1


def test_complete_inventory_correct_sizes_no_self_reference_and_preserved_identity(project):
    context = finish(project)
    assert p.verify_run(project) == []
    payload = json.loads((project/p.METADATA_PATHS[3]).read_text(encoding='utf8'))
    assert payload['run_id'] == context.run_id
    assert payload['context']['scoring_input']['rows'] == 2
    assert payload['context']['simulation_input']['rows'] == 2
    assert 'must_never_be_captured' not in json.dumps(payload)
    assert '.env' not in {f['path'] for f in payload['source_final']}
    observed = payload['artifacts_final']
    assert {f['path'] for f in observed} == {f.path for f in p.artifact_snapshot(project)}
    assert next(f for f in observed if f['path']=='data/raw/existing.csv')['observation']=='preexisting_content_unchanged'
    assert not set(p.METADATA_PATHS) & {f['path'] for f in observed}
    for row in payload['manifest_files']:
        assert row == asdict(p.record_file(project, project/row['path']))
    table = pd.read_csv(project/p.METADATA_PATHS[0])
    for row in table.to_dict('records'):
        evidence = p.record_file(project, project/row['path'])
        assert evidence.sha256 == row['sha256'] and evidence.bytes == row['file_size_bytes']


@pytest.mark.parametrize('mutation', ['data','output','source','new_output','manifest','seal','missing_seal'])
def test_integrity_verification_rejects_changes(project, mutation):
    finish(project)
    paths = {'data':'data/raw/existing.csv','output':'outputs/reports/report.pdf','source':'src/example.py',
             'new_output':'outputs/tables/untracked.csv','manifest':p.METADATA_PATHS[0],'seal':p.METADATA_PATHS[3]}
    if mutation=='missing_seal':
        (project/p.METADATA_PATHS[3]).unlink()
    else:
        (project/paths[mutation]).write_text('changed', encoding='utf8')
    assert p.verify_run(project)


def test_source_drift_and_changed_scoring_snapshot_refuse_finalization(project):
    context = p.start_run(project)
    context = p.capture_scoring_input(context, project, pd.DataFrame({'input':[1]}))
    (project/context.scoring_input['path']).write_text('input\n999\n',encoding='utf8')
    with pytest.raises(RuntimeError, match='scoring input changed'):
        manifest.build_run_manifest_artifacts(context=context)
    (project/'src/example.py').write_text('VALUE = 2\n', encoding='utf8')
    with pytest.raises(RuntimeError, match='Source changed'):
        manifest.build_run_manifest_artifacts(context=context)


def test_wrong_run_identity_and_standalone_claim_boundaries(project):
    context=p.start_run(project)
    with pytest.raises(ValueError, match='identity'):
        manifest.build_run_manifest_artifacts(context=context, run_id='wrong')
    manifest.build_run_manifest_artifacts(manifest_phase='standalone')
    payload=json.loads((project/p.METADATA_PATHS[3]).read_text(encoding='utf8'))
    assert payload['context'] is None
    assert payload['execution_scope']=='standalone_file_observation_not_pipeline_execution'
    assert p.verify_run(project)==[]


def test_inventory_change_between_manifest_and_seal_is_rejected(project):
    context=p.start_run(project)
    manifest.build_run_manifest_artifacts(context=context, manifest_phase='pre_report')
    (project/'outputs/tables/late.csv').write_text('value\n9\n',encoding='utf8')
    with pytest.raises(RuntimeError, match='between manifest inventory'):
        p.seal_run(project, context, context.run_id, 'final')


def test_release_specification_changes_are_source_drift(project):
    specification=project/'release_specification.json'
    specification.write_text('{"status":"draft"}',encoding='utf8')
    context=p.start_run(project)
    assert specification.name in {r.path for r in context.source_before}
    specification.write_text('{"status":"changed"}',encoding='utf8')
    with pytest.raises(RuntimeError, match='Source changed'):
        manifest.build_run_manifest_artifacts(context=context)


def test_capture_tool_sources_are_inventoried_and_changes_are_detected(project):
    tools=project/'tools';tools.mkdir();script=tools/'capture.py';script.write_text('VALUE = 1\n',encoding='utf8')
    finish(project)
    payload=json.loads((project/p.METADATA_PATHS[3]).read_text(encoding='utf8'))
    assert 'tools/capture.py' in {f['path'] for f in payload['source_final']}
    assert p.verify_run(project)==[]
    script.write_text('VALUE = 2\n',encoding='utf8')
    assert 'source_inventory_or_content_mismatch' in p.verify_run(project)
