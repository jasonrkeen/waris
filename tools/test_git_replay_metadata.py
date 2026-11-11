from pathlib import Path
import hashlib,shutil
import pytest
from git_distribution import ORIGINAL_SHA256,REPLACEMENT,restore_replay_metadata

ROOT=Path(__file__).resolve().parents[1]
def copies(tmp_path:Path):
    runtime=tmp_path/'runtime';archival=tmp_path/'archival'
    for path in (runtime,archival):path.mkdir();(path/'.gitattributes').write_bytes(REPLACEMENT);(path/'source.py').write_bytes(b'# synthetic fixture\n')
    return runtime,archival

def test_only_original_attributes_restored_in_scratch(tmp_path):
    runtime,archival=copies(tmp_path)
    restore_replay_metadata(ROOT,runtime,archival)
    for path in (runtime,archival):
        assert hashlib.sha256((path/'.gitattributes').read_bytes()).hexdigest()==ORIGINAL_SHA256
        assert (path/'source.py').read_bytes()==b'# synthetic fixture\n'
    assert (ROOT/'runtime/.gitattributes').read_bytes()==REPLACEMENT

def test_candidate_itself_cannot_be_restoration_target(tmp_path):
    runtime,archival=copies(tmp_path)
    with pytest.raises(ValueError,match='outside the candidate'):restore_replay_metadata(ROOT,ROOT/'runtime',archival)

def test_unexpected_scratch_attribute_is_rejected(tmp_path):
    runtime,archival=copies(tmp_path);(archival/'.gitattributes').write_bytes(b'* text=auto\n')
    with pytest.raises(ValueError,match='expected distribution view'):restore_replay_metadata(ROOT,runtime,archival)
    assert (runtime/'.gitattributes').read_bytes()==REPLACEMENT
