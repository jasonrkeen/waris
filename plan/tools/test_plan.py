from pathlib import Path
import hashlib,json,shutil,tempfile,unittest
from validate_plan import validate

ROOT=Path(__file__).resolve().parents[1]

class PlanChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'plan';shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__'))
    def update(self,rel,obj):
        p=self.root/rel;p.write_text(json.dumps(obj),encoding='utf8')
        m=json.loads((self.root/'FILE_MANIFEST.json').read_text())
        m['files'][rel]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
        (self.root/'FILE_MANIFEST.json').write_text(json.dumps(m))
    def plan(self):return json.loads((self.root/'FULL_RELEASE_PLAN.json').read_text())
    def test_exact_plan(self):self.assertEqual(validate(self.root)['components'],11)
    def test_missing_companion(self):
        (self.root/'companions/C03.md').unlink()
        with self.assertRaises(ValueError):validate(self.root)
    def test_extra_input(self):
        (self.root/'unreviewed.csv').write_text('x\n1\n')
        with self.assertRaises(ValueError):validate(self.root)
    def test_dependency_cycle(self):
        p=self.plan();p['components'][0]['dependencies']=['C05'];self.update('FULL_RELEASE_PLAN.json',p)
        with self.assertRaises(ValueError):validate(self.root)
    def test_missing_dependency(self):
        p=self.plan();p['components'][0]['dependencies']=['UNKNOWN'];self.update('FULL_RELEASE_PLAN.json',p)
        with self.assertRaises(ValueError):validate(self.root)
    def test_required_archival_edge_not_omitted(self):
        p=self.plan();next(c for c in p['components'] if c['id']=='C06')['dependencies']=['C04'];self.update('FULL_RELEASE_PLAN.json',p)
        with self.assertRaises(ValueError):validate(self.root)
    def test_archival_runtime_promotion(self):
        p=self.plan();p['components'][-1]['runtime_status']='active';self.update('FULL_RELEASE_PLAN.json',p)
        with self.assertRaises(ValueError):validate(self.root)
    def test_benchmark_scoring_promotion(self):
        b=json.loads((self.root/'SOURCE_BOUNDARIES.json').read_text());b['official_GRP']='scoring';self.update('SOURCE_BOUNDARIES.json',b)
        p=self.plan();p['boundaries']=b;self.update('FULL_RELEASE_PLAN.json',p)
        with self.assertRaises(ValueError):validate(self.root)
    def test_withheld_theme_even_if_hashes_updated(self):
        t=json.loads((self.root/'TRANSFORMATIONS.json').read_text());p=self.root/t[0]['path'];p.write_text(p.read_text().replace('WAML-010','WAML-006'))
        m=json.loads((self.root/'FILE_MANIFEST.json').read_text());m['files'][t[0]['path']]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size};(self.root/'FILE_MANIFEST.json').write_text(json.dumps(m))
        t[0]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();t[0]['bytes']=p.stat().st_size;self.update('TRANSFORMATIONS.json',t)
        with self.assertRaises(ValueError):validate(self.root)
    def test_missing_external_components_not_passed_as_verified(self):
        with self.assertRaises(ValueError):validate(self.root,Path(self.tmp.name)/'missing')

if __name__=='__main__':unittest.main()
