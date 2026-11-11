from pathlib import Path
import json,shutil
import pytest
from release_metadata import validate_release_metadata

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def candidate(tmp_path:Path)->Path:
    target=tmp_path/'candidate';shutil.copytree(ROOT,target,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'));return target

def mutate(root:Path,key:str,value)->None:
    path=root/'RELEASE_SCOPE.json';scope=json.loads(path.read_text());scope[key]=value;path.write_text(json.dumps(scope))

def test_current_metadata_validates(candidate):
    assert validate_release_metadata(candidate)['security_reporting_configured'] is False

def test_publication_claim_rejected(candidate):
    mutate(candidate,'published',True)
    with pytest.raises(ValueError):validate_release_metadata(candidate)

@pytest.mark.parametrize('key,value',[('doi','10.0000/unassigned'),('repository_url','https://example.invalid/unassigned'),('public_release_date','2026-10-26')])
def test_invented_identifier_or_release_date_rejected(candidate,key,value):
    mutate(candidate,key,value)
    with pytest.raises(ValueError):validate_release_metadata(candidate)

def test_changed_citation_identity_rejected(candidate):
    path=candidate/'CITATION.cff';path.write_text(path.read_text().replace('release-review-1','released-1'))
    with pytest.raises(ValueError):validate_release_metadata(candidate)

def test_GRP_promotion_rejected(candidate):
    mutate(candidate,'official_GRP','scoring')
    with pytest.raises(ValueError):validate_release_metadata(candidate)

def test_unconfigured_route_cannot_be_called_enabled(candidate):
    path=candidate/'RELEASE_SCOPE.json';scope=json.loads(path.read_text());scope['security_reporting']['configured']=True;path.write_text(json.dumps(scope))
    with pytest.raises(ValueError):validate_release_metadata(candidate)

def test_broken_current_reader_link_rejected(candidate):
    path=candidate/'README.md';path.write_text(path.read_text()+'\n[Missing](missing-document.md)\n')
    with pytest.raises(ValueError):validate_release_metadata(candidate)
