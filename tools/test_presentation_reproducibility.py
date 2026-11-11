from pathlib import Path
import hashlib,json
import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from presentation_reproducibility import compare_presentation

@pytest.fixture
def pair(tmp_path:Path):
    roots=[tmp_path/'canonical',tmp_path/'built']
    for root in roots:
        root.mkdir();Image.new('RGBA',(3,3),(5,10,15,255)).save(root/'chart.png',compress_level=0)
        (root/'table.csv').write_bytes(b'value\r\n1\r\n');(root/'report.pdf').write_bytes(b'fixed-PDF-reference')
        refresh(root)
    return roots

def refresh(root:Path,metadata:str='same'):
    manifest={'source_contract':'frozen','metrics':metadata,'outputs':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in root.iterdir() if p.name!='presentation_manifest.json'}}
    (root/'presentation_manifest.json').write_text(json.dumps(manifest),encoding='utf8')

def reencode(root:Path):
    with Image.open(root/'chart.png') as image:copy=image.copy()
    copy.save(root/'chart.png',compress_level=9);refresh(root)

def test_identical_bytes_pass(pair):
    assert compare_presentation(*pair)['PNG_encoding_only_differences']==[]

def test_encoding_difference_rejected_in_strict_mode(pair):
    reencode(pair[1])
    with pytest.raises(ValueError,match='bytes changed'):compare_presentation(*pair)

def test_encoding_only_difference_allowed_explicitly(pair):
    reencode(pair[1])
    assert compare_presentation(*pair,True)['PNG_encoding_only_differences']==['chart.png']

def test_changed_pixel_is_never_allowed(pair):
    Image.new('RGBA',(3,3),(6,10,15,255)).save(pair[1]/'chart.png');refresh(pair[1])
    with pytest.raises(ValueError,match='pixels changed'):compare_presentation(*pair,True)

def test_changed_csv_is_never_allowed(pair):
    (pair[1]/'table.csv').write_bytes(b'value\n2\n');refresh(pair[1])
    with pytest.raises(ValueError,match='bytes changed'):compare_presentation(*pair,True)

def test_changed_pdf_is_never_allowed(pair):
    (pair[1]/'report.pdf').write_bytes(b'different-PDF');refresh(pair[1])
    with pytest.raises(ValueError,match='bytes changed'):compare_presentation(*pair,True)

def test_changed_metric_metadata_is_never_allowed(pair):
    refresh(pair[1],'changed')
    with pytest.raises(ValueError,match='metadata changed'):compare_presentation(*pair,True)

def test_hash_manifest_cannot_hide_changed_artifact(pair):
    (pair[1]/'table.csv').write_bytes(b'not-in-manifest')
    with pytest.raises(ValueError,match='manifest mismatch'):compare_presentation(*pair,True)

def test_added_png_metadata_is_never_allowed(pair):
    info=PngInfo();info.add_text('comment','unexpected-label')
    with Image.open(pair[1]/'chart.png') as image:copy=image.copy()
    copy.save(pair[1]/'chart.png',pnginfo=info);refresh(pair[1])
    with pytest.raises(ValueError,match='metadata changed'):compare_presentation(*pair,True)
