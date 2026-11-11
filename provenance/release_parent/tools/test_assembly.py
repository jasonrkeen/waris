from pathlib import Path
import hashlib,json,shutil,tempfile,unittest
from validate_assembly import validate

ROOT=Path(__file__).resolve().parents[1]

class AssemblyChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'candidate';shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__'))
    def reseal(self,rel):
        p=self.root/rel;m=json.loads((self.root/'ASSEMBLY_MANIFEST.json').read_text())
        m['files'][rel]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
        (self.root/'ASSEMBLY_MANIFEST.json').write_text(json.dumps(m))
    def test_exact_materialisation(self):self.assertEqual(validate(self.root)['selected_component_files'],317)
    def test_missing_companion_rejected(self):
        (self.root/'plan/companions/C03.md').unlink()
        with self.assertRaises(ValueError):validate(self.root)
    def test_extra_provider_input_rejected(self):
        (self.root/'unreviewed_provider.csv').write_text('x\n1\n')
        with self.assertRaises(ValueError):validate(self.root)
    def test_runtime_mutation_even_after_reseal(self):
        p=self.root/'runtime/main.py';p.write_bytes(p.read_bytes()+b'\n# drift\n');self.reseal('runtime/main.py')
        with self.assertRaises(ValueError):validate(self.root)
    def test_restored_ten_row_reader_crosswalk_rejected(self):
        rel='components/C04/docs/typology_conceptual_page_crosswalk.csv';p=self.root/rel;p.parent.mkdir(exist_ok=True);p.write_text('waris_id\nWAML-006\n');self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_benchmark_scoring_promotion_rejected(self):
        p=self.root/'SOURCE_BOUNDARIES.json';x=json.loads(p.read_text());x['official_GRP']='scoring';p.write_text(json.dumps(x));self.reseal('SOURCE_BOUNDARIES.json')
        with self.assertRaises(ValueError):validate(self.root)
    def test_example_missing_synthetic_label_rejected(self):
        rel='examples/synthetic/synthetic_inputs.csv';p=self.root/rel;p.write_text(p.read_text().replace('synthetic_only','observed'));self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)

if __name__=='__main__':unittest.main()
