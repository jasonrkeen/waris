"""Permit two exact Git-attribute packaging adapters; never code/data overrides."""
from pathlib import Path
import hashlib,json

ORIGINAL_SHA256='e1357bb602862385b16147b77b4e0d5f6af570b6fa228d3142f2bc41f6d62fb3'
REPLACEMENT=b'* -text\n'
OVERRIDES={'runtime/.gitattributes':'provenance/git_attributes/runtime.original.gitattributes','components/C11/.gitattributes':'provenance/git_attributes/archival_rc11.original.gitattributes'}

def verify_git_overrides(root:Path)->dict[str,bytes]:
    def read(rel:str)->bytes:
        path=(root/rel).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():raise ValueError('Missing or unsafe Git metadata evidence')
        return path.read_bytes()
    ledger=json.loads(read('GIT_METADATA_OVERRIDES.json'))
    if ledger['schema']!='WARIS-git-attributes-only-1' or set(ledger['overrides'])!=set(OVERRIDES):raise ValueError('Unapproved Git metadata override inventory')
    if read('.gitattributes')!=REPLACEMENT:raise ValueError('Root Git normalization policy changed')
    originals={}
    for rel,archive in OVERRIDES.items():
        entry=ledger['overrides'][rel]
        expected={'original_sha256':ORIGINAL_SHA256,'replacement_sha256':hashlib.sha256(REPLACEMENT).hexdigest(),'archived_original':archive,'scope':'Git line-ending metadata only; no source/data/model change'}
        if entry!=expected:raise ValueError('Git metadata exception changed')
        data=read(archive)
        if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA256:raise ValueError('Original Git metadata evidence changed')
        if read(rel)!=REPLACEMENT:raise ValueError('Git metadata replacement changed')
        originals[rel]=data
    return originals

def restore_replay_metadata(root:Path,runtime_copy:Path,archival_copy:Path)->None:
    originals=verify_git_overrides(root)
    targets={'runtime/.gitattributes':runtime_copy/'.gitattributes','components/C11/.gitattributes':archival_copy/'.gitattributes'}
    for target in targets.values():
        if target.resolve().is_relative_to(root.resolve()):raise ValueError('Replay metadata restoration must be outside the candidate')
        if not target.is_file() or target.read_bytes()!=REPLACEMENT:raise ValueError('Replay copy is not the expected distribution view')
    for rel,target in targets.items():target.write_bytes(originals[rel])
