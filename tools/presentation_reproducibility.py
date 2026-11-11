"""Strict source/PDF/table checks with an explicit PNG encoding-only allowance."""
from pathlib import Path
import hashlib,json
from PIL import Image

def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compare_presentation(canonical_dir:Path,output_dir:Path,allow_png_encoding_difference:bool=False)->dict:
    canonical=json.loads((canonical_dir/'presentation_manifest.json').read_text(encoding='utf8'))
    actual=json.loads((output_dir/'presentation_manifest.json').read_text(encoding='utf8'))
    if {k:v for k,v in canonical.items() if k!='outputs'}!={k:v for k,v in actual.items() if k!='outputs'}:
        raise ValueError('Presentation source/metric metadata changed')
    if set(canonical['outputs'])!=set(actual['outputs']):raise ValueError('Presentation output inventory changed')
    encoding_only=[]
    for rel,expected in canonical['outputs'].items():
        base=(canonical_dir/rel).resolve();built=(output_dir/rel).resolve()
        if not base.is_relative_to(canonical_dir.resolve()) or not built.is_relative_to(output_dir.resolve()):raise ValueError('Unsafe presentation output path')
        observed=actual['outputs'][rel]
        if digest(base)!=expected['sha256'] or base.stat().st_size!=expected['bytes']:raise ValueError('Canonical artifact changed')
        if digest(built)!=observed['sha256'] or built.stat().st_size!=observed['bytes']:raise ValueError('Build artifact/manifest mismatch')
        if expected==observed:continue
        if not (allow_png_encoding_difference and Path(rel).suffix.lower()=='.png'):raise ValueError('Presentation bytes changed')
        with Image.open(base) as first,Image.open(built) as second:
            if first.format!='PNG' or second.format!='PNG' or first.size!=second.size:raise ValueError('PNG type/dimensions changed')
            if first.info!=second.info:raise ValueError('PNG metadata changed')
            if first.convert('RGBA').tobytes()!=second.convert('RGBA').tobytes():raise ValueError('PNG decoded pixels changed')
        encoding_only.append(rel)
    return {'nonoutput_metadata_identical':True,'PDF_and_plotted_CSV_bytes_identical':True,'PNG_encoding_only_differences':encoding_only,'PNG_pixels_identical':True}
