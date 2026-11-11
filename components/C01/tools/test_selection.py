from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import unittest
from validate_selection import validate

ROOT = Path(__file__).resolve().parents[1]

class SelectionIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'candidate'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__'))
    def plan(self): return json.loads((self.root/'INCLUSION_PLAN.json').read_text())
    def replace_manifest_entry(self,rel):
        p=self.root/rel
        m=json.loads((self.root/'FILE_MANIFEST.json').read_text())
        m['files'][rel]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        (self.root/'FILE_MANIFEST.json').write_text(json.dumps(m))
    def test_exact_selection(self): self.assertTrue(validate(self.root)['mandatory_public_companions_present'])
    def test_missing_mandatory_companion_rejected(self):
        (self.root/self.plan()['artifacts'][0]['companion']).unlink()
        with self.assertRaises(ValueError): validate(self.root)
    def test_changed_historical_bytes_rejected(self):
        p=self.root/self.plan()['artifacts'][0]['artifact_path'];p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaises(ValueError): validate(self.root)
    def test_unlisted_data_rejected(self):
        (self.root/'unreviewed_provider.csv').write_text('x\n1\n')
        with self.assertRaises(ValueError): validate(self.root)
    def test_alias_drift_rejected_even_with_updated_inventory(self):
        p=self.plan();p['entries'][-1]['sha256']='0'*64
        (self.root/'INCLUSION_PLAN.json').write_text(json.dumps(p));self.replace_manifest_entry('INCLUSION_PLAN.json')
        with self.assertRaises(ValueError): validate(self.root)
    def test_scoring_promotion_rejected_even_with_updated_inventory(self):
        p=self.plan();p['grp']='scoring'
        (self.root/'INCLUSION_PLAN.json').write_text(json.dumps(p));self.replace_manifest_entry('INCLUSION_PLAN.json')
        with self.assertRaises(ValueError): validate(self.root)
    def test_source_replacement_rejected(self):
        p=self.root/'source_baseline/WARIS-v0.12.0-rc13-docs-review-1.zip'
        p.write_bytes(p.read_bytes()+b'altered');self.replace_manifest_entry(p.relative_to(self.root).as_posix())
        with self.assertRaises(ValueError): validate(self.root)

if __name__=='__main__': unittest.main()
